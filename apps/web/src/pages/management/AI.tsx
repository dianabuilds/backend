import React from 'react';
import { ApexChart, Button, Card, Drawer, Input, Select, Spinner, Switch, Table, Textarea } from '@ui';
import { apiDelete, apiGet, apiPost } from '../../shared/api/client';

type Model = {
  id: string;
  name: string;
  provider_slug: string;
  version?: string | null;
  status?: string;
  is_default?: boolean;
  params?: any | null;
};

type Provider = {
  slug: string;
  title?: string | null;
  enabled?: boolean;
  base_url?: string | null;
  timeout_sec?: number | null;
};

export default function ManagementAI() {
  // Datasets
  const [models, setModels] = React.useState<Model[]>([]);
  const [providers, setProviders] = React.useState<Provider[]>([]);
  const [metrics, setMetrics] = React.useState<any | null>(null);

  // UI state
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [editing, setEditing] = React.useState<Model | null>(null);
  const [editingProvider, setEditingProvider] = React.useState<Provider | null>(null);
  const [provApiKey, setProvApiKey] = React.useState<string>('');
  const [provRetries, setProvRetries] = React.useState<number | ''>('');

  // Playground
  const [pgPrompt, setPgPrompt] = React.useState('');
  const [pgModel, setPgModel] = React.useState('');
  const [pgResult, setPgResult] = React.useState<string>('');
  const [pgBusy, setPgBusy] = React.useState(false);
  const [pgLatency, setPgLatency] = React.useState<number | null>(null);

  const load = React.useCallback(async () => {
    try {
      const m = await apiGet<{ items: Model[] }>('/v1/ai/admin/models');
      setModels(m?.items || []);
    } catch {}
    try {
      const p = await apiGet<{ items: Provider[] }>('/v1/ai/admin/providers');
      setProviders(p?.items || []);
    } catch {}
    try {
      const s = await apiGet<any>('/v1/admin/telemetry/llm/summary');
      setMetrics(s || {});
    } catch {}
  }, []);
  React.useEffect(() => { void load(); }, [load]);

  // Helpers
  const usageByKey = React.useMemo(() => {
    const calls = (metrics?.calls || []) as Array<any>;
    const tokens = (metrics?.tokens_total || []) as Array<any>;
    const errors = calls.filter((r) => r.type === 'errors');
    const ok = calls.filter((r) => r.type === 'calls');
    const by: Record<string, { calls: number; errors: number; prompt: number; completion: number }> = {};
    for (const r of ok) {
      const k = `${r.provider}:${r.model}`;
      by[k] = by[k] || { calls: 0, errors: 0, prompt: 0, completion: 0 };
      by[k].calls += r.count || 0;
    }
    for (const r of errors) {
      const k = `${r.provider}:${r.model}`;
      by[k] = by[k] || { calls: 0, errors: 0, prompt: 0, completion: 0 };
      by[k].errors += r.count || 0;
    }
    for (const r of tokens) {
      const k = `${r.provider}:${r.model}`;
      by[k] = by[k] || { calls: 0, errors: 0, prompt: 0, completion: 0 };
      if (r.type === 'prompt') by[k].prompt += r.total || 0;
      if (r.type === 'completion') by[k].completion += r.total || 0;
    }
    return by;
  }, [metrics]);

  const openAddModel = () => {
    setEditing({ id: '', name: '', provider_slug: '', version: '', status: 'active', params: { limits: {}, usage: {}, fallback_priority: 100 } });
    setEditingProvider(null);
    setProvApiKey('');
    setProvRetries('');
    setDrawerOpen(true);
  };
  const openEditModel = (m: Model) => {
    setEditing({ ...m });
    setEditingProvider(providers.find((p) => p.slug === m.provider_slug) || null);
    setProvApiKey('');
    setProvRetries('');
    setDrawerOpen(true);
  };

  const saveModel = async () => {
    if (!editing) return;
    const payload: any = {
      id: editing.id || undefined,
      name: editing.name,
      provider_slug: editing.provider_slug,
      version: (editing.version || '').trim() || undefined,
      status: editing.status || 'active',
      is_default: !!editing.is_default,
      params: editing.params || {},
    };
    await apiPost('/v1/ai/admin/models', payload);
    if (editingProvider && editingProvider.slug) {
      await apiPost('/v1/ai/admin/providers', {
        slug: editingProvider.slug,
        title: editingProvider.title,
        enabled: editingProvider.enabled,
        base_url: editingProvider.base_url,
        timeout_sec: editingProvider.timeout_sec,
        api_key: provApiKey || undefined,
        extras: typeof provRetries === 'number' ? { retries: provRetries } : undefined,
      });
    }
    setDrawerOpen(false);
    await load();
  };

  const toggleEnabled = async (m: Model) => {
    const status = (m.status || 'active') === 'disabled' ? 'active' : 'disabled';
    await apiPost('/v1/ai/admin/models', { id: m.id, name: m.name, provider_slug: m.provider_slug, version: m.version, status, params: m.params || {} });
    await load();
  };

  const deleteModel = async (m: Model) => {
    if (!m?.id) return;
    await apiDelete(`/v1/ai/admin/models/${encodeURIComponent(m.id)}`);
    await load();
  };

  const onPlay = async () => {
    if (!pgPrompt) return;
    setPgBusy(true);
    setPgResult('');
    const t0 = performance.now();
    try {
      const chosen = models.find((x) => x.id === pgModel);
      const r = await apiPost<{ result: string }>('/v1/ai/admin/playground', {
        prompt: pgPrompt,
        model: chosen?.name || undefined,
        provider: chosen?.provider_slug || undefined,
      });
      setPgResult(String((r as any)?.result || ''));
    } catch (e: any) {
      setPgResult(String(e?.message || e || 'error'));
    } finally {
      setPgLatency(Math.round(performance.now() - t0));
      setPgBusy(false);
    }
  };

  // Derived lists for charts
  const providersList = React.useMemo(() => Array.from(new Set(models.map((m) => `${m.provider_slug}:${m.name}`))), [models]);
  const okSeries = providersList.map((k) => usageByKey[k]?.calls || 0);
  const errSeries = providersList.map((k) => usageByKey[k]?.errors || 0);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xl font-semibold">AI & LLM — Управление моделями</div>
          <div className="text-sm text-gray-500">Здесь вы управляете списком моделей, лимитами и fallback-политиками. Все изменения влияют на работу платформы в реальном времени.</div>
        </div>
        <Button onClick={openAddModel}>Добавить модель</Button>
      </div>

      {/* Models table */}
      <Card>
        <div className="p-4">
          <Table.Table>
            <Table.THead>
              <Table.TR>
                <Table.TH>Вкл</Table.TH>
                <Table.TH>Модель</Table.TH>
                <Table.TH>Провайдер</Table.TH>
                <Table.TH>Версия</Table.TH>
                <Table.TH>Статус</Table.TH>
                <Table.TH>Лимиты</Table.TH>
                <Table.TH>Использование</Table.TH>
                <Table.TH>Fallback</Table.TH>
                <Table.TH>Действия</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {models.map((m) => {
                const key = `${m.provider_slug}:${m.name}`;
                const u = usageByKey[key] || { calls: 0, errors: 0, prompt: 0, completion: 0 };
                const limits = m?.params?.limits || {};
                const priority = m?.params?.fallback_priority ?? '-';
                const enabled = (m.status || 'active') !== 'disabled';
                const statusColor = u.errors > 0 ? 'text-red-600' : 'text-green-600';
                return (
                  <Table.TR key={m.id}>
                    <Table.TD>
                      <Switch checked={enabled} onChange={() => void toggleEnabled(m)} />
                    </Table.TD>
                    <Table.TD>{m.name}</Table.TD>
                    <Table.TD>{m.provider_slug}</Table.TD>
                    <Table.TD>{m.version || '-'}</Table.TD>
                    <Table.TD><span className={`text-xs ${statusColor}`}>{enabled ? (u.errors ? 'ошибки' : 'работает') : 'выкл'}</span></Table.TD>
                    <Table.TD>
                      <div className="text-xs text-gray-600">
                        {limits.daily_tokens ? `день: ${limits.daily_tokens}` : ''}{limits.daily_tokens && limits.monthly_tokens ? ', ' : ''}{limits.monthly_tokens ? `мес: ${limits.monthly_tokens}` : ''}
                      </div>
                    </Table.TD>
                    <Table.TD>
                      <div className="text-xs">calls: {u.calls} / err: {u.errors}</div>
                      <div className="text-xs">tok: {u.prompt + u.completion}</div>
                    </Table.TD>
                    <Table.TD>{priority}</Table.TD>
                    <Table.TD>
                      <div className="flex gap-2">
                        <Button onClick={() => openEditModel(m)}>✏️ Редактировать</Button>
                        <Button onClick={() => deleteModel(m)}>🗑️ Удалить</Button>
                        <Button onClick={() => window.open('/observability/llm', '_blank')}>🔍 Логи</Button>
                      </div>
                    </Table.TD>
                  </Table.TR>
                );
              })}
            </Table.TBody>
          </Table.Table>
        </div>
      </Card>

      {/* Global settings & stats */}
      <div className="grid grid-cols-2 gap-6">
        {/* Global */}
        <Card>
          <div className="p-4 space-y-3">
            <div className="text-sm font-semibold">Глобальные настройки</div>
            <div className="text-xs text-gray-500">Fallback-политика настраивается правилами ниже. Таймаут/ретраи — через провайдер.</div>
            {/* Fallback rules editor (simple) */}
            <FallbackRules models={models} onChange={load} />
          </div>
        </Card>
        {/* Stats */}
        <Card>
          <div className="p-4">
            <div className="mb-2 text-sm text-gray-500">LLM calls/errors by provider:model</div>
            <ApexChart
              type="bar"
              series={[
                { name: 'calls', data: providersList.map((_, i) => okSeries[i]) },
                { name: 'errors', data: providersList.map((_, i) => errSeries[i]) },
              ]}
              options={{ xaxis: { categories: providersList, labels: { rotate: -45 } }, legend: { show: true } }}
              height={300}
            />
          </div>
        </Card>
      </div>

      {/* Playground */}
      <Card>
        <div className="p-4 space-y-2">
          <div className="text-sm font-semibold">Playground</div>
          <div className="grid grid-cols-3 gap-2">
            <Select value={pgModel} onChange={(e: any) => setPgModel(e.target.value)}>
              <option value="">Выберите модель</option>
              {models.map((m) => (
                <option value={m.id} key={m.id}>{m.provider_slug}:{m.name}</option>
              ))}
            </Select>
            <div className="col-span-2" />
          </div>
          <Textarea placeholder="Prompt" value={pgPrompt} onChange={(e) => setPgPrompt(e.target.value)} />
          <div className="flex items-center gap-2">
            <Button onClick={onPlay} disabled={!pgPrompt || pgBusy}>Отправить</Button>
            {pgBusy && <Spinner />}
            {pgLatency != null && <span className="text-xs text-gray-500">{pgLatency} ms</span>}
          </div>
          {pgResult && <pre className="mt-2 rounded bg-gray-50 p-3 text-sm whitespace-pre-wrap">{pgResult}</pre>}
        </div>
      </Card>

      {/* Drawer for model/provider editing */}
      <Drawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title="Редактирование модели"
        footer={<Button onClick={saveModel} disabled={!editing?.name || !editing?.provider_slug}>Сохранить изменения</Button>}
        widthClass="w-[640px]"
      >
        <div className="p-4 space-y-3">
          {/* Model */}
          <div className="text-sm font-semibold">Модель</div>
          <div className="grid grid-cols-2 gap-2">
            <Input placeholder="Название (системное)" value={editing?.name || ''} onChange={(e) => setEditing((s) => ({ ...(s as any), name: e.target.value }))} />
            <Input placeholder="Провайдер (slug)" value={editing?.provider_slug || ''} onChange={(e) => { const v = e.target.value; setEditing((s) => ({ ...(s as any), provider_slug: v })); setEditingProvider((p) => p && p.slug === v ? p : { slug: v }); }} />
            <Input placeholder="Версия" value={editing?.version || ''} onChange={(e) => setEditing((s) => ({ ...(s as any), version: e.target.value }))} />
            <div className="flex items-center gap-2 text-sm"><span>Включено</span><Switch checked={(editing?.status || 'active') !== 'disabled'} onChange={() => setEditing((s) => ({ ...(s as any), status: ((s?.status || 'active') === 'disabled') ? 'active' : 'disabled' }))} /></div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Input placeholder="Лимит токенов (день)" value={editing?.params?.limits?.daily_tokens || ''} onChange={(e) => setEditing((s) => ({ ...(s as any), params: { ...(s?.params||{}), limits: { ...((s?.params||{}).limits||{}), daily_tokens: Number(e.target.value||0) } } }))} />
            <Input placeholder="Лимит токенов (мес)" value={editing?.params?.limits?.monthly_tokens || ''} onChange={(e) => setEditing((s) => ({ ...(s as any), params: { ...(s?.params||{}), limits: { ...((s?.params||{}).limits||{}), monthly_tokens: Number(e.target.value||0) } } }))} />
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div className="flex items-center gap-2 text-sm"><Switch checked={!!editing?.params?.usage?.content} onChange={() => setEditing((s) => ({ ...(s as any), params: { ...(s?.params||{}), usage: { ...((s?.params||{}).usage||{}), content: !s?.params?.usage?.content } } }))} /><span>генерация контента</span></div>
            <div className="flex items-center gap-2 text-sm"><Switch checked={!!editing?.params?.usage?.quests} onChange={() => setEditing((s) => ({ ...(s as any), params: { ...(s?.params||{}), usage: { ...((s?.params||{}).usage||{}), quests: !s?.params?.usage?.quests } } }))} /><span>AI-квесты</span></div>
            <div className="flex items-center gap-2 text-sm"><Switch checked={!!editing?.params?.usage?.moderation} onChange={() => setEditing((s) => ({ ...(s as any), params: { ...(s?.params||{}), usage: { ...((s?.params||{}).usage||{}), moderation: !s?.params?.usage?.moderation } } }))} /><span>модерация</span></div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Input placeholder="Fallback-приоритет (число)" value={editing?.params?.fallback_priority ?? ''} onChange={(e) => setEditing((s) => ({ ...(s as any), params: { ...(s?.params||{}), fallback_priority: Number(e.target.value||0) } }))} />
          </div>

          {/* Provider config */}
          <div className="mt-2 text-sm font-semibold">Провайдер</div>
          <div className="grid grid-cols-2 gap-2">
            <Input placeholder="Название (опц.)" value={editingProvider?.title || ''} onChange={(e) => setEditingProvider((p: any) => ({ ...(p||{ slug: editing?.provider_slug||'' }), title: e.target.value }))} />
            <Input placeholder="Endpoint URL (опц.)" value={editingProvider?.base_url || ''} onChange={(e) => setEditingProvider((p: any) => ({ ...(p||{ slug: editing?.provider_slug||'' }), base_url: e.target.value }))} />
            <Input placeholder="Timeout, сек (опц.)" value={editingProvider?.timeout_sec ?? ''} onChange={(e) => setEditingProvider((p: any) => ({ ...(p||{ slug: editing?.provider_slug||'' }), timeout_sec: Number(e.target.value||0) }))} />
            <Input placeholder="Ретраи (опц.)" value={provRetries} onChange={(e) => { const v = e.target.value; setProvRetries(v === '' ? '' : Number(v)); }} />
            <Input placeholder="API ключ (не отображается)" value={provApiKey} onChange={(e) => setProvApiKey(e.target.value)} />
          </div>
        </div>
      </Drawer>
    </div>
  );
}

function FallbackRules({ models, onChange }: { models: Model[]; onChange: () => void }) {
  const [rules, setRules] = React.useState<any[]>([]);
  const [primary, setPrimary] = React.useState('');
  const [secondary, setSecondary] = React.useState('');
  const load = React.useCallback(async () => {
    try { const r = await apiGet<{ items: any[] }>('/v1/ai/admin/fallbacks'); setRules(r?.items || []); } catch {}
  }, []);
  React.useEffect(() => { void load(); }, [load]);
  const add = async () => {
    if (!primary || !secondary) return;
    await apiPost('/v1/ai/admin/fallbacks', { primary_model: primary, fallback_model: secondary, mode: 'on_error' });
    setPrimary(''); setSecondary('');
    await load();
    onChange();
  };
  const del = async (id: string) => {
    await apiDelete(`/v1/ai/admin/fallbacks/${encodeURIComponent(id)}`);
    await load();
    onChange();
  };
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-3 gap-2">
        <Select value={primary} onChange={(e: any) => setPrimary(e.target.value)}>
          <option value="">primary model</option>
          {models.map((m) => <option key={m.id} value={m.name}>{m.name}</option>)}
        </Select>
        <Select value={secondary} onChange={(e: any) => setSecondary(e.target.value)}>
          <option value="">fallback model</option>
          {models.map((m) => <option key={m.id} value={m.name}>{m.name}</option>)}
        </Select>
        <Button onClick={add} disabled={!primary || !secondary}>Добавить правило</Button>
      </div>
      <Table.Table>
        <Table.THead>
          <Table.TR>
            <Table.TH>primary</Table.TH>
            <Table.TH>fallback</Table.TH>
            <Table.TH>mode</Table.TH>
            <Table.TH></Table.TH>
          </Table.TR>
        </Table.THead>
        <Table.TBody>
          {rules.map((r) => (
            <Table.TR key={r.id}>
              <Table.TD>{r.primary_model}</Table.TD>
              <Table.TD>{r.fallback_model}</Table.TD>
              <Table.TD>{r.mode}</Table.TD>
              <Table.TD><Button onClick={() => del(r.id)}>Удалить</Button></Table.TD>
            </Table.TR>
          ))}
        </Table.TBody>
      </Table.Table>
    </div>
  );
}

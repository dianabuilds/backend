import React from 'react';
import { Badge, Button, Card, Drawer, Input, Pagination, Select, Table, Tabs, Textarea } from '@ui';
import { apiDelete, apiGet, apiPost } from '../../shared/api/client';
import { Users, Coins, Gauge, TrendingDown } from '@icons';

type Plan = {
  id: string; slug: string; title: string; description?: string | null;
  price_cents?: number | null; currency?: string | null; is_active: boolean; order?: number;
  monthly_limits?: any; features?: any; updated_at?: string;
};

export default function TariffsPage() {
  const [kpi, setKpi] = React.useState<any>({ active_subs: 0, mrr: 0, arpu: 0, churn_30d: 0 });
  const [tab, setTab] = React.useState<'plans' | 'matrix' | 'history'>('plans');
  const [plans, setPlans] = React.useState<Plan[]>([]);
  const [page, setPage] = React.useState(1);
  const pageSize = 10;
  const [busy, setBusy] = React.useState(false);
  const [drawer, setDrawer] = React.useState(false);
  const [editing, setEditing] = React.useState<Plan | null>(null);
  const [history, setHistory] = React.useState<any[]>([]);

  const load = React.useCallback(async () => {
    try { setKpi(await apiGet('/v1/billing/admin/metrics')); } catch {}
    try { const r = await apiGet<{ items: Plan[] }>('/v1/billing/admin/plans/all'); setPlans(r?.items || []); } catch {}
  }, []);
  React.useEffect(() => { void load(); }, [load]);

  const paginate = <T,>(arr: T[], page: number, size: number) => {
    const total = Math.max(1, Math.ceil(arr.length / size));
    const p = Math.min(Math.max(1, page), total);
    const start = (p - 1) * size; return { total, page: p, items: arr.slice(start, start + size) };
  };
  const pageData = paginate(plans, page, pageSize);

  const openNew = () => { setEditing({ id: '', slug: '', title: '', price_cents: 0, currency: 'USD', is_active: false, monthly_limits: {}, features: { status: 'draft', audience: 'off' } } as any); setDrawer(true); };
  const openEdit = (p: Plan) => { setEditing({ ...p }); setDrawer(true); };
  const save = async () => {
    if (!editing) return;
    setBusy(true);
    try {
      const payload: any = {
        id: editing.id || undefined,
        slug: editing.slug,
        title: editing.title,
        description: editing.description,
        price_cents: editing.price_cents,
        currency: editing.currency,
        is_active: !!editing.is_active,
        order: editing.order ?? 100,
        monthly_limits: editing.monthly_limits || {},
        features: editing.features || {},
      };
      await apiPost('/v1/billing/admin/plans', payload);
      setDrawer(false);
      await load();
    } finally { setBusy(false); }
  };
  const removePlan = async (id: string) => { await apiDelete(`/v1/billing/admin/plans/${encodeURIComponent(id)}`); await load(); };

  const planStatusColor = (p: Plan) => {
    const s = String(p?.features?.status || (p.is_active ? 'active' : 'hidden')).toLowerCase();
    if (s === 'active') return 'success';
    if (s === 'draft') return 'warning';
    if (s === 'hidden' || s === 'archived') return 'neutral';
    return 'neutral';
  };

  // Matrix editing state derived from plans
  const [matrix, setMatrix] = React.useState<Record<string, any>>({});
  React.useEffect(() => {
    const m: Record<string, any> = {};
    for (const p of plans) m[p.slug] = { ...(p.monthly_limits || {}) };
    setMatrix(m);
  }, [plans]);
  const saveMatrix = async () => {
    const items = Object.keys(matrix).map((slug) => ({ slug, monthly_limits: matrix[slug] }));
    await apiPost('/v1/billing/admin/plans/bulk_limits', { items });
    await load();
  };

  const loadHistory = async (slug: string) => {
    const r = await apiGet<{ items: any[] }>(`/v1/billing/admin/plans/${encodeURIComponent(slug)}/audit?limit=100`);
    setHistory(r?.items || []);
    setTab('history');
  };

  return (
    <div className="p-6 space-y-6 xl:space-y-8">
      {/* KPI row */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <Card>
          <div className="p-6 lg:p-8 bg-emerald-50 rounded-md flex items-center gap-4">
            <div className="rounded-full bg-emerald-100 text-emerald-700 p-2"><Users className="h-5 w-5" /></div>
            <div>
              <div className="text-xs text-gray-600">Активные подписчики</div>
              <div className="text-2xl font-semibold tracking-tight">{kpi.active_subs || 0}</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6 lg:p-8 bg-sky-50 rounded-md flex items-center gap-4">
            <div className="rounded-full bg-sky-100 text-sky-700 p-2"><Coins className="h-5 w-5" /></div>
            <div>
              <div className="text-xs text-gray-600">MRR</div>
              <div className="text-2xl font-semibold tracking-tight">${Number(kpi.mrr || 0).toFixed(2)}</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6 lg:p-8 bg-indigo-50 rounded-md flex items-center gap-4">
            <div className="rounded-full bg-indigo-100 text-indigo-700 p-2"><Gauge className="h-5 w-5" /></div>
            <div>
              <div className="text-xs text-gray-600">ARPU</div>
              <div className="text-2xl font-semibold tracking-tight">${Number(kpi.arpu || 0).toFixed(2)}</div>
            </div>
          </div>
        </Card>
        <Card>
          <div className="p-6 lg:p-8 bg-rose-50 rounded-md flex items-center gap-4">
            <div className="rounded-full bg-rose-100 text-rose-700 p-2"><TrendingDown className="h-5 w-5" /></div>
            <div>
              <div className="text-xs text-gray-600">Отток (30д)</div>
              <div className="text-2xl font-semibold tracking-tight">{Math.round((kpi.churn_30d || 0) * 100)}%</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs items={[{ key: 'plans', label: 'Планы' }, { key: 'matrix', label: 'Матрица лимитов' }, { key: 'history', label: 'История изменений' }]} value={tab} onChange={setTab} />

      {tab === 'plans' && (
        <Card>
          <div className="p-6 lg:p-8">
            <div className="mb-3 flex items-center justify-between">
              <div className="text-sm text-gray-500">Тарифные планы</div>
              <Button onClick={openNew}>Добавить план</Button>
            </div>
            <Table.Table zebra>
              <Table.THead>
                <Table.TR>
                  <Table.TH>Название</Table.TH>
                  <Table.TH>Цена</Table.TH>
                  <Table.TH>Валюта</Table.TH>
                  <Table.TH>Лимиты</Table.TH>
                  <Table.TH>Аудитория</Table.TH>
                  <Table.TH>Статус</Table.TH>
                  <Table.TH>Действия</Table.TH>
                </Table.TR>
              </Table.THead>
              <Table.TBody>
                {pageData.items.map((p) => (
                  <React.Fragment key={p.id}>
                    <Table.TR>
                      <Table.TD>
                        <div className="flex flex-col">
                          <span className="font-medium">{p.title}</span>
                          <span className="font-mono text-xs text-gray-500">{p.slug}</span>
                        </div>
                      </Table.TD>
                      <Table.TD className="text-right">{p.price_cents != null ? `$${(p.price_cents/100).toFixed(2)}` : '-'}</Table.TD>
                      <Table.TD><Badge variant="outline">{p.currency || 'USD'}</Badge></Table.TD>
                      <Table.TD className="text-xs text-gray-600">{shortLimits(p.monthly_limits)}</Table.TD>
                      <Table.TD>{audBadge(p)}</Table.TD>
                      <Table.TD><Badge color={planStatusColor(p)}>{String(p?.features?.status || (p.is_active ? 'active' : 'hidden'))}</Badge></Table.TD>
                      <Table.TD>
                        <div className="flex items-center gap-2">
                          <Button onClick={() => openEdit(p)}>Edit</Button>
                          <Button onClick={() => loadHistory(p.slug)}>History</Button>
                          <Button onClick={() => removePlan(p.id)}>Archive</Button>
                        </div>
                      </Table.TD>
                    </Table.TR>
                  </React.Fragment>
                ))}
              </Table.TBody>
            </Table.Table>
            <div className="mt-3 flex justify-end">
              <Pagination page={pageData.page} total={pageData.total} onChange={setPage} />
            </div>
          </div>
        </Card>
      )}

      {tab === 'matrix' && (
        <Card>
          <div className="p-6 lg:p-8 space-y-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">Матрица лимитов</div>
              <div className="flex gap-2">
                <Button onClick={saveMatrix}>Сохранить матрицу</Button>
              </div>
            </div>
            <div className="overflow-auto">
              <table className="table w-full">
                <thead className="table-thead">
                  <tr className="table-tr">
                    <th className="table-th">Лимит</th>
                    {plans.map((p) => (<th key={p.slug} className="table-th">{p.title}</th>))}
                  </tr>
                </thead>
                <tbody className="table-tbody">
                  {['llm_tokens_month','quest_generations','echo_traces','tag_notifications','worlds_max','nodes_max','transitions_max','api_quota'].map((key) => (
                    <tr key={key} className="table-tr odd:bg-gray-50">
                      <td className="table-td font-medium">{limitLabel(key)}</td>
                      {plans.map((p) => (
                        <td key={p.slug} className="table-td">
                          <Input
                            value={String((matrix[p.slug]||{})[key] ?? '')}
                            onChange={(e) => setMatrix((m) => ({ ...m, [p.slug]: { ...(m[p.slug]||{}), [key]: parseInt(e.target.value || '0', 10) } }))}
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Card>
      )}

      {tab === 'history' && (
        <Card>
          <div className="p-6 lg:p-8">
            <div className="mb-2 text-sm text-gray-500">История изменений</div>
            <Table.Table zebra>
              <Table.THead>
                <Table.TR>
                  <Table.TH>Время</Table.TH>
                  <Table.TH>Действие</Table.TH>
                  <Table.TH>Ресурс</Table.TH>
                </Table.TR>
              </Table.THead>
              <Table.TBody>
                {(history || []).map((e, i) => (
                  <Table.TR key={i}>
                    <Table.TD>{e.created_at || ''}</Table.TD>
                    <Table.TD>{e.action || ''}</Table.TD>
                    <Table.TD className="font-mono text-xs">{e.resource_id || ''}</Table.TD>
                  </Table.TR>
                ))}
              </Table.TBody>
            </Table.Table>
          </div>
        </Card>
      )}

      {/* Side widgets could be added similarly (revenue chart, warnings) */}

      <Drawer
        open={drawer}
        onClose={() => setDrawer(false)}
        title="Тарифный план"
        footer={<Button onClick={save} disabled={!editing?.slug || !editing?.title || busy}>{busy ? 'Сохранение…' : 'Сохранить'}</Button>}
        widthClass="w-[900px]"
      >
        <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Основное */}
          <div className="space-y-3">
            <div className="text-sm font-semibold">Основное</div>
            <Input placeholder="Title" value={editing?.title || ''} onChange={(e) => setEditing((s: any) => ({ ...(s||{}), title: e.target.value }))} />
            <Input placeholder="Slug" value={editing?.slug || ''} onChange={(e) => setEditing((s: any) => ({ ...(s||{}), slug: e.target.value }))} />
            <Textarea placeholder="Описание" value={editing?.description || ''} onChange={(e) => setEditing((s: any) => ({ ...(s||{}), description: e.target.value }))} />
            <div className="grid grid-cols-3 gap-2">
              <Input placeholder="Цена (USD)" value={String((editing?.price_cents ?? 0)/100)} onChange={(e) => setEditing((s: any) => ({ ...(s||{}), price_cents: Math.round(parseFloat(e.target.value || '0')*100) }))} />
              <Select value={editing?.features?.interval || 'month'} onChange={(e: any) => setEditing((s: any) => ({ ...(s||{}), features: { ...(s?.features||{}), interval: e.target.value } }))}>
                <option value="month">месяц</option>
                <option value="year">год</option>
              </Select>
              <Select value={editing?.currency || 'USD'} onChange={(e: any) => setEditing((s: any) => ({ ...(s||{}), currency: e.target.value }))}>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="USDT">USDT</option>
              </Select>
            </div>
            <Select value={editing?.features?.audience || 'off'} onChange={(e: any) => setEditing((s: any) => ({ ...(s||{}), features: { ...(s?.features||{}), audience: e.target.value } }))}>
              <option value="off">Off</option>
              <option value="all">All</option>
              <option value="premium">Premium</option>
            </Select>
            <Select value={editing?.features?.status || (editing?.is_active ? 'active' : 'hidden')} onChange={(e: any) => setEditing((s: any) => ({ ...(s||{}), features: { ...(s?.features||{}), status: e.target.value }, is_active: e.target.value==='active' }))}>
              <option value="active">active</option>
              <option value="hidden">hidden</option>
              <option value="draft">draft</option>
              <option value="archived">archived</option>
            </Select>
          </div>

          {/* Лимиты */}
          <div className="space-y-3">
            <div className="text-sm font-semibold">Лимиты</div>
            {['llm_tokens_month','quest_generations','echo_traces','tag_notifications','worlds_max','nodes_max','transitions_max','api_quota'].map((key) => (
              <Input key={key} placeholder={limitLabel(key)} value={String((editing?.monthly_limits||{})[key] ?? '')} onChange={(e) => setEditing((s: any) => ({ ...(s||{}), monthly_limits: { ...((s?.monthly_limits)||{}), [key]: parseInt(e.target.value||'0',10) } }))} />
            ))}
          </div>

          {/* Фичи */}
          <div className="space-y-2">
            <div className="text-sm font-semibold">Фичи</div>
            {['ai_quest_generator','compass_enhanced','progress_map','history_advanced','exclusive_caves','achievements'].map((key) => (
              <label key={key} className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={!!(editing?.features||{})[key]} onChange={(e) => setEditing((s: any) => ({ ...(s||{}), features: { ...((s?.features)||{}), [key]: e.target.checked } }))} />
                <span>{featureLabel(key)}</span>
              </label>
            ))}
          </div>

          {/* Модели */}
          <div className="space-y-2">
            <div className="text-sm font-semibold">Доступ к моделям</div>
            <Textarea placeholder="модели через запятую (slug)" value={(editing?.features?.models_allowed||[]).join(', ')} onChange={(e) => setEditing((s: any) => ({ ...(s||{}), features: { ...((s?.features)||{}), models_allowed: e.target.value.split(',').map((x)=>x.trim()).filter(Boolean) } }))} />
          </div>

          {/* Промо */}
          <div className="space-y-2">
            <div className="text-sm font-semibold">Промо/эксперименты</div>
            <Input placeholder="Trial (days)" value={String(editing?.features?.trial_days||'')} onChange={(e)=> setEditing((s:any)=> ({...(s||{}), features:{...((s?.features)||{}), trial_days: parseInt(e.target.value||'0',10)}}))} />
            <Select value={editing?.features?.ab_variant || 'control'} onChange={(e:any)=> setEditing((s:any)=> ({...(s||{}), features:{...((s?.features)||{}), ab_variant: e.target.value}}))}>
              <option value="control">control</option>
              <option value="variant-A">variant-A</option>
              <option value="variant-B">variant-B</option>
            </Select>
            <Textarea placeholder="feature flags через запятую" value={(editing?.features?.flags||[]).join(', ')} onChange={(e)=> setEditing((s:any)=> ({...(s||{}), features:{...((s?.features)||{}), flags: e.target.value.split(',').map((x)=>x.trim()).filter(Boolean)}}))} />
          </div>
        </div>
      </Drawer>
    </div>
  );
}

function shortLimits(l: any): string {
  if (!l) return '-';
  const parts: string[] = [];
  if (l.llm_tokens_month) parts.push(`${l.llm_tokens_month} токенов`);
  if (l.quest_generations) parts.push(`${l.quest_generations} генераций`);
  return parts.join(', ');
}
function audBadge(p: Plan) {
  const v = String(p?.features?.audience || 'off');
  if (v === 'all') return <Badge>All</Badge>;
  if (v === 'premium') return <Badge color="primary">Premium</Badge>;
  return <Badge variant="outline">Off</Badge>;
}
function limitLabel(k: string): string {
  const map: Record<string, string> = {
    llm_tokens_month: 'Токены (мес)',
    quest_generations: 'Генерации',
    echo_traces: 'Эхо/следы',
    tag_notifications: 'Уведомления',
    worlds_max: 'Миры',
    nodes_max: 'Ноды',
    transitions_max: 'Переходы',
    api_quota: 'API квота',
  };
  return map[k] || k;
}
function featureLabel(k: string): string {
  const map: Record<string, string> = {
    ai_quest_generator: 'AI-генератор квестов',
    compass_enhanced: 'Расширенный компас',
    progress_map: 'Карта прогресса',
    history_advanced: 'Улучшенная история',
    exclusive_caves: 'Эксклюзивные пещеры',
    achievements: 'Достижения/награды',
  };
  return map[k] || k;
}


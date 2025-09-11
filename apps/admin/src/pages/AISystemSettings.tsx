import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  CheckCircle2,
  Circle,
  Cloud,
  Eye,
  EyeOff,
  Import,
  KeyRound,
  Pencil,
  Plus,
  RefreshCcw,
  Search,
  Trash2,
} from 'lucide-react';
import { useMemo, useState } from 'react';

import { api } from '../api/client';
import DataTable from '../components/DataTable';
import type { Column } from '../components/DataTable.helpers';
import Slideover from '../components/Slideover';
import TabRouter from '../components/TabRouter';
import { confirmDialog } from '../shared/ui';

// Friendly capability labels for UI
const CAPABILITIES: { key: string; label: string; help?: string }[] = [
  { key: 'chat', label: 'Chat', help: 'Conversational text generation' },
  { key: 'tools', label: 'Tools', help: 'Function / tool calling support' },
  { key: 'json_mode', label: 'JSON Mode', help: 'Strict JSON responses' },
  { key: 'vision', label: 'Vision', help: 'Understands images in prompts' },
  { key: 'long_context', label: 'Long Context', help: 'Extended context window' },
  { key: 'stream', label: 'Streaming', help: 'Streams tokens as they are generated' },
  { key: 'embed', label: 'Embeddings', help: 'Vector embeddings generation' },
  { key: 'rerank', label: 'Reranking', help: 'Rerank documents by relevance' },
];

const capLabel = (k: string): string => {
  const m = CAPABILITIES.find((c) => c.key === k);
  if (m) return m.label;
  // Fallback: Title Case without underscores
  return k
    .split('_')
    .map((s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s))
    .join(' ');
};

const capHelp = (k: string): string | undefined => CAPABILITIES.find((c) => c.key === k)?.help;

// Используем any, так как точные структуры могут меняться
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Provider = any;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Model = any;

// type Price = any; // removed with Costs & Limits

interface Defaults {
  provider_id?: string | null;
  model_id?: string | null;
  bundle_id?: string | null;
}

export default function AISystemSettings() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">AI System Settings</h1>
      <SettingsTabs />
    </div>
  );
}

function StatusDot({ status }: { status?: string }) {
  const s = (status || '').toLowerCase();
  let color = 'text-gray-400';
  if (s.includes('ok') || s.includes('up') || s.includes('healthy')) {
    color = 'text-green-500';
  } else if (s.includes('warn') || s.includes('degraded')) {
    color = 'text-yellow-500';
  } else if (s.includes('down') || s.includes('error')) {
    color = 'text-red-500';
  }
  return <Circle className={`w-3 h-3 ${color}`} fill="currentColor" />;
}

function SettingsTabs() {
  const qc = useQueryClient();
  const providers = useQuery({
    queryKey: ['ai', 'providers'],
    queryFn: async () => (await api.get<Provider[]>('/admin/ai/system/providers')).data || [],
  });
  const models = useQuery({
    queryKey: ['ai', 'models'],
    queryFn: async () => (await api.get<Model[]>('/admin/ai/system/models')).data || [],
  });
  const defaults = useQuery({
    queryKey: ['ai', 'defaults'],
    queryFn: async () => (await api.get<Defaults>('/admin/ai/system/defaults')).data || {},
  });

  // Drafts for editor
  const [providerDraft, setProviderDraft] = useState<Partial<Provider> | null>(null);
  const [modelDraft, setModelDraft] = useState<Partial<Model> | null>(null);
  // const [priceDraft, setPriceDraft] = useState<Partial<Price> | null>(null);
  const [manifestDraft, setManifestDraft] = useState<string>('');
  const [secretsDraft, setSecretsDraft] = useState<Record<string, string>>({});
  const [secretsProviderId, setSecretsProviderId] = useState<string>('');
  const [revealProviderCode, setRevealProviderCode] = useState(false);
  const [modelTest, setModelTest] = useState<{
    loading: boolean;
    result?: { ok: boolean; status: number; latency_ms?: number; excerpt?: string } | null;
  }>({ loading: false, result: null });
  const [priceUnit, setPriceUnit] = useState<'per_1k' | 'per_1m'>('per_1k');
  const [, setModelErrors] = useState<{
    provider_id?: string;
    code?: string;
    input_price?: string;
    output_price?: string;
  }>({});
  const [importDraft, setImportDraft] = useState<{ provider_id?: string; items?: any[] } | null>(
    null,
  );
  // Last test status per model (for Active column)
  const [modelConn, setModelConn] = useState<Record<string, 'ok' | 'fail' | 'unknown'>>({});
  // Search / filters
  const [providerSearch, setProviderSearch] = useState('');
  const [modelSearch, setModelSearch] = useState('');
  const [modelProviderFilter, setModelProviderFilter] = useState('');
  // removed Costs & Limits table

  // Filtered rows
  const providerRows = useMemo(
    () =>
      (providers.data || []).filter((p: Provider) => {
        const term = providerSearch.toLowerCase();
        return [p.id, p.code, p.name]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(term));
      }),
    [providers.data, providerSearch],
  );
  const modelRows = useMemo(
    () =>
      (models.data || []).filter((m: Model) => {
        const term = modelSearch.toLowerCase();
        if (modelProviderFilter && m.provider_id !== modelProviderFilter) {
          return false;
        }
        return [m.id, m.name, m.code]
          .filter(Boolean)
          .some((v) => String(v).toLowerCase().includes(term));
      }),
    [models.data, modelSearch, modelProviderFilter],
  );
  // no priceRows: moved to model columns

  // Default setters
  const setDefaultProvider = async (id: string) => {
    await api.put('/admin/ai/system/defaults', {
      ...(defaults.data || {}),
      provider_id: id,
    });
    await qc.invalidateQueries({ queryKey: ['ai', 'defaults'] });
  };
  const setDefaultModel = async (id: string) => {
    await api.put('/admin/ai/system/defaults', {
      ...(defaults.data || {}),
      model_id: id,
    });
    await qc.invalidateQueries({ queryKey: ['ai', 'defaults'] });
  };

  const saveManifest = async () => {
    if (!providerDraft?.id) return;
    try {
      const parsed = manifestDraft ? JSON.parse(manifestDraft) : {};
      await api.put(
        `/admin/ai/system/providers/${encodeURIComponent(providerDraft.id)}/manifest`,
        parsed,
      );
      await Promise.all([providers.refetch(), models.refetch()]);
      setProviderDraft(null);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const openSecretsEditor = async (providerId: string) => {
    const res = await api.get(
      `/admin/ai/system/providers/${encodeURIComponent(providerId)}/manifest`,
    );
    const mf = (res.data || {}) as any;
    const fields: Array<{ key: string; label?: string }> = (mf.auth?.fields || []) as any;
    const init: Record<string, string> = {};
    for (const f of fields) init[f.key] = '';
    setSecretsDraft(init);
    setSecretsProviderId(providerId);
    setProviderDraft({ id: providerId, __modal: 'secrets' } as unknown as Provider);
  };

  const saveSecrets = async () => {
    if (!providerDraft?.id && !secretsProviderId) return;
    try {
      const pid = providerDraft?.id || secretsProviderId;
      await api.post(
        `/admin/ai/system/providers/${encodeURIComponent(pid as string)}/secrets`,
        secretsDraft,
      );
      setProviderDraft(null);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  // refreshPrices removed with Costs & Limits

  // Provider actions
  const saveProvider = async () => {
    if (!providerDraft) return;
    if (providerDraft.id) {
      await api.put(
        `/admin/ai/system/providers/${encodeURIComponent(providerDraft.id)}`,
        providerDraft,
      );
    } else {
      await api.post('/admin/ai/system/providers', providerDraft);
    }
    setProviderDraft(null);
    await qc.invalidateQueries({ queryKey: ['ai', 'providers'] });
  };
  const removeProvider = async (id: string) => {
    if (!(await confirmDialog('Delete provider?'))) return;
    await api.del(`/admin/ai/system/providers/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ['ai', 'providers'] });
  };

  // Model actions
  const saveModel = async () => {
    if (!modelDraft) return;
    const errs: {
      provider_id?: string;
      code?: string;
      input_price?: string;
      output_price?: string;
    } = {};
    if (!modelDraft.provider_id) errs.provider_id = 'Select connection';
    if (!modelDraft.code || String(modelDraft.code).trim() === '') errs.code = 'Code is required';
    const pricing: any = (modelDraft as any).pricing || {};
    const inV = pricing.input_per_1k;
    const outV = pricing.output_per_1k;
    if (inV !== undefined && !Number.isFinite(inV)) errs.input_price = 'Invalid number';
    if (outV !== undefined && !Number.isFinite(outV)) errs.output_price = 'Invalid number';
    if (Object.keys(errs).length) {
      setModelErrors(errs);
      return;
    }

    const payload: any = {
      provider_id: (modelDraft as any).provider_id,
      code: (modelDraft as any).code,
      name: (modelDraft as any).name,
      family: (modelDraft as any).family,
      capabilities: (modelDraft as any).capabilities,
      inputs: (modelDraft as any).inputs,
      limits: (modelDraft as any).limits,
    };
    if (inV !== undefined || outV !== undefined) {
      payload.pricing = { ...pricing };
      if (priceUnit === 'per_1m') {
        if (payload.pricing.input_per_1k !== undefined)
          payload.pricing.input_per_1k = payload.pricing.input_per_1k / 1000;
        if (payload.pricing.output_per_1k !== undefined)
          payload.pricing.output_per_1k = payload.pricing.output_per_1k / 1000;
      }
    }

    if ((modelDraft as any).id) {
      await api.put(
        `/admin/ai/system/models/${encodeURIComponent((modelDraft as any).id as string)}` as string,
        payload,
      );
    } else {
      await api.post('/admin/ai/system/models', payload);
    }
    setModelDraft(null);
    setModelErrors({});
    await qc.invalidateQueries({ queryKey: ['ai', 'models'] });
  };
  const removeModel = async (id: string) => {
    if (!(await confirmDialog('Delete model?'))) return;
    await api.del(`/admin/ai/system/models/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ['ai', 'models'] });
  };

  // Price actions
  // price editor removed with Costs & Limits

  const [showCodes, setShowCodes] = useState<Set<string>>(new Set());
  const providerColumns: Column<Provider>[] = [
    { key: 'name', title: 'Name' },
    {
      key: 'code',
      title: 'Provider',
      render: (p) => {
        const id = String(p.id);
        const visible = showCodes.has(id);
        const text: string = String(p.code ?? '');
        const masked = text.length > 18 ? `${text.slice(0, 8)}…${text.slice(-4)}` : text;
        return (
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs" title={text}>
              {visible ? text : masked}
            </span>
            {text && (
              <button
                className="text-gray-500"
                title={visible ? 'Hide' : 'Show'}
                onClick={() =>
                  setShowCodes((s) => {
                    const copy = new Set(s);
                    if (visible) copy.delete(id);
                    else copy.add(id);
                    return copy;
                  })
                }
              >
                {visible ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            )}
          </div>
        );
      },
    },
    { key: 'base_url', title: 'Base URL' },
    {
      key: 'health',
      title: 'Status',
      render: (p) => (
        <div className="flex items-center gap-2">
          <StatusDot status={p.health || p.health_status} />
          <span className="text-xs text-gray-500">{p.health || p.health_status || 'unknown'}</span>
        </div>
      ),
    },
    {
      key: 'default',
      title: 'Default',
      render: (p) =>
        defaults.data?.provider_id === p.id ? (
          <span className="text-green-600">default</span>
        ) : (
          <button
            className="text-green-600 flex items-center gap-1"
            onClick={() => setDefaultProvider(p.id)}
          >
            <CheckCircle2 className="w-4 h-4" /> Set
          </button>
        ),
    },
    {
      key: 'actions',
      title: 'Actions',
      render: (p) => (
        <div className="flex gap-2">
          <button
            className="text-blue-600"
            onClick={() => setProviderDraft(p)}
            title="Edit connection"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            className="text-purple-600"
            onClick={() => openSecretsEditor(p.id)}
            title="Set credentials"
          >
            <KeyRound className="w-4 h-4" />
          </button>
          <button className="text-red-600" onClick={() => removeProvider(p.id)} title="Delete">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  const testModelConnection = async (id: string) => {
    try {
      setModelConn((s) => ({ ...s, [String(id)]: 'unknown' }));
      const res = await api.post(`/admin/ai/system/models/${encodeURIComponent(String(id))}/test`, {
        prompt: 'ping',
      });
      type TestResp = { ok?: boolean; status?: number };
      const d = (res.data || {}) as TestResp;
      const ok = !!(d.ok || (typeof d.status === 'number' && d.status >= 200 && d.status < 300));
      setModelConn((s) => ({ ...s, [String(id)]: ok ? 'ok' : 'fail' }));
    } catch {
      setModelConn((s) => ({ ...s, [String(id)]: 'fail' }));
    }
  };

  const modelColumns: Column<Model>[] = [
    {
      key: 'provider',
      title: 'Provider',
      render: (m) => {
        const p = providers.data?.find((p: Provider) => p.id === m.provider_id);
        const name = p?.name || p?.code || String(m.provider_id);
        const code: string | undefined = p?.code ? String(p.code) : undefined;
        const masked = code && code.length > 18 ? `${code.slice(0, 8)}…${code.slice(-4)}` : code;
        return (
          <div className="flex flex-col">
            <span>{name}</span>
            {masked && <span className="text-xs text-gray-500 font-mono">{masked}</span>}
          </div>
        );
      },
    },
    { key: 'name', title: 'Name', accessor: (m) => m.name || m.code },
    { key: 'code', title: 'Code', accessor: (m) => m.code },
    {
      key: 'input',
      title: 'Input $/1k',
      render: (m) => {
        const v = (m as any)?.pricing?.input_per_1k;
        return typeof v === 'number' ? `$${v.toFixed(4)}` : '—';
      },
    },
    {
      key: 'output',
      title: 'Output $/1k',
      render: (m) => {
        const v = (m as any)?.pricing?.output_per_1k;
        return typeof v === 'number' ? `$${v.toFixed(4)}` : '—';
      },
    },
    {
      key: 'currency',
      title: 'Currency',
      render: (m) => (m as any)?.pricing?.currency || 'USD',
    },
    {
      key: 'enabled',
      title: 'Active',
      render: (m) => {
        const status = modelConn[String(m.id)] || 'unknown';
        const enabled = status === 'ok';
        return (
          <div className="flex items-center gap-2">
            <StatusDot status={enabled ? 'ok' : status === 'fail' ? 'down' : 'unknown'} />
            <span
              className={
                enabled ? 'text-green-600' : status === 'fail' ? 'text-red-600' : 'text-gray-500'
              }
            >
              {status === 'unknown' ? 'unknown' : enabled ? 'On' : 'Off'}
            </span>
          </div>
        );
      },
    },
    {
      key: 'default',
      title: 'Default',
      render: (m) =>
        defaults.data?.model_id === m.id ? (
          <CheckCircle2 className="w-4 h-4 text-green-600" />
        ) : (
          <button
            className="text-blue-600 flex items-center gap-1"
            onClick={() => setDefaultModel(m.id)}
          >
            <CheckCircle2 className="w-4 h-4" /> Set
          </button>
        ),
    },
    {
      key: 'actions',
      title: 'Actions',
      render: (m) => (
        <div className="flex gap-2">
          <button className="text-blue-600" onClick={() => setModelDraft(m)} title="Edit model">
            <Pencil className="w-4 h-4" />
          </button>
          <button
            className="text-green-600"
            onClick={() => testModelConnection(String(m.id))}
            title="Test"
          >
            <RefreshCcw className="w-4 h-4" />
          </button>
          <button className="text-red-600" onClick={() => removeModel(m.id)} title="Delete">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  // price columns removed with Costs & Limits

  return (
    <TabRouter
      plugins={[
        {
          name: 'Connections',
          render: () => (
            <div className="space-y-4">
              <div className="bg-white p-4 rounded shadow space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-lg font-semibold">
                    <Cloud className="w-5 h-5" /> Connections
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        className="border rounded pl-6 pr-2 py-1"
                        placeholder="Search..."
                        value={providerSearch}
                        onChange={(e) => setProviderSearch(e.target.value)}
                      />
                    </div>
                    <button
                      className="flex items-center gap-1 px-2 py-1 rounded bg-blue-600 text-white"
                      onClick={() => setProviderDraft({})}
                    >
                      <Plus className="w-4 h-4" /> Add
                    </button>
                  </div>
                </div>
                <DataTable
                  columns={providerColumns}
                  rows={providerRows}
                  rowKey={(p) => String(p.id)}
                  rowClassName="odd:bg-gray-50"
                  emptyText="No connections yet. Click Add to create one."
                />
              </div>
              <Slideover
                open={!!providerDraft}
                title={
                  //
                  providerDraft?.__modal === 'manifest'
                    ? 'Edit manifest'
                    : //
                      providerDraft?.__modal === 'secrets'
                      ? 'Set secrets'
                      : providerDraft?.id
                        ? 'Edit connection'
                        : 'New connection'
                }
                onClose={() => setProviderDraft(null)}
              >
                {
                  //
                  providerDraft?.__modal === 'manifest' ? (
                    <div className="space-y-2">
                      <div className="flex flex-col gap-1">
                        <label className="text-sm text-gray-600">Manifest (JSON)</label>
                        <textarea
                          className="border rounded px-2 py-1 w-full h-80 font-mono text-sm"
                          value={manifestDraft}
                          onChange={(e) => setManifestDraft(e.target.value)}
                        />
                      </div>
                      <button
                        className="px-3 py-1 rounded bg-blue-600 text-white"
                        onClick={saveManifest}
                      >
                        Save
                      </button>
                    </div>
                  ) : //
                  providerDraft?.__modal === 'secrets' ? (
                    <div className="space-y-3">
                      {Object.keys(secretsDraft).length === 0 && (
                        <div className="text-xs text-gray-500">
                          No fields defined in manifest. Add your API key below.
                        </div>
                      )}
                      {Object.entries(secretsDraft).map(([k, v]) => (
                        <div key={k} className="grid grid-cols-1 md:grid-cols-5 gap-2 items-end">
                          <div className="md:col-span-2 flex flex-col gap-1">
                            <label className="text-sm text-gray-600">Key</label>
                            <input
                              className="border rounded px-2 py-1 w-full font-mono"
                              value={k}
                              onChange={(e) =>
                                setSecretsDraft((s) => {
                                  const n = e.target.value || '';
                                  if (n === k) return s;
                                  const copy: Record<string, string> = { ...s } as any;
                                  const val = copy[k];
                                  delete copy[k];
                                  copy[n] = val;
                                  return copy;
                                })
                              }
                            />
                          </div>
                          <div className="md:col-span-3 flex flex-col gap-1">
                            <label className="text-sm text-gray-600">Value</label>
                            <input
                              className="border rounded px-2 py-1 w-full"
                              type="password"
                              value={v}
                              onChange={(e) =>
                                setSecretsDraft((s) => ({
                                  ...s,
                                  [k]: e.target.value,
                                }))
                              }
                            />
                          </div>
                          <div className="md:col-span-5 flex justify-between">
                            <button
                              type="button"
                              className="text-sm text-gray-600"
                              onClick={() =>
                                setSecretsDraft((s) => ({
                                  ...(s || {}),
                                  ...(s['api_key'] === undefined ? { api_key: '' } : { token: '' }),
                                }))
                              }
                            >
                              <Plus className="w-4 h-4 inline-block mr-1" /> Add field
                            </button>
                            <button
                              type="button"
                              className="text-sm text-red-600"
                              onClick={() =>
                                setSecretsDraft((s) => {
                                  const copy = { ...s } as any;
                                  delete copy[k];
                                  return copy;
                                })
                              }
                            >
                              <Trash2 className="w-4 h-4 inline-block mr-1" /> Remove
                            </button>
                          </div>
                        </div>
                      ))}
                      {Object.entries(secretsDraft).length === 0 && (
                        <div>
                          <button
                            type="button"
                            className="px-3 py-1 rounded bg-gray-200"
                            onClick={() => setSecretsDraft({ api_key: '' })}
                          >
                            Add API key
                          </button>
                        </div>
                      )}
                      <div className="flex justify-end gap-2 pt-1">
                        <button
                          className="px-3 py-1 rounded bg-gray-200"
                          onClick={() => setProviderDraft(null)}
                        >
                          Cancel
                        </button>
                        <button
                          className="px-3 py-1 rounded bg-blue-600 text-white"
                          onClick={saveSecrets}
                        >
                          Save
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex flex-col gap-1">
                        <label className="text-sm text-gray-600">Connection name</label>
                        <input
                          className="border rounded px-2 py-1 w-full"
                          value={providerDraft?.name || ''}
                          onChange={(e) =>
                            setProviderDraft((s) => ({
                              ...(s || {}),
                              name: e.target.value,
                            }))
                          }
                        />
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-sm text-gray-600">Provider code (secret)</label>
                        <div className="relative">
                          <input
                            className="border rounded px-2 py-1 w-full pr-8 font-mono"
                            type={revealProviderCode ? 'text' : 'password'}
                            placeholder="aimlapi key or provider code"
                            value={providerDraft?.code || ''}
                            onChange={(e) =>
                              setProviderDraft((s) => ({
                                ...(s || {}),
                                code: e.target.value,
                              }))
                            }
                          />
                          <button
                            type="button"
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500"
                            title={revealProviderCode ? 'Hide' : 'Show'}
                            onClick={() => setRevealProviderCode((v) => !v)}
                          >
                            {revealProviderCode ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                        <div className="text-xs text-gray-500">
                          If no credential is set via Secrets, this value will be used as Bearer
                          token.
                        </div>
                      </div>
                      <div className="flex flex-col gap-1">
                        <label className="text-sm text-gray-600">Base URL (optional)</label>
                        <input
                          className="border rounded px-2 py-1 w-full"
                          placeholder="https://api.example.com"
                          value={providerDraft?.base_url || ''}
                          onChange={(e) =>
                            setProviderDraft((s) => ({
                              ...(s || {}),
                              base_url: e.target.value,
                            }))
                          }
                        />
                        <div className="text-xs text-gray-500">
                          Tip: use domain only (e.g., https://api.aimlapi.com). Path (/v1/...) is
                          handled automatically.
                        </div>
                      </div>

                      <div className="flex justify-end gap-2 pt-1">
                        <button
                          className="px-3 py-1 rounded bg-gray-200"
                          onClick={() => setProviderDraft(null)}
                        >
                          Cancel
                        </button>
                        <button
                          className="px-3 py-1 rounded bg-blue-600 text-white"
                          onClick={saveProvider}
                        >
                          Save
                        </button>
                      </div>
                    </div>
                  )
                }
              </Slideover>
            </div>
          ),
        },

        {
          name: 'Models',
          render: () => (
            <div className="space-y-4">
              <div className="bg-white p-4 rounded shadow space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-lg font-semibold">
                    <Box className="w-5 h-5" />
                    Models
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        className="border rounded pl-6 pr-2 py-1"
                        placeholder="Search..."
                        value={modelSearch}
                        onChange={(e) => setModelSearch(e.target.value)}
                      />
                    </div>
                    <select
                      className="border rounded px-2 py-1"
                      value={modelProviderFilter}
                      onChange={(e) => setModelProviderFilter(e.target.value)}
                    >
                      <option value="">All providers</option>
                      {providers.data?.map((p: Provider) => (
                        <option key={p.id} value={p.id}>
                          {p.name ||
                            (p.base_url
                              ? (() => {
                                  try {
                                    return new URL(p.base_url).host;
                                  } catch {
                                    return String(p.base_url);
                                  }
                                })()
                              : String(p.code || '').slice(0, 8) +
                                '�' +
                                String(p.code || '').slice(-4))}
                        </option>
                      ))}
                    </select>
                    <button
                      className="flex items-center gap-1 px-2 py-1 rounded bg-blue-600 text-white"
                      onClick={() => setModelDraft({})}
                    >
                      <Plus className="w-4 h-4" /> Add
                    </button>
                    <button
                      className="flex items-center gap-1 px-2 py-1 rounded bg-gray-700 text-white"
                      onClick={() =>
                        setImportDraft({
                          provider_id: providers.data?.[0]?.id,
                          items: [],
                        })
                      }
                    >
                      <Import className="w-4 h-4" /> Import from manifest
                    </button>
                  </div>
                </div>
                <DataTable
                  columns={modelColumns}
                  rows={modelRows}
                  rowKey={(m) => String(m.id)}
                  rowClassName="odd:bg-gray-50"
                />
              </div>
              <Slideover
                open={!!modelDraft}
                title={modelDraft?.id ? 'Edit model' : 'New model'}
                onClose={() => setModelDraft(null)}
              >
                <div className="space-y-2">
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">Connection</label>
                    <select
                      className="border rounded px-2 py-1 w-full"
                      value={modelDraft?.provider_id || ''}
                      onChange={(e) =>
                        setModelDraft((s) => ({ ...(s || {}), provider_id: e.target.value }))
                      }
                    >
                      <option value="">Select connection</option>
                      {providers.data?.map((p: Provider) => (
                        <option key={p.id} value={p.id}>
                          {p.name ||
                            (p.base_url
                              ? (() => {
                                  try {
                                    return new URL(p.base_url).host;
                                  } catch {
                                    return String(p.base_url);
                                  }
                                })()
                              : String(p.code || '').slice(0, 8) +
                                '�' +
                                String(p.code || '').slice(-4))}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">code</label>
                    <input
                      className="border rounded px-2 py-1 w-full"
                      placeholder="aimlapi/llama-3.1-70b"
                      value={modelDraft?.code || ''}
                      onChange={(e) =>
                        setModelDraft((s) => ({
                          ...(s || {}),
                          code: e.target.value,
                        }))
                      }
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">name</label>
                    <input
                      className="border rounded px-2 py-1 w-full"
                      value={modelDraft?.name || ''}
                      onChange={(e) =>
                        setModelDraft((s) => ({ ...(s || {}), name: e.target.value }))
                      }
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">family</label>
                    <input
                      className="border rounded px-2 py-1 w-full"
                      value={modelDraft?.family || ''}
                      onChange={(e) =>
                        setModelDraft((s) => ({
                          ...(s || {}),
                          family: e.target.value,
                        }))
                      }
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">Capabilities</label>
                    <div className="flex flex-wrap gap-2">
                      {[
                        'chat',
                        'tools',
                        'json_mode',
                        'vision',
                        'long_context',
                        'stream',
                        'embed',
                        'rerank',
                      ].map((cap) => {
                        const active = (modelDraft?.capabilities as string[] | undefined)?.includes(
                          cap,
                        );
                        return (
                          <label
                            key={cap}
                            className={`px-2 py-1 border rounded cursor-pointer ${active ? 'bg-blue-50 border-blue-400' : 'bg-white'}`}
                            title={capHelp(cap)}
                          >
                            <input
                              type="checkbox"
                              className="mr-1"
                              checked={!!active}
                              onChange={(e) =>
                                setModelDraft((s) => {
                                  const set = new Set<string>(
                                    Array.isArray(s?.capabilities)
                                      ? (s!.capabilities as string[])
                                      : [],
                                  );
                                  if (e.target.checked) set.add(cap);
                                  else set.delete(cap);
                                  return {
                                    ...(s || {}),
                                    capabilities: Array.from(set),
                                  } as any;
                                })
                              }
                            />
                            {capLabel(cap)}
                          </label>
                        );
                      })}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-sm">
                    <span className="text-gray-600">Pricing unit</span>
                    <select
                      className="border rounded px-2 py-1"
                      value={priceUnit}
                      onChange={(e) => setPriceUnit(e.target.value as 'per_1k' | 'per_1m')}
                    >
                      <option value="per_1k">per 1k tokens</option>
                      <option value="per_1m">per 1M tokens</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600 min-h-10">
                        Input price ({priceUnit === 'per_1k' ? 'per 1k' : 'per 1M'}) (USD)
                      </label>
                      <input
                        className="border rounded px-2 py-1"
                        inputMode="decimal"
                        pattern="[0-9]*[.,]?[0-9]*"
                        value={(modelDraft as any)?.pricing?.input_per_1k ?? ''}
                        onChange={(e) => {
                          const raw = e.target.value.replace(',', '.');
                          if (raw === '') {
                            setModelDraft((s) => ({
                              ...(s || ({} as any)),
                              pricing: { ...((s as any)?.pricing || {}), input_per_1k: undefined },
                            }));
                            return;
                          }
                          if (!/^\d*(?:\.\d*)?$/.test(raw)) return;
                          const num = Number(raw);
                          if (!Number.isFinite(num)) return;
                          setModelDraft((s) => ({
                            ...(s || ({} as any)),
                            pricing: { ...((s as any)?.pricing || {}), input_per_1k: num },
                          }));
                        }}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600 min-h-10">
                        Output price ({priceUnit === 'per_1k' ? 'per 1k' : 'per 1M'}) (USD)
                      </label>
                      <input
                        className="border rounded px-2 py-1"
                        inputMode="decimal"
                        pattern="[0-9]*[.,]?[0-9]*"
                        value={(modelDraft as any)?.pricing?.output_per_1k ?? ''}
                        onChange={(e) => {
                          const raw = e.target.value.replace(',', '.');
                          if (raw === '') {
                            setModelDraft((s) => ({
                              ...(s || ({} as any)),
                              pricing: { ...((s as any)?.pricing || {}), output_per_1k: undefined },
                            }));
                            return;
                          }
                          if (!/^\d*(?:\.\d*)?$/.test(raw)) return;
                          const num = Number(raw);
                          if (!Number.isFinite(num)) return;
                          setModelDraft((s) => ({
                            ...(s || ({} as any)),
                            pricing: { ...((s as any)?.pricing || {}), output_per_1k: num },
                          }));
                        }}
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600 min-h-10">currency</label>
                      <input
                        className="border rounded px-2 py-1"
                        value={(modelDraft as any)?.pricing?.currency ?? 'USD'}
                        onChange={(e) =>
                          setModelDraft((s) => ({
                            ...(s || ({} as any)),
                            pricing: {
                              ...((s as any)?.pricing || {}),
                              currency: e.target.value || 'USD',
                            },
                          }))
                        }
                      />
                    </div>
                  </div>
                  <div className="text-xs text-gray-500">
                    Leave pricing empty to track tokens only.
                  </div>
                  {modelDraft?.id ? (
                    <div className="rounded border p-2 bg-gray-50 text-xs text-gray-700 mt-2">
                      <div className="flex items-center justify-between">
                        <div>Connection test</div>
                        <div className="flex gap-2">
                          <button
                            className="px-2 py-1 rounded bg-gray-200"
                            onClick={async () => {
                              setModelTest({ loading: true, result: null });
                              try {
                                const res = await api.post(
                                  `/admin/ai/system/models/${encodeURIComponent(String(modelDraft.id))}/test`,
                                  { prompt: 'ping' },
                                );
                                setModelTest({ loading: false, result: res.data as any });
                              } catch (e) {
                                setModelTest({
                                  loading: false,
                                  result: {
                                    ok: false,
                                    status: 0,
                                    excerpt: e instanceof Error ? e.message : String(e),
                                  } as any,
                                });
                              }
                            }}
                          >
                            {modelTest.loading ? 'Testing…' : 'Test'}
                          </button>
                        </div>
                      </div>
                      {modelTest.result ? (
                        <div className="mt-1">
                          <div>
                            Status: {modelTest.result.ok ? 'OK' : 'Fail'} ({modelTest.result.status}
                            )
                            {modelTest.result.latency_ms !== undefined
                              ? ` · ${modelTest.result.latency_ms} ms`
                              : ''}
                          </div>
                          {modelTest.result.excerpt ? (
                            <pre className="mt-1 max-h-40 overflow-auto whitespace-pre-wrap">
                              {modelTest.result.excerpt}
                            </pre>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                  <div className="flex justify-end gap-2 pt-1">
                    <button
                      className="px-3 py-1 rounded bg-gray-200"
                      onClick={() => setModelDraft(null)}
                    >
                      Cancel
                    </button>
                    <button
                      className="px-3 py-1 rounded bg-blue-600 text-white"
                      onClick={saveModel}
                    >
                      Save
                    </button>
                  </div>
                </div>
              </Slideover>

              {/* Import from manifest */}
              <Slideover
                open={!!importDraft}
                title="Import models from manifest"
                onClose={() => setImportDraft(null)}
              >
                <div className="space-y-3">
                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">provider</label>
                    <select
                      className="border rounded px-2 py-1"
                      value={importDraft?.provider_id || ''}
                      onChange={async (e) => {
                        const pid = e.target.value;
                        const res = await api.get(
                          `/admin/ai/system/providers/${encodeURIComponent(pid)}/manifest`,
                        );
                        const items = Array.isArray((res.data as any)?.models)
                          ? (res.data as any).models
                          : [];
                        setImportDraft({
                          provider_id: pid,
                          items: items.map((m: any) => ({ ...m, __selected: false })),
                        });
                      }}
                    >
                      <option value="">Select provider</option>
                      {(providers.data || []).map((p: any) => (
                        <option key={p.id} value={p.id}>
                          {p.name ||
                            (p.base_url
                              ? (() => {
                                  try {
                                    return new URL(p.base_url).host;
                                  } catch {
                                    return String(p.base_url);
                                  }
                                })()
                              : String(p.code || '').slice(0, 8) +
                                '�' +
                                String(p.code || '').slice(-4))}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="max-h-80 overflow-auto border rounded">
                    {((importDraft?.items as any[]) || []).map((m: any, i: number) => (
                      <label
                        key={`${m.id}-${i}`}
                        className="flex items-center gap-2 px-2 py-1 border-b last:border-b-0"
                      >
                        <input
                          type="checkbox"
                          checked={!!m.__selected}
                          onChange={(e) =>
                            setImportDraft((s) => {
                              const copy: any = { ...(s || {}) };
                              copy.items = [...(copy.items || [])];
                              copy.items[i] = {
                                ...copy.items[i],
                                __selected: e.target.checked,
                              };
                              return copy;
                            })
                          }
                        />
                        <span className="font-mono text-xs">{m.id}</span>
                        <span className="text-sm text-gray-600">{m.name || m.id}</span>
                      </label>
                    ))}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600">input_per_1k (USD, optional)</label>
                      <input id="imp-in" className="border rounded px-2 py-1" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600">output_per_1k (USD, optional)</label>
                      <input id="imp-out" className="border rounded px-2 py-1" />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600 min-h-10">currency</label>
                      <input id="imp-cur" className="border rounded px-2 py-1" defaultValue="USD" />
                    </div>
                  </div>
                  <button
                    className="px-3 py-1 rounded bg-blue-600 text-white"
                    onClick={async () => {
                      const pid = importDraft?.provider_id as string;
                      if (!pid) return;
                      const inV = (document.getElementById('imp-in') as HTMLInputElement | null)
                        ?.value;
                      const outV = (document.getElementById('imp-out') as HTMLInputElement | null)
                        ?.value;
                      const curV =
                        (document.getElementById('imp-cur') as HTMLInputElement | null)?.value ||
                        'USD';
                      const pricing =
                        inV || outV
                          ? {
                              input_per_1k: inV ? Number(inV) : undefined,
                              output_per_1k: outV ? Number(outV) : undefined,
                              currency: curV,
                            }
                          : undefined;
                      const items = (importDraft?.items || []).filter((m: any) => m.__selected);
                      for (const m of items) {
                        await api.post('/admin/ai/system/models', {
                          provider_id: pid,
                          code: m.id,
                          name: m.name,
                          family: m.family,
                          capabilities: m.capabilities,
                          inputs: m.inputs,
                          limits: m.limits,
                          pricing,
                        });
                      }
                      setImportDraft(null);
                      await models.refetch();
                    }}
                  >
                    Import selected
                  </button>
                </div>
              </Slideover>
            </div>
          ),
        },
        // Removed: legacy Costs & Limits tab (moved to Models)
        {
          name: 'Routing Profiles',
          render: () => <RoutingProfilesTab />,
        },
        {
          name: 'Presets',
          render: () => <PresetsTab />,
        },
      ]}
    />
  );
}

// Legacy: not used anymore; kept above for reference.
/*
function SecretsTab({ providers, onManage }: { providers: any[]; onManage: (id: string) => void }) {
  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded shadow space-y-4">
        <div className="flex items-center gap-2 text-lg font-semibold">
          Connections
          Connections
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {providers.map((p) => (
            <div key={p.id} className="border rounded p-3 flex flex-col gap-2">
              <div className="font-semibold">{p.code || p.name}</div>
              <div className="text-xs text-gray-500">ID: {p.id}</div>
              <div className="text-xs text-gray-500">Base URL: {p.base_url || 'default'}</div>
              <button className="px-2 py-1 rounded bg-blue-600 text-white w-max" onClick={() => onManage(String(p.id))}>Set credentials</button>
            </div>
          ))}
          {!providers?.length && <div className="text-sm text-gray-500">No connections yet. Add a provider/connection first.</div>}
        </div>
      </div>
    </div>
  );
}
*/

function RoutingProfilesTab() {
  const qc = useQueryClient();
  const profiles = useQuery({
    queryKey: ['ai', 'profiles'],
    queryFn: async () => (await api.get('/admin/ai/system/profiles')).data || [],
  });
  // use shared caches for providers/models from the page
  const providers = useQuery({
    queryKey: ['ai', 'providers'],
    queryFn: async () => (await api.get('/admin/ai/system/providers')).data || [],
  });
  const models = useQuery({
    queryKey: ['ai', 'models'],
    queryFn: async () => (await api.get('/admin/ai/system/models')).data || [],
  });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [draft, setDraft] = useState<any | null>(null);
  const [search, setSearch] = useState('');

  const rows = useMemo(
    () =>
      ((profiles.data as any[]) || []).filter((p: any) =>
        (p.name || '').toLowerCase().includes(search.toLowerCase()),
      ),
    [profiles.data, search],
  );
  const capabilityOptions = useMemo(() => {
    const set = new Set<string>();
    for (const m of (models.data as any[]) || []) {
      for (const c of m.capabilities || []) set.add(String(c));
    }
    // ensure stable order for known caps
    const known = [
      'chat',
      'tools',
      'json_mode',
      'vision',
      'long_context',
      'stream',
      'embed',
      'rerank',
    ];
    const rest = [...set].filter((c) => !known.includes(c));
    return [...known.filter((c) => set.has(c)), ...rest];
  }, [models.data]);

  const save = async () => {
    if (!draft) return;
    const body = {
      name: draft.name || 'default',
      enabled: !!draft.enabled,
      rules: draft.rules || [],
    };
    if (draft.id) await api.put(`/admin/ai/system/profiles/${encodeURIComponent(draft.id)}`, body);
    else await api.post(`/admin/ai/system/profiles`, body);
    setDraft(null);
    await qc.invalidateQueries({ queryKey: ['ai', 'profiles'] });
  };
  const remove = async (id: string) => {
    if (!(await confirmDialog('Delete this profile?'))) return;
    await api.del(`/admin/ai/system/profiles/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ['ai', 'profiles'] });
  };
  const validate = async (id: string) => {
    const res = await api.post(`/admin/ai/system/profiles/${encodeURIComponent(id)}/validate`, {});
    const data = res.data as any;
    if (data.ok) alert('OK');
    else alert((data.errors || []).join('\n'));
  };

  const columns: Column<any>[] = [
    { key: 'name', title: 'Name' },
    { key: 'enabled', title: 'Enabled' },
    { key: 'rules', title: 'Rules', accessor: (r) => r.rules?.length || 0 },
    {
      key: 'actions',
      title: 'Actions',
      render: (r) => (
        <div className="flex gap-2">
          <button className="text-blue-600" onClick={() => setDraft(r)}>
            <Pencil className="w-4 h-4" />
          </button>
          <button className="text-green-600" onClick={() => validate(r.id)} title="Validate">
            <CheckCircle2 className="w-4 h-4" />
          </button>
          <button className="text-red-600" onClick={() => remove(r.id)}>
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded shadow space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-lg font-semibold">Routing Profiles</div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                className="border rounded pl-6 pr-2 py-1"
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button
              className="flex items-center gap-1 px-2 py-1 rounded bg-blue-600 text-white"
              onClick={() => setDraft({ enabled: true, rules: [] })}
            >
              <Plus className="w-4 h-4" /> Add
            </button>
          </div>
        </div>
        <DataTable
          columns={columns}
          rows={rows}
          rowKey={(r) => String(r.id)}
          rowClassName="odd:bg-gray-50"
        />
      </div>
      <Slideover
        open={!!draft}
        title={draft?.id ? 'Edit profile' : 'New profile'}
        onClose={() => setDraft(null)}
      >
        <div className="space-y-4">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">name</label>
            <input
              className="border rounded px-2 py-1 w-full"
              value={draft?.name || ''}
              onChange={(e) => setDraft((s: any) => ({ ...(s || {}), name: e.target.value }))}
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="prof-enabled"
              type="checkbox"
              checked={!!draft?.enabled}
              onChange={(e) => setDraft((s: any) => ({ ...(s || {}), enabled: e.target.checked }))}
            />
            <label htmlFor="prof-enabled" className="text-sm text-gray-600">
              enabled
            </label>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold text-gray-700">Rules</div>
              <button
                className="px-2 py-1 rounded bg-gray-200"
                onClick={() =>
                  setDraft((s: any) => ({
                    ...(s || {}),
                    rules: [
                      ...((s?.rules as any[]) || []),
                      {
                        task: 'chat',
                        selector: { capabilities: [] },
                        route: { provider_id: '', model_id: '', params: {}, fallback: [] },
                      },
                    ],
                  }))
                }
              >
                + Add rule
              </button>
            </div>

            {((draft?.rules as any[]) || []).map((rule: any, idx: number) => {
              const providerId = String(rule?.route?.provider_id || '');
              const providerModels = ((models.data as any[]) || []).filter(
                (m) => !providerId || String(m.provider_id) === providerId,
              );
              return (
                <div key={idx} className="rounded border p-2 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-600">Rule #{idx + 1}</div>
                    <button
                      className="text-red-600 text-sm"
                      onClick={() =>
                        setDraft((s: any) => ({
                          ...(s || {}),
                          rules: (s?.rules as any[]).filter((_: any, i: number) => i !== idx),
                        }))
                      }
                    >
                      Remove
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600">task</label>
                      <select
                        className="border rounded px-2 py-1 w-full"
                        value={rule.task || 'chat'}
                        onChange={(e) =>
                          setDraft((s: any) => {
                            const copy = { ...s };
                            copy.rules[idx].task = e.target.value;
                            return copy;
                          })
                        }
                      >
                        <option value="chat">chat</option>
                        <option value="embed">embed</option>
                        <option value="rerank">rerank</option>
                        <option value="image">image</option>
                      </select>
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600">plan</label>
                      <select
                        className="border rounded px-2 py-1 w-full"
                        value={rule.selector?.plan || ''}
                        onChange={(e) =>
                          setDraft((s: any) => {
                            const copy = { ...s };
                            copy.rules[idx].selector = {
                              ...(copy.rules[idx].selector || {}),
                              plan: e.target.value || undefined,
                            };
                            return copy;
                          })
                        }
                      >
                        <option value="">(any)</option>
                        <option value="Free">Free</option>
                        <option value="Premium">Premium</option>
                        <option value="Premium+">Premium+</option>
                      </select>
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600">min_context</label>
                      <input
                        className="border rounded px-2 py-1"
                        type="number"
                        value={rule.selector?.min_context ?? ''}
                        onChange={(e) =>
                          setDraft((s: any) => {
                            const copy = { ...s };
                            const v = e.target.value === '' ? undefined : Number(e.target.value);
                            copy.rules[idx].selector = {
                              ...(copy.rules[idx].selector || {}),
                              min_context: v,
                            };
                            return copy;
                          })
                        }
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600">max_price_per_1k</label>
                      <input
                        className="border rounded px-2 py-1"
                        type="number"
                        step="0.0001"
                        value={rule.selector?.max_price_per_1k ?? ''}
                        onChange={(e) =>
                          setDraft((s: any) => {
                            const copy = { ...s };
                            const v = e.target.value === '' ? undefined : Number(e.target.value);
                            copy.rules[idx].selector = {
                              ...(copy.rules[idx].selector || {}),
                              max_price_per_1k: v,
                            };
                            return copy;
                          })
                        }
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">capabilities</label>
                    <div className="flex flex-wrap gap-2">
                      {capabilityOptions.map((cap) => {
                        const active = (rule.selector?.capabilities || []).includes(cap);
                        return (
                          <label
                            key={cap}
                            className={`px-2 py-1 border rounded cursor-pointer ${active ? 'bg-blue-50 border-blue-400' : 'bg-white'}`}
                          >
                            <input
                              type="checkbox"
                              className="mr-1"
                              checked={active}
                              onChange={(e) =>
                                setDraft((s: any) => {
                                  const copy = { ...(s || {}) };
                                  const arr = new Set<string>(
                                    copy.rules[idx].selector?.capabilities || [],
                                  );
                                  if (e.target.checked) arr.add(cap);
                                  else arr.delete(cap);
                                  copy.rules[idx].selector = {
                                    ...(copy.rules[idx].selector || {}),
                                    capabilities: Array.from(arr),
                                  };
                                  return copy;
                                })
                              }
                            />
                            {cap}
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600">provider</label>
                      <select
                        className="border rounded px-2 py-1 w-full"
                        value={providerId}
                        onChange={(e) =>
                          setDraft((s: any) => {
                            const copy = { ...s };
                            copy.rules[idx].route = {
                              ...(copy.rules[idx].route || {}),
                              provider_id: e.target.value,
                              model_id: '',
                            };
                            return copy;
                          })
                        }
                      >
                        <option value="">Select provider</option>
                        {((providers.data as any[]) || []).map((p) => (
                          <option key={String(p.id)} value={String(p.id)}>
                            {p.code || p.name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="flex flex-col gap-1">
                      <label className="text-sm text-gray-600">model</label>
                      <select
                        className="border rounded px-2 py-1 w-full"
                        value={rule.route?.model_id || ''}
                        onChange={(e) =>
                          setDraft((s: any) => {
                            const copy = { ...s };
                            copy.rules[idx].route = {
                              ...(copy.rules[idx].route || {}),
                              model_id: e.target.value,
                            };
                            return copy;
                          })
                        }
                      >
                        <option value="">Select model</option>
                        {providerModels.map((m) => (
                          <option key={String(m.id)} value={String(m.id)}>
                            {m.name || m.code}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-sm text-gray-600">params (JSON, optional)</label>
                    <textarea
                      className="border rounded px-2 py-1 w-full h-24 font-mono text-sm"
                      value={JSON.stringify(rule.route?.params || {}, null, 2)}
                      onChange={(e) => {
                        try {
                          const obj = JSON.parse(e.target.value);
                          setDraft((s: any) => {
                            const copy = { ...s };
                            copy.rules[idx].route = {
                              ...(copy.rules[idx].route || {}),
                              params: obj,
                            };
                            return copy;
                          });
                        } catch {
                          /* ignore */
                        }
                      }}
                    />
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">fallback</div>
                      <button
                        className="px-2 py-1 rounded bg-gray-100"
                        onClick={() =>
                          setDraft((s: any) => {
                            const copy = { ...s };
                            const fb = [...(copy.rules[idx].route?.fallback || [])];
                            fb.push({ provider_id: '', model_id: '' });
                            copy.rules[idx].route = {
                              ...(copy.rules[idx].route || {}),
                              fallback: fb,
                            };
                            return copy;
                          })
                        }
                      >
                        + Add fallback
                      </button>
                    </div>
                    {(rule.route?.fallback || []).map((fb: any, j: number) => (
                      <div key={j} className="grid grid-cols-1 md:grid-cols-3 gap-2 items-center">
                        <select
                          className="border rounded px-2 py-1 w-full"
                          value={fb.provider_id || ''}
                          onChange={(e) =>
                            setDraft((s: any) => {
                              const copy = { ...s };
                              const arr = [...(copy.rules[idx].route?.fallback || [])];
                              arr[j] = {
                                ...(arr[j] || {}),
                                provider_id: e.target.value,
                                model_id: '',
                              };
                              copy.rules[idx].route = {
                                ...(copy.rules[idx].route || {}),
                                fallback: arr,
                              };
                              return copy;
                            })
                          }
                        >
                          <option value="">Provider</option>
                          {((providers.data as any[]) || []).map((p) => (
                            <option key={String(p.id)} value={String(p.id)}>
                              {p.code || p.name}
                            </option>
                          ))}
                        </select>
                        <select
                          className="border rounded px-2 py-1 w-full"
                          value={fb.model_id || ''}
                          onChange={(e) =>
                            setDraft((s: any) => {
                              const copy = { ...s };
                              const arr = [...(copy.rules[idx].route?.fallback || [])];
                              arr[j] = { ...(arr[j] || {}), model_id: e.target.value };
                              copy.rules[idx].route = {
                                ...(copy.rules[idx].route || {}),
                                fallback: arr,
                              };
                              return copy;
                            })
                          }
                        >
                          <option value="">Model</option>
                          {((models.data as any[]) || [])
                            .filter(
                              (m) =>
                                !fb.provider_id || String(m.provider_id) === String(fb.provider_id),
                            )
                            .map((m) => (
                              <option key={String(m.id)} value={String(m.id)}>
                                {m.name || m.code}
                              </option>
                            ))}
                        </select>
                        <button
                          className="text-red-600"
                          onClick={() =>
                            setDraft((s: any) => {
                              const copy = { ...s };
                              const arr = [...(copy.rules[idx].route?.fallback || [])];
                              copy.rules[idx].route = {
                                ...(copy.rules[idx].route || {}),
                                fallback: arr.filter((_: any, k: number) => k !== j),
                              };
                              return copy;
                            })
                          }
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex gap-2">
            <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={save}>
              Save
            </button>
            <button className="px-3 py-1 rounded bg-gray-200" onClick={() => setDraft(null)}>
              Cancel
            </button>
          </div>
        </div>
      </Slideover>
    </div>
  );
}

function PresetsTab() {
  const qc = useQueryClient();
  const presets = useQuery({
    queryKey: ['ai', 'presets'],
    queryFn: async () => (await api.get('/admin/ai/system/presets')).data || [],
  });
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [draft, setDraft] = useState<any | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [search, setSearch] = useState('');
  const rows = useMemo(
    () =>
      ((presets.data as any[]) || []).filter((p: any) =>
        (p.name || '').toLowerCase().includes(search.toLowerCase()),
      ),
    [presets.data, search],
  );

  const save = async () => {
    if (!draft) return;
    const body = {
      name: draft.name || 'preset',
      task: draft.task || 'chat',
      params: draft.params || {},
    };
    if (draft.id) await api.put(`/admin/ai/system/presets/${encodeURIComponent(draft.id)}`, body);
    else await api.post(`/admin/ai/system/presets`, body);
    setDraft(null);
    await qc.invalidateQueries({ queryKey: ['ai', 'presets'] });
  };
  const remove = async (id: string) => {
    if (!(await confirmDialog('Delete this preset?'))) return;
    await api.del(`/admin/ai/system/presets/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ['ai', 'presets'] });
  };

  const columns: Column<any>[] = [
    { key: 'name', title: 'Name' },
    { key: 'task', title: 'Task' },
    {
      key: 'params',
      title: 'Params',
      accessor: (r) => (JSON.stringify(r.params)?.slice(0, 60) || '') + '...',
    },
    {
      key: 'actions',
      title: 'Actions',
      render: (r) => (
        <div className="flex gap-2">
          <button className="text-blue-600" onClick={() => setDraft(r)}>
            <Pencil className="w-4 h-4" />
          </button>
          <button className="text-red-600" onClick={() => remove(r.id)}>
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      <div className="bg-white p-4 rounded shadow space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-lg font-semibold">Presets</div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                className="border rounded pl-6 pr-2 py-1"
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button
              className="flex items-center gap-1 px-2 py-1 rounded bg-blue-600 text-white"
              onClick={() => setDraft({ task: 'chat', params: {} })}
            >
              <Plus className="w-4 h-4" /> Add
            </button>
          </div>
        </div>
        <DataTable
          columns={columns}
          rows={rows}
          rowKey={(r) => String(r.id)}
          rowClassName="odd:bg-gray-50"
        />
      </div>
      <Slideover
        open={!!draft}
        title={draft?.id ? 'Edit preset' : 'New preset'}
        onClose={() => setDraft(null)}
      >
        <div className="space-y-2">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">name</label>
            <input
              className="border rounded px-2 py-1 w-full"
              value={draft?.name || ''}
              onChange={(e) => setDraft((s: any) => ({ ...(s || {}), name: e.target.value }))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">task</label>
            <select
              className="border rounded px-2 py-1 w-full"
              value={draft?.task || 'chat'}
              onChange={(e) => setDraft((s: any) => ({ ...(s || {}), task: e.target.value }))}
            >
              <option value="chat">chat</option>
              <option value="embed">embed</option>
              <option value="rerank">rerank</option>
            </select>
          </div>
          {/* Friendly params form */}
          <div className="space-y-3">
            <div className="text-sm font-semibold text-gray-700">Parameters</div>
            {/* Chat params */}
            {(!draft?.task || draft.task === 'chat') && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-gray-600">temperature (0..2)</label>
                  <input
                    className="border rounded px-2 py-1"
                    type="number"
                    step={0.1}
                    min={0}
                    max={2}
                    value={draft?.params?.temperature ?? ''}
                    onChange={(e) =>
                      setDraft((s: any) => ({
                        ...(s || {}),
                        params: {
                          ...(s?.params || {}),
                          temperature: e.target.value === '' ? undefined : Number(e.target.value),
                        },
                      }))
                    }
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-gray-600">top_p (0..1)</label>
                  <input
                    className="border rounded px-2 py-1"
                    type="number"
                    step={0.01}
                    min={0}
                    max={1}
                    value={draft?.params?.top_p ?? ''}
                    onChange={(e) =>
                      setDraft((s: any) => ({
                        ...(s || {}),
                        params: {
                          ...(s?.params || {}),
                          top_p: e.target.value === '' ? undefined : Number(e.target.value),
                        },
                      }))
                    }
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-gray-600">max_tokens</label>
                  <input
                    className="border rounded px-2 py-1"
                    type="number"
                    min={1}
                    value={draft?.params?.max_tokens ?? ''}
                    onChange={(e) =>
                      setDraft((s: any) => ({
                        ...(s || {}),
                        params: {
                          ...(s?.params || {}),
                          max_tokens: e.target.value === '' ? undefined : Number(e.target.value),
                        },
                      }))
                    }
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="json-mode"
                    type="checkbox"
                    checked={!!draft?.params?.json_mode}
                    onChange={(e) =>
                      setDraft((s: any) => ({
                        ...(s || {}),
                        params: { ...(s?.params || {}), json_mode: e.target.checked || undefined },
                      }))
                    }
                  />
                  <label htmlFor="json-mode" className="text-sm text-gray-600">
                    json_mode
                  </label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="stream"
                    type="checkbox"
                    checked={!!draft?.params?.stream}
                    onChange={(e) =>
                      setDraft((s: any) => ({
                        ...(s || {}),
                        params: { ...(s?.params || {}), stream: e.target.checked || undefined },
                      }))
                    }
                  />
                  <label htmlFor="stream" className="text-sm text-gray-600">
                    stream
                  </label>
                </div>
              </div>
            )}

            {/* Embed params */}
            {draft?.task === 'embed' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-gray-600">dimensions</label>
                  <input
                    className="border rounded px-2 py-1"
                    type="number"
                    min={1}
                    value={draft?.params?.dimensions ?? ''}
                    onChange={(e) =>
                      setDraft((s: any) => ({
                        ...(s || {}),
                        params: {
                          ...(s?.params || {}),
                          dimensions: e.target.value === '' ? undefined : Number(e.target.value),
                        },
                      }))
                    }
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-gray-600">truncate</label>
                  <select
                    className="border rounded px-2 py-1"
                    value={draft?.params?.truncate ?? ''}
                    onChange={(e) =>
                      setDraft((s: any) => ({
                        ...(s || {}),
                        params: { ...(s?.params || {}), truncate: e.target.value || undefined },
                      }))
                    }
                  >
                    <option value="">(auto)</option>
                    <option value="start">start</option>
                    <option value="end">end</option>
                    <option value="none">none</option>
                  </select>
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-gray-600">input_type</label>
                  <select
                    className="border rounded px-2 py-1"
                    value={draft?.params?.input_type ?? ''}
                    onChange={(e) =>
                      setDraft((s: any) => ({
                        ...(s || {}),
                        params: { ...(s?.params || {}), input_type: e.target.value || undefined },
                      }))
                    }
                  >
                    <option value="">(text)</option>
                    <option value="text">text</option>
                    <option value="document">document</option>
                    <option value="code">code</option>
                  </select>
                </div>
              </div>
            )}

            {/* Rerank params */}
            {draft?.task === 'rerank' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-sm text-gray-600">top_n</label>
                  <input
                    className="border rounded px-2 py-1"
                    type="number"
                    min={1}
                    value={draft?.params?.top_n ?? ''}
                    onChange={(e) =>
                      setDraft((s: any) => ({
                        ...(s || {}),
                        params: {
                          ...(s?.params || {}),
                          top_n: e.target.value === '' ? undefined : Number(e.target.value),
                        },
                      }))
                    }
                  />
                </div>
                <div className="flex items-center gap-2">
                  <input
                    id="return-docs"
                    type="checkbox"
                    checked={!!draft?.params?.return_documents}
                    onChange={(e) =>
                      setDraft((s: any) => ({
                        ...(s || {}),
                        params: {
                          ...(s?.params || {}),
                          return_documents: e.target.checked || undefined,
                        },
                      }))
                    }
                  />
                  <label htmlFor="return-docs" className="text-sm text-gray-600">
                    return_documents
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Advanced JSON (optional) */}
          <div className="space-y-1">
            <button className="text-sm underline" onClick={() => setShowAdvanced((v) => !v)}>
              {showAdvanced ? 'Hide advanced JSON' : 'Show advanced JSON'}
            </button>
            {showAdvanced && (
              <textarea
                className="border rounded px-2 py-1 w-full h-40 font-mono text-sm"
                value={JSON.stringify(draft?.params || {}, null, 2)}
                onChange={(e) => {
                  try {
                    const obj = JSON.parse(e.target.value);
                    setDraft((s: any) => ({ ...(s || {}), params: obj }));
                  } catch {
                    // ignore until valid JSON
                  }
                }}
              />
            )}
          </div>
          <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={save}>
            Save
          </button>
        </div>
      </Slideover>
    </div>
  );
}

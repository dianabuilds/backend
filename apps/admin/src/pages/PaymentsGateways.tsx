import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { api } from '../api/client';
import EditDeleteActions from '../components/common/EditDeleteActions';
import FormActions from '../components/common/FormActions';
import ListSection from '../components/common/ListSection';
import DataTable from '../components/DataTable';
import type { Column } from '../components/DataTable.helpers';
import { confirmWithEnv } from '../utils/env';

type Gateway = {
  id: string;
  slug: string;
  type: string;
  enabled: boolean;
  priority: number;
  config: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
};

type GatewayFeeConfig = {
  fee_mode?: 'none' | 'percent' | string;
  fee_percent?: number;
  fee_fixed_cents?: number;
  min_fee_cents?: number;
};

const TYPES = [
  { value: 'crypto_jwt', label: 'Crypto (JWT token placeholder)' },
  { value: 'stripe_jwt', label: 'Stripe (JWT token placeholder)' },
];

export default function PaymentsGateways() {
  const qc = useQueryClient();

  const { data = [], isLoading, error } = useQuery({
    queryKey: ['payments', 'gateways'],
    queryFn: async () => (await api.get<Gateway[]>('/admin/payments/gateways')).data || [],
    staleTime: 10_000,
  });

  const [draft, setDraft] = useState<Partial<Gateway>>({
    slug: '',
    type: 'crypto_jwt',
    enabled: true,
    priority: 100,
    config: {
      fee_mode: 'percent',
      fee_percent: 0,
      fee_fixed_cents: 0,
      min_fee_cents: 0,
    },
  });

  const isEdit = Boolean(draft.id);

  const resetDraft = () =>
    setDraft({
      slug: '',
      type: 'crypto_jwt',
      enabled: true,
      priority: 100,
      config: {
        fee_mode: 'percent',
        fee_percent: 0,
        fee_fixed_cents: 0,
        min_fee_cents: 0,
      },
    });

  const save = async () => {
    if (!draft.slug || !draft.type) return alert('Slug и Type обязательны');
    const payload = {
      slug: draft.slug,
      type: draft.type,
      enabled: !!draft.enabled,
      priority: Number(draft.priority ?? 100),
      config: draft.config ?? {},
    };
    if (isEdit) {
      await api.put(`/admin/payments/gateways/${encodeURIComponent(draft.id!)}`, payload);
    } else {
      await api.post(`/admin/payments/gateways`, payload);
    }
    resetDraft();
    await qc.invalidateQueries({ queryKey: ['payments', 'gateways'] });
  };

  const remove = async (id: string) => {
    if (!(await confirmWithEnv('Удалить шлюз?'))) return;
    await api.del(`/admin/payments/gateways/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ['payments', 'gateways'] });
  };

  const edit = (g: Gateway) => {
    setDraft({
      id: g.id,
      slug: g.slug,
      type: g.type,
      enabled: g.enabled,
      priority: g.priority,
      config: g.config || {},
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Fee helpers
  const setFee = (
    key: 'fee_mode' | 'fee_percent' | 'fee_fixed_cents' | 'min_fee_cents',
    value: string | number,
  ) => {
    setDraft((d) => ({ ...d, config: { ...(d.config || {}), [key]: value } }));
  };

  // Verify token
  const [verify, setVerify] = useState<{
    token: string;
    amount: number;
    currency: string;
    preferred_slug?: string;
  }>({
    token: '',
    amount: 100,
    currency: 'USD',
    preferred_slug: '',
  });
  const [verifyRes, setVerifyRes] = useState<string>('');

  const doVerify = async () => {
    setVerifyRes('');
    try {
      const res = await api.post<{ ok: boolean; gateway?: string }>(`/admin/payments/verify`, {
        token: verify.token,
        amount: Number(verify.amount || 0),
        currency: verify.currency || null,
        preferred_slug: verify.preferred_slug || null,
      });
      const ok = (res.data as unknown as { ok?: boolean }).ok;
      const gateway = (res.data as unknown as { gateway?: string }).gateway || '-';
      setVerifyRes(`ok=${String(ok)}, gateway=${gateway}`);
    } catch (e: unknown) {
      setVerifyRes(`Ошибка: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-lg font-semibold">Payments — Gateways</h1>

      <div className="rounded border p-3">
        <div className="text-sm text-gray-500 mb-2">
          {isEdit ? 'Редактирование шлюза' : 'Создание шлюза'}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-500">Slug</label>
            <input
              className="w-full rounded border px-2 py-1"
              value={draft.slug || ''}
              onChange={(e) => setDraft({ ...draft, slug: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Type</label>
            <select
              className="w-full rounded border px-2 py-1"
              value={draft.type || ''}
              onChange={(e) => setDraft({ ...draft, type: e.target.value })}
            >
              {TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500">Priority</label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={draft.priority ?? 100}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  priority: parseInt(e.target.value || '100', 10),
                })
              }
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="enabled"
              type="checkbox"
              checked={!!draft.enabled}
              onChange={(e) => setDraft({ ...draft, enabled: e.target.checked })}
            />
            <label htmlFor="enabled" className="text-sm">
              Enabled
            </label>
          </div>
          <div>
            <label className="block text-xs text-gray-500">Fee mode</label>
            <select
              className="w-full rounded border px-2 py-1"
              value={(draft.config as GatewayFeeConfig | undefined)?.fee_mode ?? 'percent'}
              onChange={(e) => setFee('fee_mode', e.target.value)}
            >
              <option value="none">none</option>
              <option value="percent">percent</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500">Fee percent</label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={Number((draft.config as GatewayFeeConfig | undefined)?.fee_percent ?? 0)}
              onChange={(e) => setFee('fee_percent', parseFloat(e.target.value || '0'))}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Fee fixed (cents)</label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={Number((draft.config as GatewayFeeConfig | undefined)?.fee_fixed_cents ?? 0)}
              onChange={(e) => setFee('fee_fixed_cents', parseInt(e.target.value || '0', 10))}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Min fee (cents)</label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={Number((draft.config as GatewayFeeConfig | undefined)?.min_fee_cents ?? 0)}
              onChange={(e) => setFee('min_fee_cents', parseInt(e.target.value || '0', 10))}
            />
          </div>
        </div>
        <FormActions
          primaryLabel={isEdit ? 'Save' : 'Create'}
          onPrimary={save}
          secondaryLabel="Reset"
          onSecondary={resetDraft}
        />
      </div>

      <ListSection title="Список шлюзов" loading={isLoading} error={error}>
        {(() => {
          const columns: Column<Gateway>[] = [
            { key: 'slug', title: 'Slug', accessor: (r) => r.slug },
            { key: 'type', title: 'Type', accessor: (r) => r.type },
            { key: 'priority', title: 'Priority', accessor: (r) => String(r.priority) },
            { key: 'enabled', title: 'Enabled', accessor: (r) => (r.enabled ? 'yes' : 'no') },
            {
              key: 'fee',
              title: 'Fee',
              accessor: (r) => {
                const c = (r.config || {}) as GatewayFeeConfig;
                const mode = c.fee_mode || 'none';
                const pct = Number(c.fee_percent || 0);
                const fx = Number(c.fee_fixed_cents || 0);
                return `${mode}${pct ? ` ${pct}%` : ''}${fx ? ` + ${fx}c` : ''}`;
              },
            },
            {
              key: 'actions',
              title: 'Actions',
              render: (r) => (
                <EditDeleteActions onEdit={() => edit(r as Gateway)} onDelete={() => remove(r.id)} />
              ),
            },
          ];
          return (
            <DataTable
              columns={columns}
              rows={data}
              rowKey={(r) => r.id}
              emptyText="Нет шлюзов"
            />
          );
        })()}
      </ListSection>

      <div className="rounded border p-3">
        <div className="text-sm text-gray-500 mb-2">Проверка токена</div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="md:col-span-2">
            <label className="block text-xs text-gray-500">Token (JWT)</label>
            <textarea
              className="w-full rounded border px-2 py-1 font-mono text-xs min-h-[80px]"
              value={verify.token}
              onChange={(e) => setVerify((v) => ({ ...v, token: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Amount (cents)</label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={verify.amount}
              onChange={(e) =>
                setVerify((v) => ({
                  ...v,
                  amount: parseInt(e.target.value || '0', 10),
                }))
              }
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Currency</label>
            <input
              className="w-full rounded border px-2 py-1"
              value={verify.currency}
              onChange={(e) => setVerify((v) => ({ ...v, currency: e.target.value }))}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Preferred slug (optional)</label>
            <input
              className="w-full rounded border px-2 py-1"
              value={verify.preferred_slug || ''}
              onChange={(e) => setVerify((v) => ({ ...v, preferred_slug: e.target.value }))}
            />
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <button
            onClick={doVerify}
            className="text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200"
          >
            Проверить
          </button>
          {verifyRes ? <div className="text-sm">{verifyRes}</div> : null}
        </div>
      </div>
    </div>
  );
}

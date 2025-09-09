import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { api } from '../api/client';
import EditDeleteActions from '../components/common/EditDeleteActions';
import FormActions from '../components/common/FormActions';
import ListSection from '../components/common/ListSection';
import DataTable from '../components/DataTable';
import type { Column } from '../components/DataTable.helpers';
import { confirmWithEnv } from '../utils/env';

type Plan = {
  id: string;
  slug: string;
  title: string;
  description?: string | null;
  price_cents?: number | null;
  currency?: string | null;
  is_active: boolean;
  order: number;
  monthly_limits: Record<string, number>;
  features: Record<string, unknown>;
};

export default function PremiumPlans() {
  const qc = useQueryClient();
  const { data = [], isLoading, error } = useQuery({
    queryKey: ['premium', 'plans'],
    queryFn: async () => (await api.get<Plan[]>('/admin/premium/plans')).data || [],
    staleTime: 10_000,
  });

  const [draft, setDraft] = useState<Partial<Plan>>({
    slug: '',
    title: '',
    is_active: true,
    order: 100,
    currency: 'USD',
    monthly_limits: { stories: 0 },
    features: {},
  });

  useEffect(() => {
    if (!data || data.length === 0) return;
  }, [data]);

  const save = async () => {
    if (!draft.slug || !draft.title) return alert('Slug и Title обязательны');
    if (draft.id) {
      await api.put(`/admin/premium/plans/${encodeURIComponent(draft.id)}`, draft);
    } else {
      await api.post(`/admin/premium/plans`, draft);
    }
    setDraft({
      slug: '',
      title: '',
      is_active: true,
      order: 100,
      currency: 'USD',
      monthly_limits: { stories: 0 },
      features: {},
    });
    await qc.invalidateQueries({ queryKey: ['premium', 'plans'] });
  };

  const remove = async (id: string) => {
    if (!(await confirmWithEnv('Удалить тариф?'))) return;
    await api.del(`/admin/premium/plans/${encodeURIComponent(id)}`);
    await qc.invalidateQueries({ queryKey: ['premium', 'plans'] });
  };

  const edit = (p: Plan) => {
    setDraft({
      id: p.id,
      slug: p.slug,
      title: p.title,
      description: p.description || '',
      price_cents: p.price_cents || 0,
      currency: p.currency || 'USD',
      is_active: p.is_active,
      order: p.order,
      monthly_limits: { ...(p.monthly_limits || {}) },
      features: { ...(p.features || {}) },
    });
  };

  const setStories = (n: string) => {
    const v = Math.max(0, parseInt(n || '0', 10) || 0);
    setDraft((d) => ({
      ...d,
      monthly_limits: { ...(d.monthly_limits || {}), stories: v },
    }));
  };

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-lg font-semibold">Premium — Plans</h1>

      <div className="rounded border p-3">
        <div className="text-sm text-gray-500 mb-2">Создать/изменить тариф</div>
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
            <label className="block text-xs text-gray-500">Title</label>
            <input
              className="w-full rounded border px-2 py-1"
              value={draft.title || ''}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Price (cents)</label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={draft.price_cents || 0}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  price_cents: parseInt(e.target.value || '0', 10),
                })
              }
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Currency</label>
            <input
              className="w-full rounded border px-2 py-1"
              value={draft.currency || 'USD'}
              onChange={(e) => setDraft({ ...draft, currency: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Order</label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={draft.order ?? 100}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  order: parseInt(e.target.value || '100', 10),
                })
              }
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="active"
              type="checkbox"
              checked={!!draft.is_active}
              onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })}
            />
            <label htmlFor="active" className="text-sm">
              Active
            </label>
          </div>
          <div className="md:col-span-3">
            <label className="block text-xs text-gray-500">Description</label>
            <textarea
              className="w-full rounded border px-2 py-1"
              value={draft.description || ''}
              onChange={(e) => setDraft({ ...draft, description: e.target.value })}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Limits: stories/month</label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={Number(draft.monthly_limits?.stories || 0)}
              onChange={(e) => setStories(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500">Limits: AI generations/month</label>
            <input
              className="w-full rounded border px-2 py-1"
              type="number"
              value={Number(draft.monthly_limits?.ai_generations || 0)}
              onChange={(e) => {
                const v = Math.max(0, parseInt(e.target.value || '0', 10) || 0);
                setDraft((d) => ({
                  ...d,
                  monthly_limits: {
                    ...(d.monthly_limits || {}),
                    ai_generations: v,
                  },
                }));
              }}
            />
          </div>
        </div>
        <FormActions
          primaryLabel="Save"
          onPrimary={save}
          secondaryLabel="Reset"
          onSecondary={() =>
            setDraft({
              slug: '',
              title: '',
              is_active: true,
              order: 100,
              currency: 'USD',
              monthly_limits: { stories: 0 },
              features: {},
            })
          }
        />
      </div>

      <ListSection title="Список тарифов" loading={isLoading} error={error}>
        {(() => {
          const columns: Column<Plan>[] = [
            { key: 'slug', title: 'Slug', accessor: (r) => r.slug },
            { key: 'title', title: 'Title', accessor: (r) => r.title },
            {
              key: 'price',
              title: 'Price',
              accessor: (r) => `${(r.price_cents || 0) / 100} ${r.currency || 'USD'}`,
            },
            { key: 'active', title: 'Active', accessor: (r) => (r.is_active ? 'yes' : 'no') },
            {
              key: 'stories',
              title: 'Stories/mo',
              accessor: (r) => String(r.monthly_limits?.stories ?? '-'),
            },
            {
              key: 'actions',
              title: 'Actions',
              render: (r) => (
                <EditDeleteActions onEdit={() => edit(r as Plan)} onDelete={() => remove(r.id)} />
              ),
            },
          ];
          return (
            <DataTable
              columns={columns}
              rows={data}
              rowKey={(r) => r.id}
              emptyText="Нет тарифов"
            />
          );
        })()}
      </ListSection>
    </div>
  );
}

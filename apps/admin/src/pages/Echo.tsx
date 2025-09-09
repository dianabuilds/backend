import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { api } from '../api/client';
import { TraceFilters } from './_shared/TraceFilters';

interface EchoTrace {
  id: string;
  from_slug: string;
  to_slug: string;
  user_id?: string | null;
  source?: string | null;
  channel?: string | null;
  created_at: string;
}

type Filters = {
  from?: string;
  to?: string;
  user_id?: string;
  source?: string;
  channel?: string;
  date_from?: string;
  date_to?: string;
};

async function fetchEcho(page: number, filters: Filters): Promise<EchoTrace[]> {
  const params = new URLSearchParams();
  params.set('page', String(page));
  if (filters.from) params.set('from', filters.from);
  if (filters.to) params.set('to', filters.to);
  if (filters.user_id) params.set('user_id', filters.user_id);
  if (filters.source) params.set('source', filters.source);
  if (filters.channel) params.set('channel', filters.channel);
  if (filters.date_from) params.set('date_from', filters.date_from);
  if (filters.date_to) params.set('date_to', filters.date_to);
  const qs = params.toString() ? `?${params.toString()}` : '';
  const res = await api.get<EchoTrace[]>(`/admin/echo${qs}`);
  return (res.data || []) as EchoTrace[];
}

async function deleteEcho(id: string) {
  await api.del(`/admin/echo/${id}`);
}

async function anonymizeEcho(id: string) {
  await api.post(`/admin/echo/${id}/anonymize`);
}

async function bulkAnonymizeEcho(ids: string[]) {
  await api.post(`/admin/echo/bulk/anonymize`, { ids });
}

async function bulkDeleteEcho(ids: string[]) {
  await api.post(`/admin/echo/bulk/delete`, { ids });
}

async function recomputePopularity(slugs: string[]) {
  await api.post(`/admin/echo/recompute_popularity`, {
    node_slugs: slugs.length ? slugs : undefined,
  });
}

export default function Echo() {
  const [page, setPage] = useState(1);
  const [recomputeInput, setRecomputeInput] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [userId, setUserId] = useState('');
  const [source, setSource] = useState('');
  const [channel, setChannel] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [selected, setSelected] = useState<Record<string, boolean>>({});

  const filters = useMemo<Filters>(
    () => ({
      from: from.trim() || undefined,
      to: to.trim() || undefined,
      user_id: userId.trim() || undefined,
      source: source.trim() || undefined,
      channel: channel.trim() || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [from, to, userId, source, channel, dateFrom, dateTo],
  );

  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['echo', page, filters],
    queryFn: () => fetchEcho(page, filters),
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['echo'] });

  const handleDelete = async (id: string) => {
    await deleteEcho(id);
    await refresh();
  };

  const handleAnon = async (id: string) => {
    await anonymizeEcho(id);
    await refresh();
  };

  const handleRecompute = async () => {
    const slugs = recomputeInput
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
    await recomputePopularity(slugs);
    setRecomputeInput('');
  };

  const idsSelected = useMemo(() => Object.keys(selected).filter((k) => selected[k]), [selected]);
  const allChecked = useMemo(() => {
    const items = data || [];
    return items.length > 0 && items.every((t) => selected[t.id]);
  }, [data, selected]);

  const toggleAll = () => {
    const items = data || [];
    const next: Record<string, boolean> = {};
    const value = !allChecked;
    for (const t of items) next[t.id] = value;
    setSelected(next);
  };

  const clearSelection = () => setSelected({});

  const handleBulkAnon = async () => {
    if (idsSelected.length === 0) return;
    await bulkAnonymizeEcho(idsSelected);
    clearSelection();
    await refresh();
  };

  const handleBulkDelete = async () => {
    if (idsSelected.length === 0) return;
    await bulkDeleteEcho(idsSelected);
    clearSelection();
    await refresh();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Эхо‑трейсы</h1>

      <TraceFilters
        values={{ from, to, userId, source, channel, dateFrom, dateTo }}
        onChange={(patch) => {
          if (patch.from !== undefined) setFrom(patch.from);
          if (patch.to !== undefined) setTo(patch.to);
          if (patch.userId !== undefined) setUserId(patch.userId);
          if (patch.source !== undefined) setSource(patch.source);
          if (patch.channel !== undefined) setChannel(patch.channel);
          if (patch.dateFrom !== undefined) setDateFrom(patch.dateFrom);
          if (patch.dateTo !== undefined) setDateTo(patch.dateTo);
        }}
      />

      <div className="mb-4 flex items-center gap-2">
        <input
          type="text"
          placeholder="slug нод (через запятую)"
          value={recomputeInput}
          onChange={(e) => setRecomputeInput(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <button onClick={handleRecompute} className="px-3 py-1 bg-blue-600 text-white rounded">
          Пересчитать популярность
        </button>
        <div className="ml-auto flex gap-2">
          <button onClick={handleBulkAnon} className="px-3 py-1 rounded border">
            Массовая анонимизация
          </button>
          <button onClick={handleBulkDelete} className="px-3 py-1 rounded border text-red-600">
            Массовое удаление
          </button>
        </div>
      </div>

      {isLoading && <p>Загрузка...</p>}
      {error && <p className="text-red-500">Ошибка загрузки трассировок</p>}
      {!isLoading && !error && (
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="border-b">
              <th className="p-2">
                <input type="checkbox" checked={allChecked} onChange={toggleAll} />
              </th>
              <th className="p-2">Откуда</th>
              <th className="p-2">Куда</th>
              <th className="p-2">Пользователь</th>
              <th className="p-2">Источник</th>
              <th className="p-2">Канал</th>
              <th className="p-2">Создано</th>
              <th className="p-2">Действия</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((t) => (
              <tr key={t.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="p-2">
                  <input
                    type="checkbox"
                    checked={selected[t.id]}
                    onChange={(e) => setSelected((s) => ({ ...s, [t.id]: e.target.checked }))}
                  />
                </td>
                <td className="p-2">{t.from_slug}</td>
                <td className="p-2">{t.to_slug}</td>
                <td className="p-2">{t.user_id ?? 'анон'}</td>
                <td className="p-2">{t.source ?? ''}</td>
                <td className="p-2">{t.channel ?? ''}</td>
                <td className="p-2">{new Date(t.created_at).toLocaleString()}</td>
                <td className="p-2 space-x-2">
                  <button onClick={() => handleAnon(t.id)} className="text-blue-600">
                    Анонимизировать
                  </button>
                  <button onClick={() => handleDelete(t.id)} className="text-red-600">
                    Удалить
                  </button>
                </td>
              </tr>
            ))}
            {(data?.length || 0) === 0 && (
              <tr>
                <td colSpan={8} className="p-4 text-center text-gray-500">
                  Эхо‑трейсы не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
      <div className="mt-4 flex gap-2 items-center">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="px-3 py-1 border rounded"
        >
          Назад
        </button>
        <span>Страница {page}</span>
        <button onClick={() => setPage((p) => p + 1)} className="px-3 py-1 border rounded">
          Вперед
        </button>
        <button onClick={clearSelection} className="ml-auto px-3 py-1 border rounded">
          Сбросить выбор
        </button>
      </div>
    </div>
  );
}

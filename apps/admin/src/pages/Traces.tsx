import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';

import { api } from '../api/client';
import PeriodStepSelector from '../components/PeriodStepSelector';
import { TraceFilters } from './_shared/TraceFilters';

interface TraceItem {
  id: string;
  from_slug?: string;
  to_slug?: string;
  user_id?: string | null;
  source?: string | null;
  channel?: string | null;
  type?: string | null;
  created_at?: string;
  latency_ms?: number | null;
  request_id?: string | null;
}

type Filters = {
  from?: string;
  to?: string;
  user_id?: string;
  source?: string;
  channel?: string;
  type?: string;
  date_from?: string;
  date_to?: string;
};

async function fetchTraces(page: number, filters: Filters): Promise<TraceItem[]> {
  const params = new URLSearchParams();
  params.set('page', String(page));
  if (filters.from) params.set('from', filters.from);
  if (filters.to) params.set('to', filters.to);
  if (filters.user_id) params.set('user_id', filters.user_id);
  if (filters.source) params.set('source', filters.source);
  if (filters.channel) params.set('channel', filters.channel);
  if (filters.type) params.set('type', filters.type);
  if (filters.date_from) params.set('date_from', filters.date_from);
  if (filters.date_to) params.set('date_to', filters.date_to);
  const qs = params.toString() ? `?${params.toString()}` : '';
  const res = await api.get<TraceItem[]>(`/admin/traces${qs}`);
  return (res.data || []) as TraceItem[];
}

async function anonymizeTrace(id: string) {
  await api.post(`/admin/traces/${id}/anonymize`);
}
async function deleteTrace(id: string) {
  await api.del(`/admin/traces/${id}`);
}
async function bulkAnonymize(ids: string[]) {
  await api.post(`/admin/traces/bulk/anonymize`, { ids });
}
async function bulkDelete(ids: string[]) {
  await api.post(`/admin/traces/bulk/delete`, { ids });
}

export default function Traces() {
  const [page, setPage] = useState(1);
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [userId, setUserId] = useState('');
  const [source, setSource] = useState('');
  const [channel, setChannel] = useState('');
  const [type, setType] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [range, setRange] = useState<'1h' | '24h'>('1h');
  const [step, setStep] = useState<60 | 300>(60);

  const filters = useMemo<Filters>(
    () => ({
      from: from.trim() || undefined,
      to: to.trim() || undefined,
      user_id: userId.trim() || undefined,
      source: source.trim() || undefined,
      channel: channel.trim() || undefined,
      type: type.trim() || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [from, to, userId, source, channel, type, dateFrom, dateTo],
  );

  useEffect(() => {
    setPage(1);
  }, [from, to, userId, source, channel, type, dateFrom, dateTo]);

  const queryClient = useQueryClient();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['traces', page, filters],
    queryFn: () => fetchTraces(page, filters),
    retry: false,
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ['traces'] });

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
    await bulkAnonymize(idsSelected);
    clearSelection();
    await refresh();
  };
  const handleBulkDelete = async () => {
    if (idsSelected.length === 0) return;
    await bulkDelete(idsSelected);
    clearSelection();
    await refresh();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Трассировки</h1>
      <PeriodStepSelector
        range={range}
        step={step}
        onRangeChange={setRange}
        onStepChange={setStep}
        className="mb-2"
      />
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
        Поиск и просмотр трасс переходов. Используйте фильтры для уточнения результатов.
      </p>

      <TraceFilters
        values={{ from, to, userId, source, channel, type, dateFrom, dateTo }}
        onChange={(patch) => {
          if (patch.from !== undefined) setFrom(patch.from);
          if (patch.to !== undefined) setTo(patch.to);
          if (patch.userId !== undefined) setUserId(patch.userId);
          if (patch.source !== undefined) setSource(patch.source);
          if (patch.channel !== undefined) setChannel(patch.channel);
          if (patch.type !== undefined) setType(patch.type);
          if (patch.dateFrom !== undefined) setDateFrom(patch.dateFrom);
          if (patch.dateTo !== undefined) setDateTo(patch.dateTo);
        }}
        showType
      />

      <div className="mb-3 flex items-center gap-2">
        <button onClick={handleBulkAnon} className="px-3 py-1 rounded border">
          Массовая анонимизация
        </button>
        <button onClick={handleBulkDelete} className="px-3 py-1 rounded border text-red-600">
          Массовое удаление
        </button>
      </div>

      {isLoading && <p>Загрузка...</p>}
      {error && (
        <div className="text-red-500">
          {(() => {
            const err = error as unknown as { response?: { data?: { detail?: string } } };
            return (
              err?.response?.data?.detail ||
              (error instanceof Error ? error.message : String(error))
            );
          })()}
          <button onClick={() => refetch()} className="ml-2 underline">
            Повторить
          </button>
        </div>
      )}
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
              <th className="p-2">Тип</th>
              <th className="p-2">Источник</th>
              <th className="p-2">Канал</th>
              <th className="p-2">Задержка</th>
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
                    checked={!!selected[t.id]}
                    onChange={(e) => setSelected((s) => ({ ...s, [t.id]: e.target.checked }))}
                  />
                </td>
                <td className="p-2">{t.from_slug ?? '-'}</td>
                <td className="p-2">{t.to_slug ?? '-'}</td>
                <td className="p-2">{t.user_id ?? 'анон'}</td>
                <td className="p-2">{t.type ?? '-'}</td>
                <td className="p-2">{t.source ?? '-'}</td>
                <td className="p-2">{t.channel ?? '-'}</td>
                <td className="p-2">{t.latency_ms != null ? `${t.latency_ms} ms` : '-'}</td>
                <td className="p-2">
                  {t.created_at ? new Date(t.created_at).toLocaleString() : '-'}
                </td>
                <td className="p-2 space-x-2">
                  <button
                    onClick={async () => {
                      await anonymizeTrace(t.id);
                      refresh();
                    }}
                    className="text-blue-600"
                  >
                    Анонимизировать
                  </button>
                  <button
                    onClick={async () => {
                      await deleteTrace(t.id);
                      refresh();
                    }}
                    className="text-red-600"
                  >
                    Удалить
                  </button>
                </td>
              </tr>
            ))}
            {(data?.length || 0) === 0 && (
              <tr>
                <td colSpan={10} className="p-4 text-center text-gray-500">
                  Трассировки не найдены
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

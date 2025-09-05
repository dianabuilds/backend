import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { LineChart, StackedBars } from '../../components/Charts';
import JsonCard from '../../components/JsonCard';
import PeriodStepSelector from '../../components/PeriodStepSelector';
import SummaryCard from '../../components/SummaryCard';
import { AdminTelemetryService } from '../../openapi';

export type RumEvent = {
  event: string;
  ts?: number;
  url?: string;
  data?: { dur_ms?: number } & Record<string, unknown>;
};
type RumSummary = {
  window: number;
  counts: Record<string, number>;
  login_attempt_avg_ms: number | null;
  navigation_avg: {
    ttfb_ms: number | null;
    dom_content_loaded_ms: number | null;
    load_event_ms: number | null;
  };
};

export default function RumTab() {
  const qc = useQueryClient();
  const [range, setRange] = useState<'1h' | '24h'>('1h');
  const [step, setStep] = useState<60 | 300>(60);
  const [eventFilter, setEventFilter] = useState('');
  const [urlFilter, setUrlFilter] = useState('');
  const [page, setPage] = useState(0);
  const pageSize = 50;

  const windowSize = useMemo(() => {
    const rangeSec = range === '1h' ? 3600 : 86_400;
    return rangeSec / step;
  }, [range, step]);

  const {
    data: summary,
    isFetching: sFetching,
    error: sError,
  } = useQuery({
    queryKey: ['telemetry', 'summary', range, step],
    queryFn: async () =>
      (await AdminTelemetryService.rumSummaryAdminTelemetryRumSummaryGet({ window: windowSize })) as RumSummary,
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
    staleTime: 2000,
  });

  const {
    data: events,
    isFetching: eFetching,
    error: eError,
  } = useQuery({
    queryKey: ['telemetry', 'events', range, step, eventFilter, urlFilter, page],
    queryFn: async () =>
      ((await AdminTelemetryService.listRumEventsAdminTelemetryRumGet(
        eventFilter || undefined,
        urlFilter || undefined,
        page * pageSize,
        pageSize,
      )) as RumEvent[]) || [],
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
    staleTime: 2000,
  });
  const counts = summary?.counts || {};

  const buckets = useMemo(() => {
    const res = new Map<number, { count: number; loginDur: number; loginCount: number }>();
    const now = Date.now();
    const rangeMs = range === '1h' ? 3600_000 : 86_400_000;
    const from = now - rangeMs;
    (events || []).forEach((ev) => {
      if (!ev.ts || ev.ts < from) return;
      const bucket = Math.floor(ev.ts / (step * 1000)) * step * 1000;
      const entry = res.get(bucket) || { count: 0, loginDur: 0, loginCount: 0 };
      entry.count++;
      if (ev.event === 'login_attempt' && typeof ev.data?.dur_ms === 'number') {
        entry.loginDur += ev.data.dur_ms;
        entry.loginCount++;
      }
      res.set(bucket, entry);
    });
    return res;
  }, [events, range, step]);

  const barSeries = useMemo(() => {
    const points = Array.from(buckets.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([ts, v]) => ({ ts, value: v.count }));
    return [{ points }];
  }, [buckets]);

  const linePoints = useMemo(() => {
    return Array.from(buckets.entries())
      .sort((a, b) => a[0] - b[0])
      .map(([ts, v]) => ({ ts, value: v.loginCount ? v.loginDur / v.loginCount : 0 }));
  }, [buckets]);

  const barHighlight = useMemo(() => {
    const vals = barSeries[0]?.points.map((p) => p.value) || [];
    const avg = vals.reduce((a, b) => a + b, 0) / (vals.length || 1);
    return vals.map((v) => v > avg * 1.5);
  }, [barSeries]);

  const lineHighlight = useMemo(() => {
    const vals = linePoints.map((p) => p.value);
    const avg = vals.reduce((a, b) => a + b, 0) / (vals.length || 1);
    return vals.map((v) => v > avg * 1.5);
  }, [linePoints]);

  const reload = async () => {
    await Promise.all([
      qc.invalidateQueries({ queryKey: ['telemetry', 'summary', range, step] }),
      qc.invalidateQueries({ queryKey: ['telemetry', 'events', range, step] }),
    ]);
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-lg font-semibold">Telemetry — RUM</h1>
        <div className="flex flex-wrap items-center gap-2">
          <PeriodStepSelector
            range={range}
            step={step}
            onRangeChange={setRange}
            onStepChange={setStep}
          />
          <button
            onClick={reload}
            className="text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200"
          >
            Обновить
          </button>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <input
          value={eventFilter}
          onChange={(e) => {
            setEventFilter(e.target.value);
            setPage(0);
          }}
          placeholder="event"
          className="w-40 text-sm px-2 py-1 border rounded"
        />
        <input
          value={urlFilter}
          onChange={(e) => {
            setUrlFilter(e.target.value);
            setPage(0);
          }}
          placeholder="url"
          className="w-40 text-sm px-2 py-1 border rounded"
        />
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Real user monitoring events. Use range and step to adjust aggregation.
      </p>

      <section className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Events</h2>
        </div>
        <div className="flex items-end gap-4">
          <StackedBars series={barSeries} highlight={barHighlight} />
          <div>
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Login avg (ms)</div>
            <LineChart points={linePoints} highlight={lineHighlight} />
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          {sFetching && <div className="text-xs text-gray-500 mt-1">Загрузка…</div>}
          {sError && (
            <div className="mt-1 text-xs text-red-600">
              Ошибка: {sError instanceof Error ? sError.message : String(sError)}
            </div>
          )}
          {summary && (
            <SummaryCard
              title="Сводка"
              items={[
                {
                  label: 'Окно',
                  value: summary.window,
                },
                {
                  label: 'Login avg',
                  value: `${summary.login_attempt_avg_ms ?? '-'} ms`,
                  highlight: (summary.login_attempt_avg_ms ?? 0) > 1000,
                },
                {
                  label: 'TTFB avg',
                  value: `${summary.navigation_avg.ttfb_ms ?? '-'} ms`,
                  highlight: (summary.navigation_avg.ttfb_ms ?? 0) > 1000,
                },
                {
                  label: 'DCL avg',
                  value: `${summary.navigation_avg.dom_content_loaded_ms ?? '-'} ms`,
                  highlight: (summary.navigation_avg.dom_content_loaded_ms ?? 0) > 1000,
                },
                {
                  label: 'Load avg',
                  value: `${summary.navigation_avg.load_event_ms ?? '-'} ms`,
                  highlight: (summary.navigation_avg.load_event_ms ?? 0) > 1000,
                },
                ...Object.entries(counts).map(([k, v]) => ({
                  label: k,
                  value: v,
                  highlight: k.includes('error') && v > 0,
                })),
              ]}
            />
          )}
        </div>

        <div className="md:col-span-2 rounded border p-3 bg-white shadow-sm dark:bg-gray-900">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500 dark:text-gray-400">Лента событий</div>
            {eFetching || sFetching ? (
              <div className="text-xs text-gray-500">Обновление…</div>
            ) : null}
          </div>
          {eError ? (
            <div className="mt-1 text-xs text-red-600">
              Ошибка: {eError instanceof Error ? eError.message : String(eError)}
            </div>
          ) : null}
          <div className="mt-2 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="px-2 py-1">Time</th>
                  <th className="px-2 py-1">Event</th>
                  <th className="px-2 py-1">URL</th>
                  <th className="px-2 py-1">Payload</th>
                </tr>
              </thead>
              <tbody>
                {(events || []).map((ev, idx) => (
                  <tr key={idx} className="border-t">
                    <td className="px-2 py-1">
                      {ev.ts ? new Date(ev.ts).toLocaleTimeString() : '-'}
                    </td>
                    <td className="px-2 py-1">{ev.event}</td>
                    <td className="px-2 py-1">{ev.url || '-'}</td>
                    <td className="px-2 py-1">
                      <JsonCard data={ev.data ?? {}} />
                    </td>
                  </tr>
                ))}
                {(events || []).length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-2 py-3 text-sm text-gray-500">
                      Пока нет событий
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
          <div className="mt-2 flex justify-end gap-2">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="text-sm px-2 py-1 border rounded disabled:opacity-50"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              className="text-sm px-2 py-1 border rounded"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

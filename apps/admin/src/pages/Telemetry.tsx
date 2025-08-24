import { useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../api/client";

type RumEvent = { event: string; ts?: number; url?: string; data?: any };
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

export default function Telemetry() {
  const qc = useQueryClient();

  const {
    data: summary,
    isFetching: sFetching,
    error: sError,
  } = useQuery({
    queryKey: ["telemetry", "summary"],
    queryFn: async () =>
      (await api.get<RumSummary>("/admin/telemetry/rum/summary")).data!,
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
    staleTime: 2000,
  });

  const {
    data: events,
    isFetching: eFetching,
    error: eError,
  } = useQuery({
    queryKey: ["telemetry", "events"],
    queryFn: async () =>
      (await api.get<RumEvent[]>("/admin/telemetry/rum?limit=200")).data || [],
    refetchInterval: 5000,
    refetchOnWindowFocus: true,
    staleTime: 2000,
  });

  const counts = summary?.counts || {};

  const reload = async () => {
    await Promise.all([
      qc.invalidateQueries({ queryKey: ["telemetry", "summary"] }),
      qc.invalidateQueries({ queryKey: ["telemetry", "events"] }),
    ]);
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2">
        <h1 className="text-lg font-semibold">Telemetry — RUM</h1>
        <button
          onClick={reload}
          className="ml-auto text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200"
        >
          Обновить
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded border p-3">
          <div className="text-sm text-gray-500">Сводка</div>
          {sFetching ? (
            <div className="text-xs text-gray-500 mt-1">Загрузка…</div>
          ) : null}
          {sError ? (
            <div className="text-xs text-red-600 mt-1">
              Ошибка: {(sError as any)?.message}
            </div>
          ) : null}
          {summary ? (
            <div className="text-sm mt-2 space-y-1">
              <div>Окно: {summary.window} событий</div>
              <div>Login avg: {summary.login_attempt_avg_ms ?? "-"} ms</div>
              <div>TTFB avg: {summary.navigation_avg.ttfb_ms ?? "-"} ms</div>
              <div>
                DCL avg: {summary.navigation_avg.dom_content_loaded_ms ?? "-"}{" "}
                ms
              </div>
              <div>
                Load avg: {summary.navigation_avg.load_event_ms ?? "-"} ms
              </div>
              <div className="mt-2">
                <div className="text-gray-500">Счётчики по событиям</div>
                <ul className="list-disc pl-5">
                  {Object.keys(counts).length === 0 ? (
                    <li className="text-gray-500">нет данных</li>
                  ) : null}
                  {Object.entries(counts).map(([k, v]) => (
                    <li key={k}>
                      {k}: {v}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ) : null}
        </div>

        <div className="md:col-span-2 rounded border p-3">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">Лента событий</div>
            {eFetching || sFetching ? (
              <div className="text-xs text-gray-500">Обновление…</div>
            ) : null}
          </div>
          {eError ? (
            <div className="text-xs text-red-600 mt-1">
              Ошибка: {(eError as any)?.message}
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
                      {ev.ts ? new Date(ev.ts).toLocaleTimeString() : "-"}
                    </td>
                    <td className="px-2 py-1">{ev.event}</td>
                    <td className="px-2 py-1">{ev.url || "-"}</td>
                    <td className="px-2 py-1">
                      <details>
                        <summary className="text-blue-600 cursor-pointer hover:underline">
                          Показать
                        </summary>
                        <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap text-xs bg-gray-50 p-2 rounded">
                          {JSON.stringify(ev.data ?? {}, null, 2)}
                        </pre>
                      </details>
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
        </div>
      </div>
    </div>
  );
}

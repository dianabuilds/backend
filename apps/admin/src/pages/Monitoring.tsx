import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import {
  getTimeseries,
  getTopEndpoints,
  type TimeseriesResponse,
  type TopEndpointItem,
} from "../api/metrics";

/**
 * Простой столбчатый mini-chart без внешних зависимостей.
 */
function StackedBars({
  series,
  height = 80,
}: {
  series: TimeseriesResponse["series"];
  height?: number;
}) {
  const buckets =
    series[0]?.points.map((p, i) => {
      const sum = series.reduce((acc, s) => acc + (s.points[i]?.value || 0), 0);
      return { ts: p.ts, sum };
    }) || [];
  const max = Math.max(1, ...buckets.map((b) => b.sum));
  return (
    <div className="flex items-end gap-[2px] h-[100px]" style={{ height }}>
      {buckets.map((b, i) => {
        const totals = series.map((s) => s.points[i]?.value || 0);
        const heights = totals.map((v) => Math.round((v / max) * height));
        // Цвета по классам: 2xx зелёный, 4xx оранжевый, 5xx красный
        const colors = ["#10b981", "#f59e0b", "#ef4444"];
        return (
          <div key={b.ts} className="w-[6px] flex flex-col justify-end">
            {heights.map((h, j) => (
              <div key={j} style={{ height: h, backgroundColor: colors[j] }} />
            ))}
          </div>
        );
      })}
    </div>
  );
}

function LineChart({
  points,
  height = 80,
}: {
  points: { ts: number; value: number }[];
  height?: number;
}) {
  const max = Math.max(1, ...points.map((p) => p.value));
  const path = useMemo(() => {
    if (points.length === 0) return "";
    return points
      .map((p, i) => {
        const x = i * 8 + 4;
        const y = height - Math.round((p.value / max) * height);
        return `${i === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");
  }, [points, height]);
  const width = points.length * 8 + 4;
  return (
    <svg width={width} height={height}>
      <path d={path} fill="none" stroke="#3b82f6" strokeWidth="2" />
    </svg>
  );
}

export default function Monitoring() {
  const [range, setRange] = useState<"1h" | "24h">("1h");
  const [step, setStep] = useState<60 | 300>(60);
  const [by, setBy] = useState<"p95" | "error_rate" | "rps">("p95");

  const {
    data: tsData,
    isLoading: tsLoading,
    error: tsError,
    refetch: refetchTs,
  } = useQuery({
    queryKey: ["metrics-timeseries", range, step],
    queryFn: () => getTimeseries(range, step),
    refetchInterval: 15000,
  });

  const {
    data: top,
    isLoading: topLoading,
    error: topError,
    refetch: refetchTop,
  } = useQuery({
    queryKey: ["metrics-top", range, by],
    queryFn: () => getTopEndpoints(range, by, 20),
    refetchInterval: 30000,
  });

  const legend = (
    <div className="flex items-center gap-4 text-sm">
      <span className="inline-flex items-center gap-1">
        <span
          className="w-3 h-3 inline-block rounded-sm"
          style={{ background: "#10b981" }}
        />
        2xx
      </span>
      <span className="inline-flex items-center gap-1">
        <span
          className="w-3 h-3 inline-block rounded-sm"
          style={{ background: "#f59e0b" }}
        />
        4xx
      </span>
      <span className="inline-flex items-center gap-1">
        <span
          className="w-3 h-3 inline-block rounded-sm"
          style={{ background: "#ef4444" }}
        />
        5xx
      </span>
      <span className="inline-flex items-center gap-1">
        <span
          className="w-3 h-3 inline-block rounded-sm"
          style={{ background: "#3b82f6" }}
        />
        p95
      </span>
    </div>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Monitoring</h1>
      <div className="flex items-center gap-2">
        <label className="text-sm">Range:</label>
        <select
          value={range}
          onChange={(e) => setRange(e.target.value as any)}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value="1h">1h</option>
          <option value="24h">24h</option>
        </select>
        <label className="text-sm">Step:</label>
        <select
          value={step}
          onChange={(e) => setStep(Number(e.target.value) as any)}
          className="border rounded px-2 py-1 text-sm"
        >
          <option value={60}>1m</option>
          <option value={300}>5m</option>
        </select>
        <button
          className="text-sm rounded border px-2 py-1"
          onClick={() => {
            refetchTs();
            refetchTop();
          }}
        >
          Refresh
        </button>
      </div>

      <section className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Requests</h2>
          {legend}
        </div>
        {tsLoading && (
          <p className="text-gray-600 dark:text-gray-400">
            Loading timeseries…
          </p>
        )}
        {tsError && (
          <p className="text-red-600">{(tsError as Error).message}</p>
        )}
        {tsData && (
          <div className="flex items-end gap-4">
            <StackedBars series={tsData.series} />
            <div>
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                p95 latency
              </div>
              <LineChart points={tsData.p95} />
            </div>
          </div>
        )}
      </section>

      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Top endpoints</h2>
          <div className="flex items-center gap-2">
            <label className="text-sm">By:</label>
            <select
              value={by}
              onChange={(e) => setBy(e.target.value as any)}
              className="border rounded px-2 py-1 text-sm"
            >
              <option value="p95">p95</option>
              <option value="error_rate">error rate</option>
              <option value="rps">rps</option>
            </select>
          </div>
        </div>
        {topLoading && (
          <p className="text-gray-600 dark:text-gray-400">Loading top…</p>
        )}
        {topError && (
          <p className="text-red-600">{(topError as Error).message}</p>
        )}
        {top && (
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="p-2 text-left">Route</th>
                <th className="p-2 text-left">RPS</th>
                <th className="p-2 text-left">Error rate</th>
                <th className="p-2 text-left">p95 (ms)</th>
                <th className="p-2 text-left">Count</th>
              </tr>
            </thead>
            <tbody>
              {top.map((r: TopEndpointItem) => (
                <tr key={r.route} className="border-b">
                  <td className="p-2 font-mono">{r.route}</td>
                  <td className="p-2">{r.rps.toFixed(2)}</td>
                  <td className="p-2">{(r.error_rate * 100).toFixed(2)}%</td>
                  <td className="p-2">{Math.round(r.p95)}</td>
                  <td className="p-2">{r.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

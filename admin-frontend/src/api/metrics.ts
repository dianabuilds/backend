import { api } from "./client";

export interface MetricsSummary {
  rps: number;
  error_rate: number;
  p95_latency: number;
  count_429: number;
}

export interface TimeseriesPoint {
  ts: number;
  value: number;
}
export interface TimeseriesSeries {
  name: string;
  points: TimeseriesPoint[];
}
export interface TimeseriesResponse {
  step: number;
  from: number;
  to: number;
  series: TimeseriesSeries[]; // status classes
  p95: TimeseriesPoint[];
}

export interface TopEndpointItem {
  route: string;
  p95: number;
  error_rate: number;
  rps: number;
  count: number;
}

export async function getMetricsSummary(range: "1h" | "24h" = "1h") {
  const res = await api.get<MetricsSummary>(`/admin/metrics/summary?range=${encodeURIComponent(range)}`);
  return res.data as MetricsSummary;
}

export async function getTimeseries(range: "1h" | "24h" = "1h", step: 60 | 300 = 60) {
  const res = await api.get<TimeseriesResponse>(`/admin/metrics/timeseries?range=${encodeURIComponent(range)}&step=${step}`);
  return res.data as TimeseriesResponse;
}

export async function getTopEndpoints(range: "1h" | "24h" = "1h", by: "p95" | "error_rate" | "rps" = "p95", limit = 20) {
  const res = await api.get<{ items: TopEndpointItem[] }>(`/admin/metrics/endpoints/top?range=${encodeURIComponent(range)}&by=${by}&limit=${limit}`);
  return (res.data?.items || []) as TopEndpointItem[];
}

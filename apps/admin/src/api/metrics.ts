import type { MetricsSummary } from "../openapi";
import { api } from "./client";
import type { ListResponse } from "./types";

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

export async function getMetricsSummary(
  range: "1h" | "24h" = "1h",
): Promise<MetricsSummary> {
  const res = await api.get<MetricsSummary>(
    `/admin/metrics/summary?range=${encodeURIComponent(range)}`,
  );
  return res.data!;
}

export async function getTimeseries(
  range: "1h" | "24h" = "1h",
  step: 60 | 300 = 60,
): Promise<TimeseriesResponse> {
  const res = await api.get<TimeseriesResponse>(
    `/admin/metrics/timeseries?range=${encodeURIComponent(range)}&step=${step}`,
  );
  return res.data!;
}

export async function getTopEndpoints(
  range: "1h" | "24h" = "1h",
  by: "p95" | "error_rate" | "rps" = "p95",
  limit = 20,
): Promise<TopEndpointItem[]> {
  const res = await api.get<ListResponse<TopEndpointItem>>(
    `/admin/metrics/endpoints/top?range=${encodeURIComponent(range)}&by=${by}&limit=${limit}`,
  );
  return res.data?.items ?? [];
}

export interface TransitionMetrics {
  route_length_avg: number;
  route_length_p95: number;
  tag_entropy_avg: number;
  no_route_percent: number;
  fallback_used_percent: number;
}

export type TransitionStats = Record<string, TransitionMetrics>;

export async function getTransitionStats(): Promise<TransitionStats> {
  const res = await api.get<{ stats: TransitionStats }>(
    "/admin/metrics/transitions"
  );
  return res.data?.stats || {};
}

export interface EventCounters {
  [workspace: string]: Record<string, number>;
}

export async function getEventCounters(): Promise<EventCounters> {
  const res = await api.get<{ counters: EventCounters }>(
    "/admin/metrics/events",
  );
  return res.data?.counters || {};
}

export interface ReliabilityMetrics {
  rps: number;
  p95: number;
  errors_4xx: number;
  errors_5xx: number;
  no_route_percent: number;
  fallback_percent: number;
}

export async function getReliabilityMetrics(
  workspace?: string,
): Promise<ReliabilityMetrics> {
  const params = new URLSearchParams();
  if (workspace) params.append("workspace", workspace);
  const qs = params.toString();
  const res = await api.get<ReliabilityMetrics>(
    `/admin/metrics/reliability${qs ? `?${qs}` : ""}`,
  );
  return (
    res.data || {
      rps: 0,
      p95: 0,
      errors_4xx: 0,
      errors_5xx: 0,
      no_route_percent: 0,
      fallback_percent: 0,
    }
  );
}

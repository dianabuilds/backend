import { apiGet } from '../../shared/api/client';
import {
  EventsSummary,
  HttpSummary,
  LLMSummary,
  RumEventRow,
  RumSummary,
  TelemetryOverview,
  TransitionModeSummary,
  WorkersSummary,
} from './types';

export function fetchTelemetryOverview(signal?: AbortSignal) {
  return apiGet<TelemetryOverview>('/v1/admin/telemetry/summary', { signal });
}

export function fetchHttpSummary(signal?: AbortSignal) {
  return apiGet<HttpSummary>('/v1/admin/telemetry/http/summary', { signal });
}

export function fetchLLMSummary(signal?: AbortSignal) {
  return apiGet<LLMSummary>('/v1/admin/telemetry/llm/summary', { signal });
}

export function fetchWorkerSummary(signal?: AbortSignal) {
  return apiGet<WorkersSummary>('/v1/admin/telemetry/workers/summary', { signal });
}

export function fetchEventsSummary(signal?: AbortSignal) {
  return apiGet<EventsSummary>('/v1/admin/telemetry/events/summary', { signal });
}

export function fetchTransitionsSummary(signal?: AbortSignal) {
  return apiGet<TransitionModeSummary[]>('/v1/admin/telemetry/transitions/summary', { signal });
}

export function fetchRumSummary(signal?: AbortSignal, window = 500) {
  const params = new URLSearchParams({ window: String(window) });
  return apiGet<RumSummary>(`/v1/admin/telemetry/rum/summary?${params.toString()}`, { signal });
}

type RumEventsParams = {
  event?: string | null;
  url?: string | null;
  offset?: number;
  limit?: number;
};

export function fetchRumEvents({ event, url, offset = 0, limit = 100 }: RumEventsParams = {}, signal?: AbortSignal) {
  const params = new URLSearchParams();
  if (event) params.set('event', event);
  if (url) params.set('url', url);
  if (offset) params.set('offset', String(offset));
  if (limit) params.set('limit', String(limit));
  const suffix = params.toString();
  const path = suffix ? `/v1/admin/telemetry/rum?${suffix}` : '/v1/admin/telemetry/rum';
  return apiGet<RumEventRow[]>(path, { signal });
}

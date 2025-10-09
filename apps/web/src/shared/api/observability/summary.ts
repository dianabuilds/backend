import { apiGet } from '../client';
import type {
  EventHandlerRow,
  EventsSummary,
  HttpPathStats,
  HttpSummary,
  LLMCostMetric,
  LLMCallMetric,
  LLMLatencyMetric,
  LLMSummary,
  LLMTokensMetric,
  RumEventRow,
  RumSummary,
  TelemetryOverview,
  TransitionModeSummary,
  WorkersSummary,
} from '../../types/observability';
import {
  ensureArray,
  isObjectRecord,
  pickNumber,
  pickString,
} from './utils';

type RequestOptions = {
  signal?: AbortSignal;
};

type RumSummaryOptions = RequestOptions & {
  window?: number;
};

type RumEventsOptions = RequestOptions & {
  event?: string | null;
  url?: string | null;
  offset?: number;
  limit?: number;
};

const TELEMETRY_OVERVIEW_ENDPOINT = '/v1/admin/telemetry/summary';
const TELEMETRY_HTTP_ENDPOINT = '/v1/admin/telemetry/http/summary';
const TELEMETRY_LLM_ENDPOINT = '/v1/admin/telemetry/llm/summary';
const TELEMETRY_WORKERS_ENDPOINT = '/v1/admin/telemetry/workers/summary';
const TELEMETRY_EVENTS_ENDPOINT = '/v1/admin/telemetry/events/summary';
const TELEMETRY_TRANSITIONS_ENDPOINT = '/v1/admin/telemetry/transitions/summary';
const TELEMETRY_RUM_SUMMARY_ENDPOINT = '/v1/admin/telemetry/rum/summary';
const TELEMETRY_RUM_EVENTS_ENDPOINT = '/v1/admin/telemetry/rum';

function normalizeHttpPathStats(value: unknown): HttpPathStats | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const method = pickString(value.method);
  const path = pickString(value.path);
  if (!method || !path) {
    return null;
  }
  return {
    method,
    path,
    requests_total: pickNumber(value.requests_total) ?? 0,
    error5xx_total: pickNumber(value.error5xx_total) ?? undefined,
    error5xx_ratio: pickNumber(value.error5xx_ratio) ?? 0,
    avg_duration_ms: pickNumber(value.avg_duration_ms) ?? 0,
  };
}

function normalizeHttpSummary(value: unknown): HttpSummary {
  if (!isObjectRecord(value)) {
    return { paths: [] };
  }
  return {
    paths: ensureArray(value.paths, normalizeHttpPathStats),
  };
}

function normalizeLLMCallMetric(value: unknown): LLMCallMetric | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const type = pickString(value.type);
  const provider = pickString(value.provider);
  const model = pickString(value.model);
  const stage = pickString(value.stage) ?? '';
  if (!type || !provider || !model) {
    return null;
  }
  return {
    type,
    provider,
    model,
    stage,
    count: pickNumber(value.count) ?? 0,
  };
}

function normalizeLLMLatencyMetric(value: unknown): LLMLatencyMetric | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const provider = pickString(value.provider);
  const model = pickString(value.model);
  const stage = pickString(value.stage) ?? '';
  if (!provider || !model) {
    return null;
  }
  return {
    provider,
    model,
    stage,
    avg_ms: pickNumber(value.avg_ms) ?? 0,
  };
}

function normalizeLLMTokensMetric(value: unknown): LLMTokensMetric | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const provider = pickString(value.provider);
  const model = pickString(value.model);
  const stage = pickString(value.stage) ?? '';
  const type = pickString(value.type) ?? 'prompt';
  if (!provider || !model) {
    return null;
  }
  return {
    provider,
    model,
    stage,
    type,
    total: pickNumber(value.total) ?? 0,
  };
}

function normalizeLLMCostMetric(value: unknown): LLMCostMetric | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const provider = pickString(value.provider);
  const model = pickString(value.model);
  const stage = pickString(value.stage) ?? '';
  if (!provider || !model) {
    return null;
  }
  return {
    provider,
    model,
    stage,
    total_usd: pickNumber(value.total_usd) ?? 0,
  };
}

function normalizeLLMSummary(value: unknown): LLMSummary {
  if (!isObjectRecord(value)) {
    return {
      calls: [],
      latency_avg_ms: [],
      tokens_total: [],
      cost_usd_total: [],
    };
  }
  return {
    calls: ensureArray(value.calls, normalizeLLMCallMetric),
    latency_avg_ms: ensureArray(value.latency_avg_ms, normalizeLLMLatencyMetric),
    tokens_total: ensureArray(value.tokens_total, normalizeLLMTokensMetric),
    cost_usd_total: ensureArray(value.cost_usd_total, normalizeLLMCostMetric),
  };
}

function normalizeWorkersSummary(value: unknown): WorkersSummary {
  if (!isObjectRecord(value)) {
    return {
      jobs: {},
      job_avg_ms: 0,
      cost_usd_total: 0,
      tokens: { prompt: 0, completion: 0 },
      stages: {},
    };
  }
  const jobs: Record<string, number> = {};
  if (isObjectRecord(value.jobs)) {
    for (const [key, val] of Object.entries(value.jobs)) {
      const num = pickNumber(val);
      if (num !== undefined) {
        jobs[key] = num;
      }
    }
  }
  const tokensRaw = isObjectRecord(value.tokens) ? value.tokens : {};
  const stages: Record<string, { count: number; avg_ms: number }> = {};
  if (isObjectRecord(value.stages)) {
    for (const [key, val] of Object.entries(value.stages)) {
      if (!isObjectRecord(val)) continue;
      stages[key] = {
        count: pickNumber(val.count) ?? 0,
        avg_ms: pickNumber(val.avg_ms) ?? 0,
      };
    }
  }
  return {
    jobs,
    job_avg_ms: pickNumber(value.job_avg_ms) ?? 0,
    cost_usd_total: pickNumber(value.cost_usd_total) ?? 0,
    tokens: {
      prompt: pickNumber(tokensRaw.prompt) ?? 0,
      completion: pickNumber(tokensRaw.completion) ?? 0,
    },
    stages,
  };
}

function normalizeTransitionSummary(value: unknown): TransitionModeSummary | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const mode = pickString(value.mode);
  if (!mode) {
    return null;
  }
  return {
    mode,
    avg_latency_ms: pickNumber(value.avg_latency_ms) ?? 0,
    no_route_ratio: pickNumber(value.no_route_ratio) ?? 0,
    fallback_ratio: pickNumber(value.fallback_ratio) ?? 0,
    entropy: pickNumber(value.entropy) ?? 0,
    repeat_rate: pickNumber(value.repeat_rate) ?? 0,
    novelty_rate: pickNumber(value.novelty_rate) ?? 0,
    count: pickNumber(value.count) ?? 0,
  };
}

function normalizeEventRow(value: unknown): EventHandlerRow | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const event = pickString(value.event);
  const handler = pickString(value.handler);
  if (!event || !handler) {
    return null;
  }
  return {
    event,
    handler,
    success: pickNumber(value.success) ?? 0,
    failure: pickNumber(value.failure) ?? 0,
    total: pickNumber(value.total) ?? 0,
    avg_ms: pickNumber(value.avg_ms) ?? 0,
  };
}

function normalizeEventsSummary(value: unknown): EventsSummary {
  if (!isObjectRecord(value)) {
    return {
      counts: {},
      handlers: [],
    };
  }
  const counts: Record<string, number> = {};
  if (isObjectRecord(value.counts)) {
    for (const [key, val] of Object.entries(value.counts)) {
      const num = pickNumber(val);
      if (num !== undefined) {
        counts[key] = num;
      }
    }
  }
  return {
    counts,
    handlers: ensureArray(value.handlers, normalizeEventRow),
  };
}

function normalizeRumSummary(value: unknown): RumSummary {
  if (!isObjectRecord(value)) {
    return {
      window: 0,
      counts: {},
      login_attempt_avg_ms: null,
      navigation_avg: {
        ttfb_ms: null,
        dom_content_loaded_ms: null,
        load_event_ms: null,
      },
    };
  }
  const counts: Record<string, number> = {};
  if (isObjectRecord(value.counts)) {
    for (const [key, val] of Object.entries(value.counts)) {
      const num = pickNumber(val);
      if (num !== undefined) {
        counts[key] = num;
      }
    }
  }
  const navigationRaw = isObjectRecord(value.navigation_avg) ? value.navigation_avg : {};
  return {
    window: pickNumber(value.window) ?? 0,
    counts,
    login_attempt_avg_ms: pickNumber(value.login_attempt_avg_ms) ?? null,
    navigation_avg: {
      ttfb_ms: pickNumber(navigationRaw.ttfb_ms) ?? null,
      dom_content_loaded_ms: pickNumber(navigationRaw.dom_content_loaded_ms) ?? null,
      load_event_ms: pickNumber(navigationRaw.load_event_ms) ?? null,
    },
  };
}

function normalizeTelemetryOverview(value: unknown): TelemetryOverview {
  if (!isObjectRecord(value)) {
    return {
      llm: null,
      workers: null,
      events: { counts: {}, handlers: [] },
      transitions: [],
      ux: {
        time_to_first_save_avg_s: 0,
        published_tagged_ratio: 0,
        save_next_total: 0,
      },
      rum: normalizeRumSummary(null),
    };
  }
  const uxRaw = isObjectRecord(value.ux) ? value.ux : {};
  return {
    llm: value.llm ? normalizeLLMSummary(value.llm) : null,
    workers: value.workers ? normalizeWorkersSummary(value.workers) : null,
    events: normalizeEventsSummary(value.events),
    transitions: ensureArray(value.transitions, normalizeTransitionSummary),
    ux: {
      time_to_first_save_avg_s: pickNumber(uxRaw.time_to_first_save_avg_s) ?? 0,
      published_tagged_ratio: pickNumber(uxRaw.published_tagged_ratio) ?? 0,
      save_next_total: pickNumber(uxRaw.save_next_total) ?? 0,
    },
    rum: normalizeRumSummary(value.rum),
  };
}

function normalizeRumEvent(value: unknown): RumEventRow | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const event = pickString(value.event);
  if (!event) {
    return null;
  }
  const url = pickString(value.url) ?? '';
  const tsRaw = value.ts;
  const timestamp = pickNumber(tsRaw) ?? pickString(tsRaw) ?? Date.now();
  return {
    ts: timestamp,
    event,
    url,
    data: isObjectRecord(value.data) ? value.data : null,
  };
}

export async function fetchTelemetryOverview(options: RequestOptions = {}): Promise<TelemetryOverview> {
  const payload = await apiGet<unknown>(TELEMETRY_OVERVIEW_ENDPOINT, { signal: options.signal });
  return normalizeTelemetryOverview(payload);
}

export async function fetchHttpSummary(options: RequestOptions = {}): Promise<HttpSummary> {
  const payload = await apiGet<unknown>(TELEMETRY_HTTP_ENDPOINT, { signal: options.signal });
  return normalizeHttpSummary(payload);
}

export async function fetchLLMSummary(options: RequestOptions = {}): Promise<LLMSummary> {
  const payload = await apiGet<unknown>(TELEMETRY_LLM_ENDPOINT, { signal: options.signal });
  return normalizeLLMSummary(payload);
}

export async function fetchWorkerSummary(options: RequestOptions = {}): Promise<WorkersSummary> {
  const payload = await apiGet<unknown>(TELEMETRY_WORKERS_ENDPOINT, { signal: options.signal });
  return normalizeWorkersSummary(payload);
}

export async function fetchEventsSummary(options: RequestOptions = {}): Promise<EventsSummary> {
  const payload = await apiGet<unknown>(TELEMETRY_EVENTS_ENDPOINT, { signal: options.signal });
  return normalizeEventsSummary(payload);
}

export async function fetchTransitionsSummary(options: RequestOptions = {}): Promise<TransitionModeSummary[]> {
  const payload = await apiGet<unknown>(TELEMETRY_TRANSITIONS_ENDPOINT, { signal: options.signal });
  return ensureArray(payload, normalizeTransitionSummary);
}

export async function fetchRumSummary(options: RumSummaryOptions = {}): Promise<RumSummary> {
  const params = new URLSearchParams();
  if (options.window && Number.isFinite(options.window)) {
    params.set('window', String(options.window));
  }
  const suffix = params.toString();
  const endpoint = suffix ? `${TELEMETRY_RUM_SUMMARY_ENDPOINT}?${suffix}` : TELEMETRY_RUM_SUMMARY_ENDPOINT;
  const payload = await apiGet<unknown>(endpoint, { signal: options.signal });
  return normalizeRumSummary(payload);
}

export async function fetchRumEvents(options: RumEventsOptions = {}): Promise<RumEventRow[]> {
  const params = new URLSearchParams();
  if (options.event) params.set('event', options.event.trim());
  if (options.url) params.set('url', options.url.trim());
  if (typeof options.offset === 'number') params.set('offset', String(options.offset));
  if (typeof options.limit === 'number') params.set('limit', String(options.limit));
  const suffix = params.toString();
  const endpoint = suffix ? `${TELEMETRY_RUM_EVENTS_ENDPOINT}?${suffix}` : TELEMETRY_RUM_EVENTS_ENDPOINT;
  const payload = await apiGet<unknown>(endpoint, { signal: options.signal });
  return ensureArray(payload, normalizeRumEvent);
}


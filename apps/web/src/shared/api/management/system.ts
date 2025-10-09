import { apiGet } from '../client';
import type {
  IncidentHistoryItem,
  PlatformAdminIntegrationSummary,
  SystemIncident,
  SystemIncidents,
  SystemOverview,
  SystemSignal,
  SystemSummary,
} from '../../types/management';
import { ensureArray, isObjectRecord, pickBoolean, pickNullableString, pickNumber, pickString } from './utils';

type FetchOptions = {
  signal?: AbortSignal;
};

const SYSTEM_OVERVIEW_ENDPOINT = '/v1/admin/system/overview';
const CONFIG_ENDPOINT = '/v1/admin/config';

function normalizeSystemSignal(value: unknown): SystemSignal | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  const label = pickString(value.label);
  const status = pickString(value.status) ?? 'unknown';
  if (!id || !label) {
    return null;
  }
  const signal: SystemSignal = {
    id,
    label,
    status,
    ok: pickBoolean(value.ok) ?? null,
    hint: pickNullableString(value.hint) ?? undefined,
    last_heartbeat: pickNullableString(value.last_heartbeat) ?? undefined,
    latency_ms: pickNumber(value.latency_ms) ?? null,
    pending: pickNumber(value.pending) ?? null,
    leased: pickNumber(value.leased) ?? null,
    failed: pickNumber(value.failed) ?? null,
    succeeded: pickNumber(value.succeeded) ?? null,
    oldest_pending_seconds: pickNumber(value.oldest_pending_seconds) ?? null,
    avg_duration_ms: pickNumber(value.avg_duration_ms) ?? null,
    failure_rate: pickNumber(value.failure_rate) ?? null,
    jobs_completed: pickNumber(value.jobs_completed) ?? null,
    jobs_failed: pickNumber(value.jobs_failed) ?? null,
    success_rate: pickNumber(value.success_rate) ?? null,
    total_calls: pickNumber(value.total_calls) ?? null,
    error_count: pickNumber(value.error_count) ?? null,
    models: ensureArray(value.models, (entry) => pickString(entry) ?? null),
    enabled: pickBoolean(value.enabled) ?? undefined,
    link: pickNullableString(value.link) ?? undefined,
  };
  return signal;
}

function normalizeIncidentHistoryItem(value: unknown): IncidentHistoryItem | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const action = pickString(value.action);
  if (!action) {
    return null;
  }
  return {
    action,
    created_at: pickNullableString(value.created_at) ?? undefined,
    reason: pickNullableString(value.reason) ?? undefined,
    payload: isObjectRecord(value.payload) ? value.payload : null,
  };
}

function normalizeSystemIncident(value: unknown): SystemIncident | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  const title = pickString(value.title);
  const status = pickString(value.status) ?? 'unknown';
  if (!id || !title) {
    return null;
  }
  return {
    id,
    title,
    status,
    severity: pickNullableString(value.severity) ?? undefined,
    source: pickNullableString(value.source) ?? undefined,
    first_seen_at: pickNullableString(value.first_seen_at) ?? undefined,
    updated_at: pickNullableString(value.updated_at) ?? undefined,
    impacts: ensureArray(value.impacts, (entry) => pickString(entry) ?? null),
    history: ensureArray(value.history, normalizeIncidentHistoryItem),
  };
}

function normalizeIntegrationSummary(value: unknown): PlatformAdminIntegrationSummary | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  const label = pickString(value.label);
  const status = pickString(value.status) ?? 'unknown';
  if (!id || !label) {
    return null;
  }
  return {
    id,
    label,
    status,
    link: pickNullableString(value.link) ?? undefined,
    hint: pickNullableString(value.hint) ?? undefined,
  };
}

function normalizeSystemIncidents(value: unknown): SystemIncidents | undefined {
  if (!isObjectRecord(value)) {
    return undefined;
  }
  const incidents: SystemIncidents = {};
  if ('active' in value) {
    incidents.active = ensureArray(value.active, normalizeSystemIncident);
  }
  if ('recent' in value) {
    incidents.recent = ensureArray(value.recent, normalizeSystemIncident);
  }
  if ('integrations' in value) {
    incidents.integrations = ensureArray(value.integrations, normalizeIntegrationSummary);
  }
  if ('error' in value) {
    incidents.error = pickNullableString(value.error) ?? undefined;
  }
  return incidents;
}

function normalizeSystemSummary(value: unknown): SystemSummary | undefined {
  if (!isObjectRecord(value)) {
    return undefined;
  }
  return {
    collected_at: pickNullableString(value.collected_at) ?? undefined,
    uptime_percent: pickNumber(value.uptime_percent) ?? undefined,
    db_latency_ms: pickNumber(value.db_latency_ms) ?? undefined,
    queue_pending: pickNumber(value.queue_pending) ?? undefined,
    queue_status: pickNullableString(value.queue_status) ?? undefined,
    worker_avg_ms: pickNumber(value.worker_avg_ms) ?? undefined,
    worker_failure_rate: pickNumber(value.worker_failure_rate) ?? undefined,
    llm_success_rate: pickNumber(value.llm_success_rate) ?? undefined,
    active_incidents: pickNumber(value.active_incidents) ?? undefined,
  };
}

function normalizeSystemOverview(value: unknown): SystemOverview {
  if (!isObjectRecord(value)) {
    throw new Error('system_overview_malformed');
  }
  const collected_at = pickString(value.collected_at);
  if (!collected_at) {
    throw new Error('system_overview_missing_timestamp');
  }
  const overview: SystemOverview = {
    collected_at,
    recommendations: isObjectRecord(value.recommendations)
      ? {
          auto_refresh_seconds: pickNumber(value.recommendations.auto_refresh_seconds) ?? undefined,
        }
      : undefined,
    signals: undefined,
    summary: normalizeSystemSummary(value.summary),
    incidents: normalizeSystemIncidents(value.incidents),
    links: isObjectRecord(value.links)
      ? Object.fromEntries(
          Object.entries(value.links).map(([key, entry]) => [key, pickNullableString(entry) ?? undefined]),
        )
      : undefined,
    changelog: ensureArray(value.changelog, (entry) => {
      if (!isObjectRecord(entry)) return null;
      const id = pickString(entry.id);
      const title = pickString(entry.title);
      if (!id || !title) return null;
      return {
        id,
        title,
        category: pickNullableString(entry.category) ?? undefined,
        published_at: pickNullableString(entry.published_at) ?? undefined,
        highlights: ensureArray(entry.highlights, (highlight) => pickString(highlight) ?? null),
      };
    }),
  };

  if (isObjectRecord(value.signals)) {
    overview.signals = Object.fromEntries(
      Object.entries(value.signals).map(([group, list]) => [group, ensureArray(list, normalizeSystemSignal)]),
    );
  }

  return overview;
}

export async function fetchSystemOverview({ signal }: FetchOptions = {}): Promise<SystemOverview> {
  const response = await apiGet<unknown>(SYSTEM_OVERVIEW_ENDPOINT, { signal });
  return normalizeSystemOverview(response);
}

export async function fetchSystemConfig({ signal }: FetchOptions = {}): Promise<Record<string, unknown>> {
  const response = await apiGet<unknown>(CONFIG_ENDPOINT, { signal });
  if (!isObjectRecord(response)) {
    return {};
  }
  return { ...response };
}

export const managementSystemApi = {
  fetchSystemOverview,
  fetchSystemConfig,
};

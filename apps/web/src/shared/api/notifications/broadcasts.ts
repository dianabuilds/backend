import { apiGet, apiPost, apiPut } from '../client';
import type {
  NotificationBroadcast,
  NotificationBroadcastAudience,
  NotificationBroadcastAudienceInput,
  NotificationBroadcastCreatePayload,
  NotificationBroadcastListParams,
  NotificationBroadcastListResponse,
  NotificationBroadcastStatus,
  NotificationBroadcastUpdatePayload,
} from '../../types/notifications';
import {
  ensureArray,
  isObjectRecord,
  pickBoolean,
  pickNullableString,
  pickNumber,
  pickString,
} from './utils';

type BroadcastFetchParams = NotificationBroadcastListParams & {
  signal?: AbortSignal;
};

const BROADCASTS_ENDPOINT = '/v1/notifications/admin/broadcasts';

function buildBroadcastQuery({ limit, offset, statuses, search }: NotificationBroadcastListParams = {}): string {
  const params = new URLSearchParams();
  if (typeof limit === 'number' && Number.isFinite(limit) && limit > 0) {
    params.set('limit', String(limit));
  }
  if (typeof offset === 'number' && Number.isFinite(offset) && offset >= 0) {
    params.set('offset', String(offset));
  }
  if (Array.isArray(statuses)) {
    const unique = Array.from(new Set(statuses.filter(Boolean)));
    unique.forEach((status) => params.append('statuses', status));
  }
  if (search && search.trim()) {
    params.set('q', search.trim());
  }
  return params.toString();
}

function normalizeAudience(raw: unknown): NotificationBroadcastAudience {
  const source = isObjectRecord(raw) ? raw : {};
  const type = (pickString(source.type) as NotificationBroadcastAudience['type']) ?? 'all_users';
  const filters = isObjectRecord(source.filters) ? source.filters : null;
  const userIds = ensureArray(source.user_ids, pickString);
  return {
    type,
    filters,
    user_ids: userIds.length ? userIds : null,
  };
}

function normalizeBroadcast(raw: unknown, fallbackId?: string): NotificationBroadcast | null {
  if (!isObjectRecord(raw)) {
    return null;
  }
  const id = pickString(raw.id) ?? fallbackId;
  const title = pickString(raw.title) ?? undefined;
  if (!id || !title) {
    return null;
  }
  const audience = normalizeAudience(raw.audience);
  const status = (pickString(raw.status) as NotificationBroadcastStatus) ?? 'draft';
  return {
    id,
    title,
    body: pickNullableString(raw.body) ?? null,
    template_id: pickNullableString(raw.template_id) ?? null,
    audience,
    status,
    created_by: pickString(raw.created_by) ?? '',
    created_at: pickNullableString(raw.created_at) ?? '',
    updated_at: pickNullableString(raw.updated_at) ?? '',
    scheduled_at: pickNullableString(raw.scheduled_at) ?? null,
    started_at: pickNullableString(raw.started_at) ?? null,
    finished_at: pickNullableString(raw.finished_at) ?? null,
    total: pickNumber(raw.total) ?? 0,
    sent: pickNumber(raw.sent) ?? 0,
    failed: pickNumber(raw.failed) ?? 0,
  };
}

function normalizeBroadcastList(payload: unknown): NotificationBroadcastListResponse {
  if (!isObjectRecord(payload)) {
    return {
      items: [],
      total: 0,
      offset: 0,
      limit: 0,
      has_next: false,
      status_counts: {},
      recipients: 0,
    };
  }
  const items = ensureArray(payload.items, normalizeBroadcast);
  const statusCountsSource = isObjectRecord(payload.status_counts) ? payload.status_counts : {};
  const status_counts: Record<string, number> = {};
  Object.entries(statusCountsSource).forEach(([key, value]) => {
    const numeric = pickNumber(value);
    if (numeric !== undefined) {
      status_counts[key] = numeric;
    }
  });
  return {
    items,
    total: pickNumber(payload.total) ?? items.length,
    offset: pickNumber(payload.offset) ?? 0,
    limit: pickNumber(payload.limit) ?? items.length,
    has_next: pickBoolean(payload.has_next) ?? (items.length > 0 && items.length >= (pickNumber(payload.limit) ?? items.length)),
    status_counts,
    recipients: pickNumber(payload.recipients) ?? 0,
  };
}

function prepareAudiencePayload(audience: NotificationBroadcastAudienceInput): NotificationBroadcastAudienceInput {
  const type = audience.type;
  const payload: NotificationBroadcastAudienceInput = { type };
  if (audience.filters !== undefined) {
    payload.filters = audience.filters;
  }
  if (audience.user_ids !== undefined) {
    payload.user_ids = audience.user_ids;
  }
  return payload;
}

export async function fetchNotificationBroadcasts(
  params: BroadcastFetchParams = {},
): Promise<NotificationBroadcastListResponse> {
  const query = buildBroadcastQuery(params);
  const url = query ? `${BROADCASTS_ENDPOINT}?${query}` : BROADCASTS_ENDPOINT;
  const response = await apiGet<unknown>(url, { signal: params.signal });
  return normalizeBroadcastList(response);
}

export async function createNotificationBroadcast(
  payload: NotificationBroadcastCreatePayload,
): Promise<NotificationBroadcast> {
  const prepared = {
    title: payload.title,
    body: payload.body ?? null,
    template_id: payload.template_id ?? null,
    audience: prepareAudiencePayload(payload.audience),
    created_by: payload.created_by,
    scheduled_at: payload.scheduled_at ?? null,
  };
  const response = await apiPost<unknown>(BROADCASTS_ENDPOINT, prepared);
  const normalized = normalizeBroadcast(response);
  if (!normalized) {
    throw new Error('broadcast_create_failed');
  }
  return normalized;
}

export async function updateNotificationBroadcast(
  id: string,
  payload: NotificationBroadcastUpdatePayload,
): Promise<NotificationBroadcast> {
  const normalizedId = id.trim();
  if (!normalizedId) {
    throw new Error('broadcast_id_missing');
  }
  const body = {
    title: payload.title,
    body: payload.body ?? null,
    template_id: payload.template_id ?? null,
    audience: prepareAudiencePayload(payload.audience),
    scheduled_at: payload.scheduled_at ?? null,
  };
  const response = await apiPut<unknown>(`${BROADCASTS_ENDPOINT}/${encodeURIComponent(normalizedId)}`, body);
  const normalized = normalizeBroadcast(response, normalizedId);
  if (!normalized) {
    throw new Error('broadcast_update_failed');
  }
  return normalized;
}

async function postBroadcastAction(
  id: string,
  action: 'send-now' | 'cancel',
): Promise<NotificationBroadcast> {
  const normalizedId = id.trim();
  if (!normalizedId) {
    throw new Error('broadcast_id_missing');
  }
  const response = await apiPost<unknown>(
    `${BROADCASTS_ENDPOINT}/${encodeURIComponent(normalizedId)}/actions/${action}`,
    {},
  );
  const normalized = normalizeBroadcast(response, normalizedId);
  if (!normalized) {
    throw new Error('broadcast_action_failed');
  }
  return normalized;
}

export async function sendNotificationBroadcastNow(id: string): Promise<NotificationBroadcast> {
  return postBroadcastAction(id, 'send-now');
}

export async function cancelNotificationBroadcast(id: string): Promise<NotificationBroadcast> {
  return postBroadcastAction(id, 'cancel');
}

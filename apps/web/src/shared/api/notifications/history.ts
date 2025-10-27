import { apiGet, apiPost } from '../client';
import type {
  NotificationHistoryItem,
  NotificationHistoryResponse,
  NotificationsListResponse,
} from '../../types/notifications';
import {
  ensureArray,
  isObjectRecord,
  pickBoolean,
  pickNullableString,
  pickNumber,
  pickString,
} from './utils';

export type FetchNotificationsHistoryOptions = {
  limit?: number;
  offset?: number;
  signal?: AbortSignal;
};

export type NotificationsHistoryPage = {
  items: NotificationHistoryItem[];
  nextOffset: number;
  hasMore: boolean;
  unread: number;
  unreadTotal: number;
  total: number;
};

const HISTORY_ENDPOINT = '/v1/notifications';

export function normalizeHistoryItem(value: unknown, fallbackId?: string): NotificationHistoryItem | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id) ?? fallbackId;
  if (!id) {
    return null;
  }
  const userId = pickString(value.user_id) ?? '';
  const channel = pickNullableString(value.channel) ?? null;
  const title = pickNullableString(value.title) ?? null;
  const message = pickNullableString(value.message) ?? null;
  const type = pickNullableString(value.type) ?? null;
  const priority = pickString(value.priority) ?? 'normal';
  const createdAt = pickNullableString(value.created_at) ?? null;
  const updatedAt = pickNullableString(value.updated_at) ?? null;
  const readAt = pickNullableString(value.read_at) ?? null;
  const isRead = pickBoolean(value.is_read);
  const meta = isObjectRecord(value.meta) ? value.meta : {};

  return {
    id,
    user_id: userId,
    channel,
    title,
    message,
    type,
    priority,
    meta,
    created_at: createdAt,
    updated_at: updatedAt,
    read_at: readAt,
    is_read: isRead ?? Boolean(readAt),
  };
}

function normalizeHistoryResponse(
  payload: unknown,
): NotificationsListResponse {
  if (!isObjectRecord(payload)) {
    return {
      items: [],
      unread: 0,
      unread_total: 0,
      total: 0,
      has_more: false,
    };
  }
  const items = ensureArray(payload.items, normalizeHistoryItem);
  const unread = pickNumber(payload.unread) ?? 0;
  const unreadTotal = pickNumber(payload.unread_total) ?? unread;
  const total = pickNumber(payload.total) ?? Math.max(items.length, unreadTotal);
  const hasMore = pickBoolean(payload.has_more) ?? false;
  return {
    items,
    unread,
    unread_total: unreadTotal,
    total,
    has_more: hasMore,
  };
}

function sanitizeLimit(limit?: number): number {
  if (typeof limit !== 'number' || Number.isNaN(limit)) {
    return 30;
  }
  const normalized = Math.floor(limit);
  if (normalized <= 0) {
    return 30;
  }
  if (normalized > 100) {
    return 100;
  }
  return normalized;
}

function sanitizeOffset(offset?: number): number {
  if (typeof offset !== 'number' || Number.isNaN(offset)) {
    return 0;
  }
  const normalized = Math.floor(offset);
  return normalized < 0 ? 0 : normalized;
}

export async function fetchNotificationsHistory(
  options: FetchNotificationsHistoryOptions = {},
): Promise<NotificationsHistoryPage> {
  const limit = sanitizeLimit(options.limit);
  const offset = sanitizeOffset(options.offset);
  const search = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  const response = await apiGet<NotificationHistoryResponse | NotificationsListResponse>(
    `${HISTORY_ENDPOINT}?${search.toString()}`,
    {
      signal: options.signal,
    },
  );
  const normalized = normalizeHistoryResponse(response);
  const items = normalized.items;
  const unreadTotal = normalized.unread_total ?? normalized.unread ?? 0;
  const total = normalized.total ?? items.length;
  const hasMore =
    normalized.has_more ??
    (typeof normalized.total === 'number'
      ? offset + items.length < Math.max(normalized.total, 0)
      : items.length === limit);
  return {
    items,
    unread: normalized.unread ?? unreadTotal,
    unreadTotal,
    total,
    nextOffset: Math.min(total, offset + items.length),
    hasMore,
  };
}

export type MarkNotificationAsReadOptions = {
  payload?: Record<string, unknown>;
  signal?: AbortSignal;
};

export async function markNotificationAsRead(
  notificationId: string,
  options: MarkNotificationAsReadOptions = {},
): Promise<NotificationHistoryItem | null> {
  const id = notificationId?.trim();
  if (!id) {
    throw new Error('notification_id_missing');
  }
  const response = await apiPost<{ notification?: unknown }>(
    `/v1/notifications/read/${encodeURIComponent(id)}`,
    options.payload ?? {},
    { signal: options.signal },
  );
  return normalizeHistoryItem(response?.notification, id);
}

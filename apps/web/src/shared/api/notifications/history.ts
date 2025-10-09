import { apiGet, apiPost } from '../client';
import type {
  NotificationHistoryItem,
  NotificationHistoryResponse,
} from '../../types/notifications';
import {
  ensureArray,
  isObjectRecord,
  pickNullableString,
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
};

const HISTORY_ENDPOINT = '/v1/notifications';

function normalizeHistoryItem(value: unknown): NotificationHistoryItem | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  if (!id) {
    return null;
  }
  const item: NotificationHistoryItem = { id };
  const title = pickNullableString(value.title);
  if (title !== undefined) {
    item.title = title;
  }
  const message = pickNullableString(value.message);
  if (message !== undefined) {
    item.message = message;
  }
  const type = pickNullableString(value.type);
  if (type !== undefined) {
    item.type = type;
  }
  const priority = pickNullableString(value.priority);
  if (priority !== undefined) {
    item.priority = priority;
  }
  const createdAt = pickNullableString(value.created_at);
  if (createdAt !== undefined) {
    item.created_at = createdAt;
  }
  const readAt = pickNullableString(value.read_at);
  if (readAt !== undefined) {
    item.read_at = readAt;
  }
  if (value.meta === null) {
    item.meta = null;
  } else if (isObjectRecord(value.meta)) {
    item.meta = value.meta;
  }
  return item;
}

function normalizeHistoryResponse(
  payload: NotificationHistoryResponse | undefined,
): NotificationHistoryItem[] {
  if (!payload) {
    return [];
  }
  return ensureArray(payload.items, normalizeHistoryItem);
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
  const response = await apiGet<NotificationHistoryResponse>(`${HISTORY_ENDPOINT}?${search.toString()}`, {
    signal: options.signal,
  });
  const items = normalizeHistoryResponse(response);
  return {
    items,
    nextOffset: offset + items.length,
    hasMore: items.length === limit,
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
  return normalizeHistoryItem(response?.notification);
}




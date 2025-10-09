import { apiGet, apiPost, apiPut } from '../client';
import type {
  NotificationBroadcastListParams,
  NotificationBroadcastListResponse,
  NotificationBroadcastPayload,
} from '../../types/notifications';

type BroadcastFetchParams = NotificationBroadcastListParams & {
  signal?: AbortSignal;
};

const BROADCASTS_ENDPOINT = '/v1/notifications/admin/broadcasts';

function buildBroadcastQuery({ limit, offset, status, search }: NotificationBroadcastListParams = {}): string {
  const params = new URLSearchParams();
  if (typeof limit === 'number') {
    params.set('limit', String(limit));
  }
  if (typeof offset === 'number') {
    params.set('offset', String(offset));
  }
  if (status && status !== 'all') {
    params.set('status', status);
  }
  if (search) {
    params.set('q', search);
  }
  return params.toString();
}

export async function fetchNotificationBroadcasts(
  params: BroadcastFetchParams = {},
): Promise<NotificationBroadcastListResponse> {
  const query = buildBroadcastQuery(params);
  const url = query ? `${BROADCASTS_ENDPOINT}?${query}` : BROADCASTS_ENDPOINT;
  return apiGet<NotificationBroadcastListResponse>(url, { signal: params.signal });
}

export async function createNotificationBroadcast(payload: NotificationBroadcastPayload): Promise<void> {
  await apiPost(BROADCASTS_ENDPOINT, payload);
}

export async function updateNotificationBroadcast(id: string, payload: NotificationBroadcastPayload): Promise<void> {
  await apiPut(`${BROADCASTS_ENDPOINT}/${id}`, payload);
}

export async function sendNotificationBroadcastNow(id: string): Promise<void> {
  await apiPost(`${BROADCASTS_ENDPOINT}/${id}/actions/send-now`, {});
}

export async function cancelNotificationBroadcast(id: string): Promise<void> {
  await apiPost(`${BROADCASTS_ENDPOINT}/${id}/actions/cancel`, {});
}

import { apiRequestRaw } from '../client';
import type {
  NotificationPreferences,
  NotificationPreferencesResponse,
} from '../../types/notifications';
import { isObjectRecord } from './utils';

export const NOTIFICATION_PREFERENCES_ENDPOINT = '/v1/me/settings/notifications/preferences' as const;

export type FetchNotificationPreferencesOptions = {
  signal?: AbortSignal;
};

export type UpdateNotificationPreferencesOptions = {
  headers?: Record<string, string>;
  signal?: AbortSignal;
};

function extractPreferences(
  payload: NotificationPreferencesResponse | undefined,
  fallback: NotificationPreferences = {},
): NotificationPreferences {
  if (payload && isObjectRecord(payload.preferences)) {
    return payload.preferences as NotificationPreferences;
  }
  return fallback;
}

export async function fetchNotificationPreferences(
  { signal }: FetchNotificationPreferencesOptions = {},
): Promise<{ preferences: NotificationPreferences; etag: string | null }> {
  const response = await apiRequestRaw(NOTIFICATION_PREFERENCES_ENDPOINT, { signal });
  const json = (await response.json().catch(() => undefined)) as NotificationPreferencesResponse | undefined;
  return {
    preferences: extractPreferences(json),
    etag: response.headers.get('ETag'),
  };
}

export async function updateNotificationPreferences(
  preferences: NotificationPreferences,
  options: UpdateNotificationPreferencesOptions = {},
): Promise<{ preferences: NotificationPreferences; etag: string | null }> {
  const response = await apiRequestRaw(NOTIFICATION_PREFERENCES_ENDPOINT, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    body: JSON.stringify({ preferences }),
    signal: options.signal,
  });
  const json = (await response.json().catch(() => undefined)) as NotificationPreferencesResponse | undefined;
  return {
    preferences: extractPreferences(json, preferences),
    etag: response.headers.get('ETag'),
  };
}

import { apiGet } from '../client';
import type {
  NotificationChannelOverview,
  NotificationSummaryOverview,
  NotificationTopicChannel,
  NotificationTopicOverview,
  NotificationsChannelsOverview,
  NotificationsChannelsOverviewResponse,
} from '../../types/notifications';
import { NOTIFICATION_PREFERENCES_ENDPOINT } from './preferences';
import {
  ensureArray,
  isObjectRecord,
  pickBoolean,
  pickNullableString,
  pickNumber,
  pickString,
} from './utils';

const CHANNEL_STATUSES = new Set(['required', 'recommended', 'optional']);

function normalizeChannelOverview(value: unknown): NotificationChannelOverview | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const key = pickString(value.key);
  if (!key) {
    return null;
  }
  const label = pickString(value.label) ?? key;
  const statusRaw = pickString(value.status);
  const status = CHANNEL_STATUSES.has(statusRaw ?? '') ? (statusRaw as NotificationChannelOverview['status']) : 'optional';
  const optIn = pickBoolean(value.opt_in) ?? false;
  return {
    key,
    label,
    status,
    opt_in: optIn,
  };
}

function normalizeTopicChannel(value: unknown): NotificationTopicChannel | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const key = pickString(value.key);
  const label = pickString(value.label) ?? key;
  if (!key || !label) {
    return null;
  }
  const delivery = pickString(value.delivery) ?? 'opt_in';
  const optIn = pickBoolean(value.opt_in) ?? false;
  const topicChannel: NotificationTopicChannel = {
    key,
    label,
    delivery,
    opt_in: optIn,
  };
  if (value.locked !== undefined) {
    const locked = pickBoolean(value.locked);
    if (locked !== undefined) {
      topicChannel.locked = locked;
    }
  }
  if (value.digest !== undefined) {
    const digest = pickNullableString(value.digest);
    if (digest !== undefined) {
      topicChannel.digest = digest;
    }
  }
  if (value.supports_digest !== undefined) {
    const supports = pickBoolean(value.supports_digest);
    if (supports !== undefined) {
      topicChannel.supports_digest = supports;
    }
  }
  return topicChannel;
}

function normalizeTopicOverview(value: unknown): NotificationTopicOverview | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const key = pickString(value.key);
  const label = pickString(value.label) ?? key;
  if (!key || !label) {
    return null;
  }
  const topic: NotificationTopicOverview = {
    key,
    label,
    channels: ensureArray(value.channels, normalizeTopicChannel),
  };
  if (value.description !== undefined) {
    topic.description = pickNullableString(value.description);
  }
  return topic;
}

function normalizeSummary(value: unknown): NotificationSummaryOverview {
  if (!isObjectRecord(value)) {
    return {
      active_channels: 0,
      total_channels: 0,
    };
  }
  const active = pickNumber(value.active_channels) ?? 0;
  const total = pickNumber(value.total_channels) ?? active;
  const summary: NotificationSummaryOverview = {
    active_channels: active,
    total_channels: total,
  };
  if (value.email_digest !== undefined) {
    const digest = pickNullableString(value.email_digest);
    if (digest !== undefined) {
      summary.email_digest = digest;
    }
  }
  if (value.updated_at !== undefined) {
    const updatedAt = pickNullableString(value.updated_at);
    if (updatedAt !== undefined) {
      summary.updated_at = updatedAt;
    }
  }
  return summary;
}

function normalizeOverview(payload: NotificationsChannelsOverviewResponse | undefined): NotificationsChannelsOverview {
  if (!payload || !isObjectRecord(payload.overview)) {
    throw new Error('notifications_overview_malformed');
  }
  const rawOverview = payload.overview as Record<string, unknown>;
  return {
    channels: ensureArray(rawOverview.channels, normalizeChannelOverview),
    topics: ensureArray(rawOverview.topics, normalizeTopicOverview),
    summary: normalizeSummary(rawOverview.summary),
  };
}

export type FetchNotificationsChannelsOverviewOptions = {
  signal?: AbortSignal;
};

export async function fetchNotificationsChannelsOverview(
  options: FetchNotificationsChannelsOverviewOptions = {},
): Promise<NotificationsChannelsOverview> {
  const response = await apiGet<NotificationsChannelsOverviewResponse>(NOTIFICATION_PREFERENCES_ENDPOINT, {
    signal: options.signal,
  });
  return normalizeOverview(response);
}


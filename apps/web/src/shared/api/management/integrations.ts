import { apiGet, apiPost } from '../client';
import type {
  IntegrationItem,
  IntegrationOverview,
  ManagementConfig,
  NotificationTestChannel,
  NotificationTestPayload,
} from '../../types/management';
import { ensureArray, isObjectRecord, pickBoolean, pickNullableString, pickNumber, pickString } from './utils';

type FetchIntegrationsOptions = {
  signal?: AbortSignal;
};

type SendTestOptions = {
  signal?: AbortSignal;
};

const INTEGRATIONS_ENDPOINT = '/v1/admin/integrations';
const CONFIG_ENDPOINT = '/v1/admin/config';
const NOTIFICATIONS_SEND_ENDPOINT = '/v1/notifications/send';

function normalizeIntegrationItem(value: unknown): IntegrationItem | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  if (!id) {
    return null;
  }
  return {
    id,
    status: pickString(value.status) ?? 'unknown',
    connected: pickBoolean(value.connected),
    topics: ensureArray(value.topics, (entry) => pickString(entry) ?? null),
    event_group: pickNullableString(value.event_group) ?? undefined,
    idempotency_ttl: pickNumber(value.idempotency_ttl) ?? null,
    smtp_host: pickNullableString(value.smtp_host) ?? undefined,
    smtp_port: pickNumber(value.smtp_port),
    smtp_tls: pickBoolean(value.smtp_tls),
    smtp_mock: pickBoolean(value.smtp_mock),
    mail_from: pickNullableString(value.mail_from) ?? undefined,
    mail_from_name: pickNullableString(value.mail_from_name) ?? undefined,
  };
}

function normalizeIntegrationOverview(value: unknown): IntegrationOverview {
  if (!isObjectRecord(value)) {
    return { collected_at: undefined, items: [] };
  }
  return {
    collected_at: pickNullableString(value.collected_at) ?? undefined,
    items: ensureArray(value.items, normalizeIntegrationItem),
  };
}

function normalizeConfig(value: unknown): ManagementConfig {
  if (!isObjectRecord(value)) {
    return {};
  }
  const config: ManagementConfig = {};
  if (value.env !== undefined) {
    config.env = pickNullableString(value.env);
  }
  if (value.database_url !== undefined) {
    config.database_url = pickNullableString(value.database_url) ?? undefined;
  }
  if (value.redis_url !== undefined) {
    config.redis_url = pickNullableString(value.redis_url) ?? undefined;
  }
  if (value.event_topics !== undefined) {
    config.event_topics = pickNullableString(value.event_topics) ?? undefined;
  }
  if (value.event_group !== undefined) {
    config.event_group = pickNullableString(value.event_group) ?? undefined;
  }
  return config;
}

export async function fetchIntegrationsOverview({ signal }: FetchIntegrationsOptions = {}): Promise<IntegrationOverview> {
  const response = await apiGet<unknown>(INTEGRATIONS_ENDPOINT, { signal });
  return normalizeIntegrationOverview(response);
}

export async function fetchManagementConfig({ signal }: FetchIntegrationsOptions = {}): Promise<ManagementConfig> {
  const response = await apiGet<unknown>(CONFIG_ENDPOINT, { signal });
  return normalizeConfig(response);
}

export async function sendNotificationTest(
  channel: NotificationTestChannel,
  payload: NotificationTestPayload,
  { signal }: SendTestOptions = {},
): Promise<void> {
  await apiPost(NOTIFICATIONS_SEND_ENDPOINT, { channel, payload }, { signal });
}

export const managementIntegrationsApi = {
  fetchIntegrationsOverview,
  fetchManagementConfig,
  sendNotificationTest,
};

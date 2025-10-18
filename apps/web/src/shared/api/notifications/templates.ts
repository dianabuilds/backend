import { apiDelete, apiGet, apiPost } from '../client';
import type {
  NotificationTemplate,
  NotificationTemplatePayload,
  NotificationTemplatesResponse,
} from '../../types/notifications';
import { ensureArray, isObjectRecord, pickNullableString, pickString } from './utils';

const TEMPLATES_ENDPOINT = '/v1/notifications/admin/templates';

function normalizeTemplate(value: unknown): NotificationTemplate | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  const slug = pickString(value.slug);
  const name = pickString(value.name);
  const body = pickString(value.body);
  const createdAt = pickString(value.created_at) ?? pickString(value.createdAt);
  const updatedAt = pickString(value.updated_at) ?? pickString(value.updatedAt);
  if (!id || !slug || !name || !body || !createdAt || !updatedAt) {
    return null;
  }
  const template: NotificationTemplate = {
    id,
    slug,
    name,
    body,
    description: pickNullableString(value.description) ?? null,
    subject: pickNullableString(value.subject) ?? null,
    locale: pickNullableString(value.locale) ?? null,
    variables: isObjectRecord(value.variables) ? value.variables : {},
    meta: isObjectRecord(value.meta) ? value.meta : {},
    created_by: pickNullableString(value.created_by) ?? null,
    created_at: createdAt,
    updated_at: updatedAt,
  };
  return template;
}

function normalizeTemplatesPayload(payload: NotificationTemplatesResponse | undefined): NotificationTemplate[] {
  if (!payload) {
    return [];
  }
  return ensureArray(payload.items, normalizeTemplate);
}

export type FetchNotificationTemplatesOptions = {
  signal?: AbortSignal;
};

export async function fetchNotificationTemplates({ signal }: FetchNotificationTemplatesOptions = {}): Promise<NotificationTemplate[]> {
  const response = await apiGet<NotificationTemplatesResponse>(TEMPLATES_ENDPOINT, { signal });
  return normalizeTemplatesPayload(response);
}

export async function saveNotificationTemplate(payload: NotificationTemplatePayload): Promise<void> {
  const prepared: NotificationTemplatePayload = {
    ...payload,
    slug: payload.slug ?? null,
    description: payload.description ?? null,
    subject: payload.subject ?? null,
    locale: payload.locale ?? null,
    variables: payload.variables ?? null,
    meta: payload.meta ?? null,
    created_by: payload.created_by ?? null,
  };
  await apiPost(TEMPLATES_ENDPOINT, prepared);
}

export async function deleteNotificationTemplate(id: string): Promise<void> {
  const normalizedId = id?.trim();
  if (!normalizedId) {
    throw new Error('template_id_missing');
  }
  await apiDelete(`${TEMPLATES_ENDPOINT}/${normalizedId}`);
}

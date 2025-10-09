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
  const createdAt = pickString(value.created_at);
  const updatedAt = pickString(value.updated_at);
  if (!id || !slug || !name || !body || !createdAt || !updatedAt) {
    return null;
  }
  const template: NotificationTemplate = {
    id,
    slug,
    name,
    body,
    created_at: createdAt,
    updated_at: updatedAt,
  };
  const description = pickNullableString(value.description);
  if (description !== undefined) {
    template.description = description;
  }
  const subject = pickNullableString(value.subject);
  if (subject !== undefined) {
    template.subject = subject;
  }
  const locale = pickNullableString(value.locale);
  if (locale !== undefined) {
    template.locale = locale;
  }
  if (value.variables !== undefined) {
    if (value.variables === null) {
      template.variables = null;
    } else if (isObjectRecord(value.variables)) {
      template.variables = value.variables;
    }
  }
  if (value.meta !== undefined) {
    if (value.meta === null) {
      template.meta = null;
    } else if (isObjectRecord(value.meta)) {
      template.meta = value.meta;
    }
  }
  const createdBy = pickNullableString(value.created_by);
  if (createdBy !== undefined) {
    template.created_by = createdBy;
  }
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
  await apiPost(TEMPLATES_ENDPOINT, payload);
}

export async function deleteNotificationTemplate(id: string): Promise<void> {
  const normalizedId = id?.trim();
  if (!normalizedId) {
    throw new Error('template_id_missing');
  }
  await apiDelete(`${TEMPLATES_ENDPOINT}/${normalizedId}`);
}

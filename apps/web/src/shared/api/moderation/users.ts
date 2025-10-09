import { apiGet, apiPost } from '../client';
import {
  ModerationUserDetail,
  ModerationUsersList,
} from '../../types/moderation';
import {
  ensureArray,
  isObjectRecord,
  normalizeUserDetail,
  normalizeUserSummary,
  pickNumber,
  pickString,
} from './utils';

export type FetchModerationUsersParams = {
  limit?: number;
  cursor?: string | null;
  status?: string | null;
  role?: string | null;
  registrationFrom?: string | null;
  registrationTo?: string | null;
  search?: string | null;
  signal?: AbortSignal;
};

export async function fetchModerationUsers(
  { limit = 25, cursor, status, role, registrationFrom, registrationTo, search, signal }: FetchModerationUsersParams = {},
): Promise<ModerationUsersList> {
  const params = new URLSearchParams();
  params.set('limit', String(limit));
  if (cursor) params.set('cursor', cursor);
  if (status && status !== 'all') params.set('status', status);
  if (role && role !== 'any') params.set('role', role);
  if (registrationFrom) params.set('registered_from', registrationFrom);
  if (registrationTo) params.set('registered_to', registrationTo);
  if (search && search.trim()) params.set('q', search.trim());

  const payload = await apiGet<unknown>(`/api/moderation/users?${params.toString()}`, { signal });
  const source = isObjectRecord(payload) ? payload : {};

  const items = ensureArray(source.items, (item) => normalizeUserSummary(item)).filter((user) => user.id.trim().length > 0);
  const nextCursor = pickString(source.next_cursor) ?? pickString(source.nextCursor) ?? null;
  const total = pickNumber(source.total);
  const meta = isObjectRecord(source.meta) ? source.meta : undefined;

  return {
    items,
    nextCursor,
    total: total ?? undefined,
    meta,
  };
}

export async function fetchModerationUserDetail(userId: string, options: { signal?: AbortSignal } = {}): Promise<ModerationUserDetail> {
  const trimmed = userId.trim();
  if (!trimmed) {
    throw new Error('moderation_user_id_missing');
  }
  const payload = await apiGet<unknown>(`/api/moderation/users/${encodeURIComponent(trimmed)}`, { signal: options.signal });
  return normalizeUserDetail(payload);
}

export type UpdateModerationUserRolesPayload = {
  add: string[];
  remove: string[];
};

export async function updateModerationUserRoles(
  userId: string,
  payload: UpdateModerationUserRolesPayload,
  options: { signal?: AbortSignal } = {},
): Promise<void> {
  const trimmed = userId.trim();
  if (!trimmed) {
    throw new Error('moderation_user_id_missing');
  }
  await apiPost(`/api/moderation/users/${encodeURIComponent(trimmed)}/roles`, payload, { signal: options.signal });
}

export type CreateModerationSanctionPayload = {
  type: string;
  reason?: string;
  duration_hours?: number;
};

export async function createModerationUserSanction(
  userId: string,
  payload: CreateModerationSanctionPayload,
  options: { signal?: AbortSignal } = {},
): Promise<void> {
  const trimmed = userId.trim();
  if (!trimmed) {
    throw new Error('moderation_user_id_missing');
  }
  await apiPost(`/api/moderation/users/${encodeURIComponent(trimmed)}/sanctions`, payload, { signal: options.signal });
}

export type CreateModerationNotePayload = {
  text: string;
  pinned?: boolean;
};

export async function createModerationUserNote(
  userId: string,
  payload: CreateModerationNotePayload,
  options: { signal?: AbortSignal } = {},
): Promise<void> {
  const trimmed = userId.trim();
  if (!trimmed) {
    throw new Error('moderation_user_id_missing');
  }
  await apiPost(`/api/moderation/users/${encodeURIComponent(trimmed)}/notes`, payload, { signal: options.signal });
}

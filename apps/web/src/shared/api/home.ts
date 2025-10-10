import { apiGet, apiPost, apiPut } from './client';
import { extractErrorMessage } from '../utils/errors';
import type {
  HomeAdminPayload,
  HomeConfigPayload,
  HomeConfigSnapshot,
  HomeHistoryEntry,
  HomeConfigStatus,
  HomeErrorPayload,
  HomePreviewResult,
  HomePublishResult,
  HomeRestoreResult,
} from '../types/home';
import { pushGlobalToast } from '../ui/toastBus';

const HOME_ENDPOINT = '/v1/admin/home';
const HOME_PUBLISH_ENDPOINT = `${HOME_ENDPOINT}/publish`;
const HOME_PREVIEW_ENDPOINT = `${HOME_ENDPOINT}/preview`;
const HOME_RESTORE_ENDPOINT = `${HOME_ENDPOINT}/restore`;
const DEFAULT_SLUG = 'main';

const DEFAULT_ERROR_MESSAGE = 'Не удалось выполнить запрос. Попробуйте ещё раз.';
const SESSION_LOST_MESSAGE = 'Сессия истекла. Пожалуйста, войдите снова.';
const PERMISSION_DENIED_MESSAGE = 'Недостаточно прав';
const INVALID_RESPONSE_MESSAGE = 'Некорректный ответ сервера. Попробуйте позже.';

const HOME_ERROR_MESSAGES: Record<string, string> = {
  insufficient_permissions: PERMISSION_DENIED_MESSAGE,
  home_config_not_found: 'Конфигурация главной страницы не найдена.',
  home_config_draft_not_found: 'Черновик главной страницы не найден.',
  home_config_version_not_found: 'Указанная версия публикации не найдена.',
  home_config_duplicate_block_ids: 'Идентификаторы блоков должны быть уникальными.',
  home_config_schema_invalid: 'Конфигурация не соответствует ожидаемой схеме.',
  home_config_validation_failed: 'Конфигурация не прошла валидацию.',
  payload_not_mapping: 'Неверный формат данных конфигурации.',
  home_storage_unavailable: 'Хранилище конфигураций временно недоступно. Попробуйте позже.',
  home_config_engine_unavailable: 'Хранилище конфигураций временно недоступно. Попробуйте позже.',
};

type ApiError = Error & { status?: number; body?: string };

type RequestOptions = {
  signal?: AbortSignal;
  headers?: Record<string, string>;
};

type DraftRequestOptions = RequestOptions & {
  slug?: string;
};

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

function pickString(value: unknown): string | undefined {
  return typeof value === 'string' ? value : undefined;
}

function pickNullableString(value: unknown): string | null | undefined {
  if (value === null) return null;
  return pickString(value);
}

function pickNumber(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return undefined;
}

function pickStatus(value: unknown): HomeConfigStatus | undefined {
  if (typeof value !== 'string') {
    return undefined;
  }
  const normalized = value.trim().toLowerCase();
  if (normalized === 'draft' || normalized === 'published') {
    return normalized as HomeConfigStatus;
  }
  return undefined;
}

function normalizeSnapshot(payload: unknown): HomeConfigSnapshot | null {
  if (!isObjectRecord(payload)) {
    return null;
  }
  const id = pickString(payload.id);
  const slug = pickString(payload.slug)?.trim();
  const version = pickNumber(payload.version);
  const status = pickStatus(payload.status);
  const createdAt = pickString(payload.created_at);
  const updatedAt = pickString(payload.updated_at);
  if (!id || !slug || version === undefined || status === undefined || !createdAt || !updatedAt) {
    return null;
  }
  const data = isObjectRecord(payload.data) ? (payload.data as Record<string, unknown>) : {};
  return {
    id,
    slug,
    version,
    status,
    data,
    created_at: createdAt,
    updated_at: updatedAt,
    published_at: pickNullableString(payload.published_at) ?? null,
    created_by: pickNullableString(payload.created_by) ?? null,
    updated_by: pickNullableString(payload.updated_by) ?? null,
    draft_of: pickNullableString(payload.draft_of) ?? null,
  };
}

function normalizeHistoryEntry(payload: unknown): HomeHistoryEntry | null {
  if (!isObjectRecord(payload)) {
    return null;
  }
  const configId = pickString(payload.config_id ?? payload.configId);
  const version = pickNumber(payload.version);
  const action = pickString(payload.action)?.trim() || null;
  const actor = pickNullableString(payload.actor) ?? null;
  const actorTeam = pickNullableString(payload.actor_team ?? payload.actorTeam) ?? null;
  const commentRaw = pickNullableString(payload.comment);
  const comment = commentRaw == null ? null : commentRaw.trim() || null;
  const createdAt = pickString(payload.created_at ?? payload.createdAt);
  const publishedAt = pickNullableString(payload.published_at ?? payload.publishedAt) ?? null;
  const currentFlag = (payload as any).is_current ?? (payload as any).isCurrent;
  const isCurrent = typeof currentFlag === 'boolean' ? currentFlag : currentFlag === 'true';
  if (!configId || version === undefined || !createdAt) {
    return null;
  }
  return {
    configId,
    version,
    action: action || 'publish',
    actor,
    actorTeam,
    comment,
    createdAt,
    publishedAt,
    isCurrent: isCurrent ?? false,
  };
}

function normalizeAdminResponse(value: unknown, fallbackSlug: string): HomeAdminPayload {
  if (!isObjectRecord(value)) {
    return { slug: fallbackSlug, draft: null, published: null, history: [] };
  }
  const slug = pickString(value.slug)?.trim() || fallbackSlug;
  const draft = normalizeSnapshot((value as any).draft);
  const published = normalizeSnapshot((value as any).published);
  const historyRaw = Array.isArray((value as any).history) ? (value as any).history : [];
  const history = historyRaw
    .map((item: unknown) => normalizeHistoryEntry(item))
    .filter((entry: HomeHistoryEntry | null): entry is HomeHistoryEntry => entry !== null);
  return { slug, draft, published, history };
}

function normalizePublishResponse(value: unknown, fallbackSlug: string): HomePublishResult {
  if (!isObjectRecord(value)) {
    throw new Error('home_invalid_publish_response');
  }
  const slug = pickString(value.slug)?.trim() || fallbackSlug;
  const published = normalizeSnapshot((value as any).published);
  if (!published) {
    throw new Error('home_invalid_publish_response');
  }
  return { slug, published };
}

function normalizePreviewResponse(value: unknown, fallbackSlug: string): HomePreviewResult {
  if (!isObjectRecord(value)) {
    return { slug: fallbackSlug, payload: {} };
  }
  const slug = pickString(value.slug)?.trim() || fallbackSlug;
  const payload = isObjectRecord((value as any).payload)
    ? ((value as any).payload as Record<string, unknown>)
    : {};
  return { slug, payload };
}

function normalizeRestoreResponse(value: unknown, fallbackSlug: string): HomeRestoreResult {
  if (!isObjectRecord(value)) {
    throw new Error('home_invalid_restore_response');
  }
  const slug = pickString(value.slug)?.trim() || fallbackSlug;
  const draft = normalizeSnapshot((value as any).draft);
  if (!draft) {
    throw new Error('home_invalid_restore_response');
  }
  return { slug, draft };
}

function parseErrorBody(error: ApiError): HomeErrorPayload | null {
  const raw = error?.body;
  if (typeof raw !== 'string' || !raw.trim()) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') {
      return parsed as HomeErrorPayload;
    }
  } catch {
    return null;
  }
  return null;
}

function extractErrorCode(payload: HomeErrorPayload | null): string | null {
  if (!payload || typeof payload !== 'object') {
    return null;
  }
  const candidates: Array<unknown> = [payload.code, payload.error, payload.detail];
  const detail = payload.detail;
  if (detail && typeof detail === 'object') {
    candidates.push((detail as any).code);
    candidates.push((detail as any).error);
  }
  if (typeof payload.message === 'string') {
    candidates.push(payload.message);
  }
  for (const candidate of candidates) {
    if (typeof candidate === 'string' && candidate.trim()) {
      return candidate.trim();
    }
  }
  return null;
}


function formatMessageWithDetail(base: string, detail: string): string {
  const trimmed = base.endsWith('.') ? base.slice(0, -1) : base;
  return detail ? `${trimmed}: ${detail}` : trimmed;
}

function resolveHomeErrorMessage(error: ApiError): string {
  const payload = parseErrorBody(error);
  const code = extractErrorCode(payload);
  if (code) {
    if (code === 'home_config_duplicate_block_ids') {
      const details = Array.isArray(payload?.details) ? payload?.details : [];
      const duplicates = details
        .map((item) => (typeof item === 'string' ? item.trim() : null))
        .filter((item): item is string => !!item);
      if (duplicates.length) {
        const base = HOME_ERROR_MESSAGES[code] || DEFAULT_ERROR_MESSAGE;
        return formatMessageWithDetail(base, duplicates.join(', '));
      }
    }
    if (code === 'home_config_schema_invalid') {
      const violations = Array.isArray(payload?.details) ? payload?.details : [];
      const message = violations.find((item) => typeof item?.message === 'string');
      if (message && typeof (message as any).message === 'string') {
        const base = HOME_ERROR_MESSAGES[code] || DEFAULT_ERROR_MESSAGE;
        return formatMessageWithDetail(base, (message as any).message);
      }
    }
    const mapped = HOME_ERROR_MESSAGES[code];
    if (mapped) {
      return mapped;
    }
  }
  return extractErrorMessage(error, DEFAULT_ERROR_MESSAGE);
}

function handleHomeApiError(error: unknown): never {
  const err = error as ApiError;
  const status = err?.status;
  if (status === 401) {
    pushGlobalToast({ intent: 'error', description: SESSION_LOST_MESSAGE });
    throw err;
  }
  if (status === 403) {
    pushGlobalToast({ intent: 'error', description: PERMISSION_DENIED_MESSAGE });
    throw err;
  }
  const message = resolveHomeErrorMessage(err);
  pushGlobalToast({ intent: 'error', description: message });
  throw err;
}

async function requestWithHandling<T>(request: () => Promise<T>): Promise<T> {
  try {
    return await request();
  } catch (error) {
    return handleHomeApiError(error);
  }
}

function resolveSlug(slug?: string): string {
  if (typeof slug !== 'string') {
    return DEFAULT_SLUG;
  }
  const trimmed = slug.trim();
  return trimmed || DEFAULT_SLUG;
}

function buildHomeEndpoint(slug: string): string {
  const normalized = resolveSlug(slug);
  if (normalized === DEFAULT_SLUG) {
    return HOME_ENDPOINT;
  }
  return `${HOME_ENDPOINT}?slug=${encodeURIComponent(normalized)}`;
}

function makePayload(payload: HomeConfigPayload | undefined): HomeConfigPayload {
  const slug = resolveSlug(payload?.slug);
  const data = payload?.data ?? null;
  const rawComment = payload?.comment;
  let comment: string | null | undefined = rawComment;
  if (typeof rawComment === "string") {
    const trimmed = rawComment.trim();
    comment = trimmed.length ? trimmed : undefined;
  }
  if (comment === undefined) {
    return { slug, data };
  }
  return { slug, data, comment };
}

export async function getDraft(options: DraftRequestOptions = {}): Promise<HomeAdminPayload> {
  const slug = resolveSlug(options.slug);
  const endpoint = buildHomeEndpoint(slug);
  const response = await requestWithHandling(() => apiGet<unknown>(endpoint, { signal: options.signal, headers: options.headers }));
  return normalizeAdminResponse(response, slug);
}

export async function saveDraft(payload: HomeConfigPayload, options: RequestOptions = {}): Promise<HomeConfigSnapshot> {
  const requestPayload = makePayload(payload);
  const response = await requestWithHandling(() => apiPut<unknown>(HOME_ENDPOINT, requestPayload, { signal: options.signal, headers: options.headers }));
  const snapshot = normalizeSnapshot(response);
  if (!snapshot) {
    pushGlobalToast({ intent: 'error', description: INVALID_RESPONSE_MESSAGE });
    throw new Error('home_invalid_draft_response');
  }
  return snapshot;
}

export async function publishHome(payload: HomeConfigPayload, options: RequestOptions = {}): Promise<HomePublishResult> {
  const requestPayload = makePayload(payload);
  const response = await requestWithHandling(() => apiPost<unknown>(HOME_PUBLISH_ENDPOINT, requestPayload, { signal: options.signal, headers: options.headers }));
  try {
    return normalizePublishResponse(response, requestPayload.slug ?? DEFAULT_SLUG);
  } catch (err) {
    pushGlobalToast({ intent: 'error', description: INVALID_RESPONSE_MESSAGE });
    throw err;
  }
}

export async function previewHome(payload: HomeConfigPayload, options: RequestOptions = {}): Promise<HomePreviewResult> {
  const requestPayload = makePayload(payload);
  const response = await requestWithHandling(() => apiPost<unknown>(HOME_PREVIEW_ENDPOINT, requestPayload, { signal: options.signal, headers: options.headers }));
  return normalizePreviewResponse(response, requestPayload.slug ?? DEFAULT_SLUG);
}

export async function restoreHome(version: number, payload: HomeConfigPayload, options: RequestOptions = {}): Promise<HomeRestoreResult> {
  if (!Number.isFinite(version)) {
    throw new Error('home_invalid_restore_version');
  }
  const requestPayload = makePayload(payload);
  const endpoint = `${HOME_RESTORE_ENDPOINT}/${encodeURIComponent(String(version))}`;
  const response = await requestWithHandling(() => apiPost<unknown>(endpoint, requestPayload, { signal: options.signal, headers: options.headers }));
  try {
    return normalizeRestoreResponse(response, requestPayload.slug ?? DEFAULT_SLUG);
  } catch (err) {
    pushGlobalToast({ intent: 'error', description: INVALID_RESPONSE_MESSAGE });
    throw err;
  }
}

export const homeApi = {
  getDraft,
  saveDraft,
  publishHome,
  previewHome,
  restoreHome,
};


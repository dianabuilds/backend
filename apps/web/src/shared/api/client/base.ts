import { extractErrorMessage } from '../../utils/errors';
import { csrfHeaders, syncCsrfFromResponse, clearCsrfToken } from './csrf';
import { applyAdminKey, notifyAuthLost } from './auth';
import { pushGlobalToast } from '@shared/ui/toastBus';

const isDev = (import.meta as any)?.env?.DEV;
const apiBase = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;
const isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';

function resolveServerApiBase(): string {
  const explicit = apiBase?.trim();
  if (explicit) return explicit.replace(/\/+$/u, '');
  const envBase =
    typeof process !== 'undefined' && process.env
      ? (process.env.SSR_API_BASE ?? process.env.API_BASE ?? process.env.VITE_API_BASE ?? '').trim()
      : '';
  if (envBase) return envBase.replace(/\/+$/u, '');
  return 'http://127.0.0.1:8000';
}

function buildUrl(path: string): string {
  if (path.startsWith('http')) return path;
  if (!isBrowser) {
    return `${resolveServerApiBase()}${path}`;
  }
  return (isDev ? '' : apiBase || '') + path;
}

function needsCsrf(method: string): boolean {
  const upper = method.toUpperCase();
  return upper !== 'GET' && upper !== 'HEAD';
}

const RATE_LIMIT_MAX_RETRIES = 1;
const MIN_RATE_LIMIT_DELAY_SECONDS = 1;
const MAX_RATE_LIMIT_DELAY_SECONDS = 60;
let lastSecurityToastMessage: string | null = null;
let lastSecurityToastTimestamp = 0;

function emitSecurityToast(description: string, intent: 'success' | 'info' | 'error', durationMs?: number): void {
  if (!description) return;
  const now = Date.now();
  if (lastSecurityToastMessage === description && now - lastSecurityToastTimestamp < 1500) {
    return;
  }
  lastSecurityToastMessage = description;
  lastSecurityToastTimestamp = now;
  pushGlobalToast({ description, intent, durationMs });
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => {
    if (ms <= 0) {
      resolve();
      return;
    }
    setTimeout(resolve, ms);
  });
}

function normalizeRetryDelaySeconds(raw: number | null | undefined): number | null {
  if (raw == null || Number.isNaN(raw)) {
    return null;
  }
  const numeric = Math.ceil(Number(raw));
  if (!Number.isFinite(numeric)) {
    return null;
  }
  if (numeric <= 0) {
    return MIN_RATE_LIMIT_DELAY_SECONDS;
  }
  return Math.min(Math.max(numeric, MIN_RATE_LIMIT_DELAY_SECONDS), MAX_RATE_LIMIT_DELAY_SECONDS);
}

function showRateLimitRetryToast(delaySeconds: number): void {
  const bounded = Math.min(Math.max(delaySeconds, MIN_RATE_LIMIT_DELAY_SECONDS), MAX_RATE_LIMIT_DELAY_SECONDS);
  const durationMs = Math.max(bounded * 1000 + 1500, 5000);
  emitSecurityToast(`Превышен лимит запросов. Повторим через ${bounded} с.`, 'info', durationMs);
}

function showRateLimitFailureToast(): void {
  emitSecurityToast('Превышен лимит запросов. Попробуйте выполнить действие позже.', 'error');
}

const CSRF_ERROR_CODES = new Set(['csrf_failed', 'csrf_mismatch', 'csrf_denied']);

function handleForbiddenError(error: ApiRequestError): void {
  const code = (error.code || '').toLowerCase();
  const body = (error.body || '').toLowerCase();
  if (code === 'missing_token' || body.includes('missing_token')) {
    emitSecurityToast('Сессия истекла. Пожалуйста, войдите снова.', 'error');
    clearCsrfToken();
    return;
  }
  if (CSRF_ERROR_CODES.has(code) || body.includes('csrf')) {
    emitSecurityToast('Защита CSRF отклонила запрос. Обновите страницу и повторите действие.', 'error');
    clearCsrfToken();
    return;
  }
  if (code) {
    emitSecurityToast(error.message || 'Недостаточно прав для выполнения действия.', 'error');
  }
}

export class ApiRequestError extends Error {
  status: number;
  code?: string;
  retryAfter?: number;
  details?: unknown;
  body?: string;
  headers: Record<string, string>;

  constructor(message: string, init: {
    status: number;
    code?: string;
    retryAfter?: number;
    details?: unknown;
    body?: string;
    headers?: Record<string, string>;
  }) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = init.status;
    this.code = init.code;
    this.retryAfter = init.retryAfter;
    this.details = init.details;
    this.body = init.body;
    this.headers = init.headers ?? {};
  }
}

function parseRetryAfter(headerValue: string | null): number | undefined {
  if (!headerValue) {
    return undefined;
  }
  const numeric = Number(headerValue);
  if (!Number.isNaN(numeric)) {
    return numeric >= 0 ? numeric : undefined;
  }
  const dateCandidate = new Date(headerValue);
  if (!Number.isNaN(dateCandidate.getTime())) {
    const diffMs = dateCandidate.getTime() - Date.now();
    if (diffMs > 0) {
      return Math.round(diffMs / 1000);
    }
  }
  return undefined;
}

async function handleResponse(res: Response): Promise<Response> {
  syncCsrfFromResponse(res);
  if (res.ok) return res;

  const headers: Record<string, string> = {};
  res.headers.forEach((value, key) => {
    headers[key] = value;
  });

  let errorBody = '';
  try {
    errorBody = await res.text();
  } catch {
    errorBody = '';
  }

  let parsedBody: unknown;
  if (errorBody) {
    try {
      parsedBody = JSON.parse(errorBody);
    } catch {
      parsedBody = undefined;
    }
  }

  let errorCode: string | undefined;
  let errorMessage: string | undefined;
  let errorDetails: unknown;
  if (isObjectRecord(parsedBody)) {
    if (isObjectRecord(parsedBody.error)) {
      const inner = parsedBody.error as Record<string, unknown>;
      errorCode = pickString(inner.code);
      errorMessage = pickString(inner.message);
      if (inner.extra !== undefined) {
        errorDetails = inner.extra;
      }
    } else {
      errorDetails = parsedBody;
    }
  }

  const fallback = `Request failed (HTTP ${res.status})`;
  const message = errorMessage ?? (errorBody ? extractErrorMessage(errorBody, fallback) : fallback);
  const retryAfter = parseRetryAfter(res.headers.get('Retry-After'));

  const error = new ApiRequestError(message, {
    status: res.status,
    code: errorCode,
    retryAfter,
    details: errorDetails,
    body: errorBody || undefined,
    headers,
  });

  if (res.status === 401 || (res.status === 403 && (errorCode === 'missing_token' || (errorBody && errorBody.includes('missing_token'))))) {
    notifyAuthLost();
  }

  throw error;
}

export type ApiRequestOptions = {
  method?: string;
  headers?: Record<string, string>;
  json?: unknown;
  body?: BodyInit | null;
  omitCredentials?: boolean;
  signal?: AbortSignal;
};

function prepareRequestInit(path: string, options: ApiRequestOptions): RequestInit {
  const method = (options.method || (options.json ? 'POST' : 'GET')).toUpperCase();
  const headers: Record<string, string> = { ...(options.headers || {}) };

  if (options.json !== undefined) {
    if (options.body !== undefined) {
      throw new Error('Pass either `json` or `body`, not both.');
    }
    if (!headers['Content-Type'] && !headers['content-type']) {
      headers['Content-Type'] = 'application/json';
    }
  }

  if (needsCsrf(method)) {
    Object.assign(headers, csrfHeaders());
  }

  applyAdminKey(headers, path);

  const body: BodyInit | null | undefined = options.json !== undefined
    ? JSON.stringify(options.json ?? {})
    : options.body;

  return {
    method,
    credentials: options.omitCredentials ? 'omit' : 'include',
    headers,
    body,
    signal: options.signal,
  };
}

export async function apiRequestRaw(path: string, options: ApiRequestOptions = {}): Promise<Response> {
  for (let attempt = 0; attempt <= RATE_LIMIT_MAX_RETRIES; attempt += 1) {
    const init = prepareRequestInit(path, options);
    const response = await fetch(buildUrl(path), init);
    try {
      return await handleResponse(response);
    } catch (error) {
      if (!(error instanceof ApiRequestError)) {
        throw error;
      }

      if (error.status === 429) {
        const retryDelaySeconds = normalizeRetryDelaySeconds(error.retryAfter);
        if (retryDelaySeconds != null && attempt < RATE_LIMIT_MAX_RETRIES) {
          showRateLimitRetryToast(retryDelaySeconds);
          await delay(retryDelaySeconds * 1000);
          continue;
        }
        showRateLimitFailureToast();
      } else if (error.status === 403) {
        handleForbiddenError(error);
      }

      throw error;
    }
  }
  throw new ApiRequestError('rate_limited', { status: 429 });
}

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  return text ? (JSON.parse(text) as T) : (undefined as T);
}

export async function apiFetch<T = unknown>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const res = await apiRequestRaw(path, options);
  return parseJson<T>(res);
}

export type GetOptions = {
  omitCredentials?: boolean;
  signal?: AbortSignal;
  headers?: Record<string, string>;
};

export async function apiGetWithResponse<T = unknown>(path: string, opts: GetOptions = {}): Promise<{ data: T; response: Response }> {
  const response = await apiRequestRaw(path, {
    method: 'GET',
    headers: opts.headers,
    omitCredentials: opts.omitCredentials,
    signal: opts.signal,
  });
  const data = await parseJson<T>(response);
  return { data, response };
}

export async function apiGet<T = unknown>(path: string, opts: GetOptions = {}): Promise<T> {
  const { data } = await apiGetWithResponse<T>(path, opts);
  return data;
}

export async function apiGetRaw(path: string, opts: GetOptions = {}): Promise<Response> {
  return apiRequestRaw(path, {
    method: 'GET',
    headers: opts.headers,
    omitCredentials: opts.omitCredentials,
    signal: opts.signal,
  });
}

export async function apiPost<T = unknown>(path: string, body: any, opts: ApiRequestOptions = {}): Promise<T> {
  return apiFetch<T>(path, {
    ...opts,
    method: 'POST',
    json: body,
  });
}

export async function apiPatch<T = unknown>(path: string, body: any, opts: ApiRequestOptions = {}): Promise<T> {
  return apiFetch<T>(path, {
    ...opts,
    method: 'PATCH',
    json: body,
  });
}

export async function apiPutWithResponse<T = unknown>(
  path: string,
  body: any,
  opts: ApiRequestOptions = {}
): Promise<{ data: T; response: Response }> {
  const response = await apiRequestRaw(path, {
    ...opts,
    method: 'PUT',
    json: body,
  });
  const data = await parseJson<T>(response);
  return { data, response };
}

export async function apiPut<T = unknown>(path: string, body: any, opts: ApiRequestOptions = {}): Promise<T> {
  const { data } = await apiPutWithResponse<T>(path, body, opts);
  return data;
}

export async function apiDelete<T = unknown>(path: string, opts: ApiRequestOptions = {}): Promise<T> {
  return apiFetch<T>(path, {
    ...opts,
    method: 'DELETE',
  });
}

export { buildUrl };

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

function pickString(value: unknown): string | undefined {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length ? trimmed : undefined;
  }
  return undefined;
}

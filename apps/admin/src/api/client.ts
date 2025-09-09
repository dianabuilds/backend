/* eslint-disable @typescript-eslint/no-explicit-any */
import { getOverrideState, setWarningBanner } from '../shared/hooks';
import { ADMIN_DEV_TOOLS } from '../utils/env';
import { safeLocalStorage, safeSessionStorage } from '../utils/safeStorage';

let csrfTokenMem: string | null = safeSessionStorage.getItem('csrfToken');

// Токен превью-сессии для доступа без авторизации
let previewTokenMem: string | null = safeSessionStorage.getItem('previewToken');

export function setCsrfToken(token: string | null) {
  csrfTokenMem = token || null;
  if (token) safeSessionStorage.setItem('csrfToken', token);
  else safeSessionStorage.removeItem('csrfToken');
}

export function setPreviewToken(token: string | null) {
  previewTokenMem = token || null;
  if (token) safeSessionStorage.setItem('previewToken', token);
  else safeSessionStorage.removeItem('previewToken');
}

// Пытаемся вытащить csrf_token из JSON-ответа и сохранить его
export async function syncCsrfFromResponse(resp: Response): Promise<void> {
  try {
    const cloned = resp.clone();
    const ct = cloned.headers.get('Content-Type') || '';
    if (ct.includes('application/json')) {
      const data = (await cloned.json().catch(() => null)) as Record<string, unknown> | null;
      const token = data && (data.csrf_token || data.csrfToken || data.csrf);
      if (typeof token === 'string' && token) setCsrfToken(token);
    }
  } catch {
    // игнорируем
  }
}

function getCsrfToken(): string {
  // Пытаемся найти токен в наиболее распространённых именах cookie
  const cookies = document.cookie || '';
  const tryNames = ['XSRF-TOKEN', 'xsrf-token', 'csrf_token', 'csrftoken', 'CSRF-TOKEN'];
  for (const name of tryNames) {
    const re = new RegExp(`(?:^|;\\s*)${name}=([^;]+)`);
    const m = cookies.match(re);
    if (m) return decodeURIComponent(m[1]);
  }
  return csrfTokenMem || '';
}

function getCookie(name: string): string {
  try {
    const m = (document.cookie || '').match(new RegExp(`(?:^|;\\s*)${name}=([^;]+)`));
    return m ? decodeURIComponent(m[1]) : '';
  } catch {
    return '';
  }
}

/**
 * Низкоуровневый fetch с поддержкой cookie‑сессии,
 * авторефрешем access/CSRF на 401 и синхронизацией CSRF.
 * Поддерживает таймаут через AbortController (VITE_API_TIMEOUT_MS или 15000 мс по умолчанию).
 */
export async function apiFetch(
  input: RequestInfo,
  init: RequestInit = {},
  _retry = true,
): Promise<Response> {
  const rest = init as RequestInit;
  const method = (rest.method || 'GET').toUpperCase();
  const headers: Record<string, string> = {
    ...(rest.headers as Record<string, string> | undefined),
  };

  if (ADMIN_DEV_TOOLS) {
    const existing = headers['X-Feature-Flags'];
    headers['X-Feature-Flags'] = existing ? `${existing},ADMIN_DEV_TOOLS` : 'ADMIN_DEV_TOOLS';
  }

  // Явно запрашиваем JSON, чтобы сервер мог отличать API-запросы от HTML SPA
  if (!Object.keys(headers).some((k) => k.toLowerCase() === 'accept')) {
    headers['Accept'] = 'application/json';
  }

  // Распознаём /auth/*, чтобы избежать лишних заголовков и preflight
  const pathStr = typeof input === 'string' ? input : input instanceof Request ? input.url : '';
  const isAuthCall = pathStr.startsWith('/auth/');
  const isSafeMethod = method === 'GET' || method === 'HEAD';

  // Для безопасных методов (GET/HEAD) не отправляем CSRF. Для /auth/* — тоже не отправляем.
  const csrf = getCsrfToken();
  if (csrf && !isSafeMethod && !isAuthCall) {
    headers['X-CSRF-Token'] = csrf;
  }

  if (previewTokenMem) {
    headers['X-Preview-Token'] = previewTokenMem;
  }

  // Dev helper: attach Bearer from access_token cookie to support cross-origin requests
  // when SameSite=Lax prevents browsers from sending cookies with XHR/fetch.
  // Skip for /auth/* endpoints and do not override explicit Authorization.
  if (!isAuthCall && !headers['Authorization']) {
    const at = getCookie('access_token');
    if (at) headers['Authorization'] = `Bearer ${at}`;
  }

  const override = getOverrideState();
  if (override.enabled) {
    headers['X-Admin-Override'] = 'on';
    if (override.reason) {
      headers['X-Override-Reason'] = override.reason;
    }
  }

  // Формируем конечный URL:
  // - Если задан VITE_API_BASE — используем его (например, https://api.example.com)
  // - Иначе: если dev‑сервер фронта на 5173–5176, по умолчанию шлём на http://<hostname>:8000
  // - В противном случае оставляем относительный путь (для прод/одного домена)
  const toUrl = (u: RequestInfo): RequestInfo => {
    if (typeof u !== 'string') return u;
    if (!u.startsWith('/')) return u;
    try {
      const envBase = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env
        ?.VITE_API_BASE;
      if (envBase) {
        return envBase.replace(/\/+$/, '') + u;
      }
    } catch {
      // ignore
    }
    try {
      const loc = window.location;
      const port = String(loc.port || '');
      const isViteDev = /^517[3-6]$/.test(port);
      if (isViteDev) {
        return 'http://' + loc.hostname + ':8000' + u;
      }
    } catch {
      // ignore
    }
    return u;
  };

  // Таймаут запроса: можно задать VITE_API_TIMEOUT_MS, иначе 15с для обычных запросов и 60с для /auth/*
  const envTimeout = Number(
    (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env
      ?.VITE_API_TIMEOUT_MS || 0,
  );
  const defaultTimeout = envTimeout > 0 ? envTimeout : isAuthCall ? 60000 : 15000;
  const optTimeout = (init as RequestOptions).timeoutMs;
  const timeoutMs = Number.isFinite(optTimeout as number)
    ? Math.max(0, Number(optTimeout))
    : defaultTimeout;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let resp: Response;
  try {
    resp = await fetch(toUrl(input), {
      ...rest,
      method,
      headers,
      credentials: 'include',
      signal: controller.signal,
    });
  } catch (e: any) {
    clearTimeout(timer);
    // Нормализуем AbortError в предсказуемое сообщение
    if (
      e &&
      (e.name === 'AbortError' ||
        String(e.message || '')
          .toLowerCase()
          .includes('aborted'))
    ) {
      const err = new Error('RequestTimeout');
      (err as Error & { cause?: unknown }).cause = e;
      throw err;
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }

  // Единственная попытка рефреша при 401 (кроме вызовов самого /auth/refresh)
  const isRefreshCall = typeof input === 'string' && input.startsWith('/auth/refresh');
  if (resp.status === 401 && _retry && !isRefreshCall) {
    try {
      const refreshHeaders: Record<string, string> = {};
      const csrfForRefresh = getCsrfToken();
      if (csrfForRefresh) refreshHeaders['X-CSRF-Token'] = csrfForRefresh;

      // Отдельный контроллер/таймаут для refresh, чтобы не зависеть от уже сработавшего abort
      const refreshCtl = new AbortController();
      const refreshTimeout = setTimeout(() => refreshCtl.abort(), 15000);
      let refresh: Response;
      try {
        refresh = await fetch(toUrl('/auth/refresh'), {
          method: 'POST',
          headers: refreshHeaders,
          credentials: 'include',
          signal: refreshCtl.signal,
        });
      } finally {
        clearTimeout(refreshTimeout);
      }
      if (refresh.ok) {
        await syncCsrfFromResponse(refresh);
        return apiFetch(input, init, false);
      }
    } catch {
      // игнорируем — вернём исходный 401
    }
  }

  // Единоразовая синхронизация CSRF из ответа (если сервер выдал новый токен)
  try {
    await syncCsrfFromResponse(resp);
  } catch {
    // no-op
  }
  try {
    const cloned = resp.clone();
    const ct = cloned.headers.get('Content-Type') || '';
    if (ct.includes('application/json')) {
      const data = (await cloned.json().catch(() => null)) as Record<string, unknown> | null;
      const banner =
        data && typeof data.warning_banner === 'string'
          ? (data.warning_banner as string)
          : undefined;
      if (typeof banner === 'string' && banner) setWarningBanner(banner);
    }
  } catch {
    // ignore
  }

  return resp;
}

/**
 * Высокоуровневые хелперы API: парсинг JSON, поддержка ETag, единый ответ.
 */
export interface RequestOptions extends RequestInit {
  etag?: string | null;
  acceptNotModified?: boolean;
  json?: unknown;
  timeoutMs?: number;
  retry?: number;
}

export interface ApiResponse<T = unknown> {
  ok: boolean;
  status: number;
  etag?: string | null;
  data?: T;
  response: Response;
}

export class ApiError<T = any> extends Error {
  status: number;
  code?: string;
  detail?: T;
  headers?: Headers;
  constructor(message: string, status: number, code?: string, detail?: T, headers?: Headers) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.detail = detail;
    this.headers = headers;
  }
}

async function request<T = unknown>(
  url: string,
  opts: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string> | undefined),
  };
  if (opts.json !== undefined) headers['Content-Type'] = 'application/json';
  if (opts.etag) headers['If-None-Match'] = opts.etag;

  let attempts = 0;
  let resp: Response;
  while (true) {
    try {
      resp = await apiFetch(url, {
        ...opts,
        headers,
        body: opts.json !== undefined ? JSON.stringify(opts.json) : opts.body,
      });
      break;
    } catch (e: any) {
      attempts += 1;
      if (attempts <= (opts.retry || 0)) {
        continue;
      }
      if (e && e.message === 'RequestTimeout') {
        throw new ApiError(
          'Превышено время ожидания запроса. Проверьте соединение или повторите попытку позже.',
          0,
          'REQUEST_TIMEOUT',
        );
      }
      throw e;
    }
  }
  const etag = resp.headers.get('ETag');

  if (resp.status === 304 && opts.acceptNotModified) {
    return { ok: true, status: resp.status, etag, response: resp };
  }

  const contentType = resp.headers.get('Content-Type') || '';
  let data: any = undefined;
  if (contentType.includes('application/json')) {
    try {
      data = await resp.json();
    } catch {
      data = undefined;
    }
  } else {
    const t = await resp.text();
    try {
      data = t ? JSON.parse(t) : undefined;
    } catch {
      data = t;
    }
  }

  if (!resp.ok) {
    // Пытаемся достать message/code/detail из ответа
    const detail = (data && (data.detail ?? data.error?.detail)) || undefined;
    const code =
      (typeof detail === 'object' && detail?.code) || data?.code || data?.error?.code || undefined;
    let msg =
      (typeof detail === 'object' && detail?.message) ||
      data?.message ||
      data?.error?.message ||
      resp.statusText ||
      'Request failed';
    switch (resp.status) {
      case 405:
        msg = 'Метод не поддерживается';
        break;
      case 422:
        msg = 'Ошибка валидации';
        break;
      case 500:
        msg = 'Внутренняя ошибка сервера';
        break;
    }
    throw new ApiError(
      String(msg),
      resp.status,
      typeof code === 'string' ? code : undefined,
      detail,
      resp.headers,
    );
  }

  return { ok: true, status: resp.status, etag, data: data as T, response: resp };
}

// Простое кеширование ответов по ETag для GET-запросов
const responseCache = new Map<string, { etag: string; data: unknown }>();

export async function cachedGet<T = unknown>(
  url: string,
  opts: RequestOptions = {},
): Promise<ApiResponse<T>> {
  const cached = responseCache.get(url);
  const res = await request<T>(url, {
    ...opts,
    etag: opts.etag ?? cached?.etag ?? null,
    acceptNotModified: true,
  });
  if (res.status === 304 && cached) {
    return {
      ok: true,
      status: 200,
      etag: cached.etag,
      data: cached.data as T,
      response: res.response,
    };
  }
  if (res.etag && res.data !== undefined) {
    responseCache.set(url, { etag: res.etag, data: res.data });
  }
  return res;
}

export const get = <T = unknown>(url: string, opts?: RequestOptions): Promise<ApiResponse<T>> =>
  request<T>(url, { ...opts, method: 'GET' });

export const post = <TReq = unknown, TRes = unknown>(
  url: string,
  json?: TReq,
  opts?: RequestOptions,
): Promise<ApiResponse<TRes>> => request<TRes>(url, { ...opts, method: 'POST', json });

export const put = <TReq = unknown, TRes = unknown>(
  url: string,
  json?: TReq,
  opts?: RequestOptions,
): Promise<ApiResponse<TRes>> => request<TRes>(url, { ...opts, method: 'PUT', json });

export const patch = <TReq = unknown, TRes = unknown>(
  url: string,
  json?: TReq,
  opts?: RequestOptions,
): Promise<ApiResponse<TRes>> => request<TRes>(url, { ...opts, method: 'PATCH', json });

export const del = <T = unknown>(url: string, opts?: RequestOptions): Promise<ApiResponse<T>> =>
  request<T>(url, { ...opts, method: 'DELETE' });

export const api = {
  request,
  get,
  cachedGet,
  post,
  put,
  patch,
  del,
  delete: del,
};

export { del as delete };

// Типы и API для сервер‑драйв меню админки (с ETag кэшем)
export interface AdminMenuItem {
  id: string;
  label: string;
  path?: string | null;
  icon?: string | null;
  order?: number | null;
  children?: AdminMenuItem[] | null;
  external?: boolean | null;
  divider?: boolean | null;
  roles?: string[] | null;
  featureFlag?: string | null;
  hidden?: boolean | null;
}

export interface AdminMenuResponse {
  items: AdminMenuItem[];
  version?: string | number | null;
}

const MENU_CACHE_VERSION = 'v4'; // bump cache to invalidate stale ordered menu
const MENU_ETAG_KEY = `adminMenuEtag:${MENU_CACHE_VERSION}`;
const MENU_CACHE_KEY = `adminMenuCache:${MENU_CACHE_VERSION}`;

export async function getAdminMenu(): Promise<AdminMenuResponse> {
  const etag = safeLocalStorage.getItem(MENU_ETAG_KEY);
  const cached = safeLocalStorage.getItem(MENU_CACHE_KEY);
  try {
    const res = await api.cachedGet<AdminMenuResponse>('/admin/menu', { etag });
    if (res.status === 304 && cached) {
      return JSON.parse(cached) as AdminMenuResponse;
    }
    if (res.etag) safeLocalStorage.setItem(MENU_ETAG_KEY, res.etag);
    if (res.data) safeLocalStorage.setItem(MENU_CACHE_KEY, JSON.stringify(res.data));
    return (res.data || (cached && JSON.parse(cached))) as AdminMenuResponse;
  } catch (e) {
    if (cached) return JSON.parse(cached) as AdminMenuResponse;
    throw e;
  }
}

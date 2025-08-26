/* eslint-disable @typescript-eslint/no-explicit-any */
import { ADMIN_DEV_TOOLS } from "../utils/env";
import { safeLocalStorage, safeSessionStorage } from "../utils/safeStorage";

let csrfTokenMem: string | null = safeSessionStorage.getItem("csrfToken");

// Храним access_token для Bearer, если cookie недоступны/не прикрепились
let accessTokenMem: string | null = safeSessionStorage.getItem("accessToken");

// Храним текущий workspace_id для админских запросов
let workspaceIdMem: string | null = safeLocalStorage.getItem("workspaceId");

// Токен превью-сессии для доступа без авторизации
let previewTokenMem: string | null = safeSessionStorage.getItem("previewToken");

export function setCsrfToken(token: string | null) {
  csrfTokenMem = token || null;
  if (token) safeSessionStorage.setItem("csrfToken", token);
  else safeSessionStorage.removeItem("csrfToken");
}

export function setAccessToken(token: string | null) {
  accessTokenMem = token || null;
  if (token) safeSessionStorage.setItem("accessToken", token);
  else safeSessionStorage.removeItem("accessToken");
}

export function setWorkspaceId(id: string | null) {
  workspaceIdMem = id || null;
  if (id) safeLocalStorage.setItem("workspaceId", id);
  else safeLocalStorage.removeItem("workspaceId");
}

export function setPreviewToken(token: string | null) {
  previewTokenMem = token || null;
  if (token) safeSessionStorage.setItem("previewToken", token);
  else safeSessionStorage.removeItem("previewToken");
}

function applyWorkspace(u: string, method?: string): string {
  if (!u.startsWith("/")) return u;
  if (!workspaceIdMem) {
    if (method === "POST" || method === "PUT") {
      throw new Error("workspaceId is required for write requests");
    }
    return u;
  }
  try {
    const url = new URL(u, "http://d");
    if (!url.searchParams.get("workspace_id")) {
      url.searchParams.set("workspace_id", workspaceIdMem);
    }
    return url.pathname + url.search;
  } catch {
    return u;
  }
}

// Пытаемся вытащить csrf_token из JSON-ответа и сохранить его
export async function syncCsrfFromResponse(resp: Response): Promise<void> {
  try {
    const cloned = resp.clone();
    const ct = cloned.headers.get("Content-Type") || "";
    if (ct.includes("application/json")) {
      const data = (await cloned.json().catch(() => null)) as
        | Record<string, unknown>
        | null;
      const token = data && (data.csrf_token || data.csrfToken || data.csrf);
      if (typeof token === "string" && token) setCsrfToken(token);
    }
  } catch {
    // игнорируем
  }
}

function getCsrfToken(): string {
  const match = document.cookie.match(/XSRF-TOKEN=([^;]+)/);
  if (match) return decodeURIComponent(match[1]);
  return csrfTokenMem || "";
}

// Достаём access_token: сначала из cookie, затем из sessionStorage
function getAccessToken(): string {
  const m = document.cookie.match(/(?:^|;\s*)access_token=([^;]+)/);
  if (m) return decodeURIComponent(m[1]);
  return accessTokenMem || "";
}

/**
 * Низкоуровневый fetch с поддержкой cookie‑сессии,
 * авторефрешем access/CSRF на 401 и синхронизацией CSRF.
 * Поддерживает таймаут через AbortController (VITE_API_TIMEOUT_MS или 15000 мс по умолчанию).
 */
export async function apiFetch(
  input: RequestInfo,
  init: RequestInit & { skipAuth?: boolean } = {},
  _retry = true,
): Promise<Response> {
  const { skipAuth, ...rest } = init as RequestInit & { skipAuth?: boolean };
  const method = (rest.method || "GET").toUpperCase();
  const headers: Record<string, string> = {
    ...(rest.headers as Record<string, string> | undefined),
  };

  if (ADMIN_DEV_TOOLS) {
    const existing = headers["X-Feature-Flags"];
    headers["X-Feature-Flags"] = existing
      ? `${existing},ADMIN_DEV_TOOLS`
      : "ADMIN_DEV_TOOLS";
  }

  // Явно запрашиваем JSON, чтобы сервер мог отличать API-запросы от HTML SPA
  if (!Object.keys(headers).some((k) => k.toLowerCase() === "accept")) {
    headers["Accept"] = "application/json";
  }

  // Распознаём /auth/*, чтобы избежать лишних заголовков и preflight
  const pathStr =
    typeof input === "string" ? input : input instanceof Request ? input.url : "";
  const isAuthCall = typeof pathStr === "string" && pathStr.startsWith("/auth/");
  const isSafeMethod = method === "GET" || method === "HEAD";

  // Для безопасных методов (GET/HEAD) не отправляем CSRF. Для /auth/* — тоже не отправляем.
  const csrf = getCsrfToken();
  if (csrf && !isSafeMethod && !isAuthCall) {
    headers["X-CSRF-Token"] = csrf;
  }

  // Если явно не передали Authorization — берём токен из cookie/хранилища,
  // но НИКОГДА не добавляем его автоматически для /auth/*, чтобы избежать preflight/конфликтов.
  const lowerCaseHeaders = Object.fromEntries(Object.entries(headers).map(([k, v]) => [k.toLowerCase(), v]));
  if (!skipAuth && !("authorization" in lowerCaseHeaders) && !isAuthCall) {
    const at = getAccessToken();
    const hasCookieAccess =
      typeof document !== "undefined" && /(?:^|;\s*)access_token=/.test(document.cookie || "");
    if (at && (!isSafeMethod || !hasCookieAccess)) {
      headers["Authorization"] = `Bearer ${at}`;
    }
  }

  if (previewTokenMem) {
    headers["X-Preview-Token"] = previewTokenMem;
  }

  // Формируем конечный URL:
  // - Если задан VITE_API_BASE — используем его (например, https://api.example.com)
  // - Иначе: если dev‑сервер фронта на 5173–5176, по умолчанию шлём на http://<hostname>:8000
  // - В противном случае оставляем относительный путь (для прод/одного домена)
  const toUrl = (u: RequestInfo): RequestInfo => {
    if (typeof u !== "string") return u;
    if (!u.startsWith("/")) return u;
    u = applyWorkspace(u, method);
    try {
      const envBase = (
        import.meta as ImportMeta & { env?: Record<string, string | undefined> }
      ).env?.VITE_API_BASE;
      if (envBase) {
        return envBase.replace(/\/+$/, "") + u;
      }
    } catch {
      // ignore
    }
    try {
      const loc = window.location;
      const port = String(loc.port || "");
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
    (
      (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env
        ?.VITE_API_TIMEOUT_MS || 0
    ),
  );
  const defaultTimeout = envTimeout > 0 ? envTimeout : (isAuthCall ? 60000 : 15000);
  const timeoutMs =
    typeof (init as RequestOptions).timeoutMs === "number"
      ? Math.max(0, Number((init as RequestOptions).timeoutMs))
      : defaultTimeout;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let resp: Response;
  try {
    resp = await fetch(toUrl(input), {
      ...rest,
      method,
      headers,
      credentials: "include",
      signal: controller.signal,
    });
  } catch (e: any) {
    clearTimeout(timer);
    // Нормализуем AbortError в предсказуемое сообщение
    if (e && (e.name === "AbortError" || String(e.message || "").toLowerCase().includes("aborted"))) {
      const err = new Error("RequestTimeout");
      (err as Error & { cause?: unknown }).cause = e;
      throw err;
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }

  // Единственная попытка рефреша при 401 (кроме вызовов самого /auth/refresh)
  const isRefreshCall = typeof input === "string" && input.startsWith("/auth/refresh");
  if (resp.status === 401 && _retry && !isRefreshCall) {
    try {
      const refreshHeaders: Record<string, string> = {};
      const csrfForRefresh = getCsrfToken();
      if (csrfForRefresh) refreshHeaders["X-CSRF-Token"] = csrfForRefresh;

      // Отдельный контроллер/таймаут для refresh, чтобы не зависеть от уже сработавшего abort
      const refreshCtl = new AbortController();
      const refreshTimeout = setTimeout(() => refreshCtl.abort(), 15000);
      let refresh: Response;
      try {
        refresh = await fetch(toUrl("/auth/refresh"), {
          method: "POST",
          headers: refreshHeaders,
          credentials: "include",
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
  constructor(
    message: string,
    status: number,
    code?: string,
    detail?: T,
    headers?: Headers,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.detail = detail;
    this.headers = headers;
  }
}

async function request<T = unknown>(url: string, opts: RequestOptions = {}): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string> | undefined),
  };
  if (opts.json !== undefined) headers["Content-Type"] = "application/json";
  if (opts.etag) headers["If-None-Match"] = opts.etag;

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
      if (e && e.message === "RequestTimeout") {
        throw new ApiError(
          "Превышено время ожидания запроса. Проверьте соединение или повторите попытку позже.",
          0,
          "REQUEST_TIMEOUT",
        );
      }
      throw e;
    }
  }
  const etag = resp.headers.get("ETag");

  if (resp.status === 304 && opts.acceptNotModified) {
    return { ok: true, status: resp.status, etag, response: resp };
  }

  const contentType = resp.headers.get("Content-Type") || "";
  let data: any = undefined;
  if (contentType.includes("application/json")) {
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
      (typeof detail === "object" && detail?.code) ||
      data?.code ||
      data?.error?.code ||
      undefined;
    const msg =
      (typeof detail === "object" && detail?.message) ||
      data?.message ||
      data?.error?.message ||
      resp.statusText ||
      "Request failed";
    throw new ApiError(
      String(msg),
      resp.status,
      typeof code === "string" ? code : undefined,
      detail,
      resp.headers,
    );
  }

  return { ok: true, status: resp.status, etag, data: data as T, response: resp };
}

export const get = <T = unknown>(
  url: string,
  opts?: RequestOptions,
): Promise<ApiResponse<T>> => request<T>(url, { ...opts, method: "GET" });

export const post = <TReq = unknown, TRes = unknown>(
  url: string,
  json?: TReq,
  opts?: RequestOptions,
): Promise<ApiResponse<TRes>> => request<TRes>(url, { ...opts, method: "POST", json });

export const put = <TReq = unknown, TRes = unknown>(
  url: string,
  json?: TReq,
  opts?: RequestOptions,
): Promise<ApiResponse<TRes>> => request<TRes>(url, { ...opts, method: "PUT", json });

export const patch = <TReq = unknown, TRes = unknown>(
  url: string,
  json?: TReq,
  opts?: RequestOptions,
): Promise<ApiResponse<TRes>> => request<TRes>(url, { ...opts, method: "PATCH", json });

export const del = <T = unknown>(
  url: string,
  opts?: RequestOptions,
): Promise<ApiResponse<T>> => request<T>(url, { ...opts, method: "DELETE" });

export const api = {
  request,
  get,
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
}

export interface AdminMenuResponse {
  items: AdminMenuItem[];
  version?: string | number | null;
}

const MENU_CACHE_VERSION = "v4"; // bump cache to invalidate stale ordered menu
const MENU_ETAG_KEY = `adminMenuEtag:${MENU_CACHE_VERSION}`;
const MENU_CACHE_KEY = `adminMenuCache:${MENU_CACHE_VERSION}`;

export async function getAdminMenu(): Promise<AdminMenuResponse> {
  const etag = safeLocalStorage.getItem(MENU_ETAG_KEY);
  try {
    const res = await api.get<AdminMenuResponse>("/admin/menu", { etag, acceptNotModified: true });
    if (res.status === 304) {
      const cached = safeLocalStorage.getItem(MENU_CACHE_KEY);
      if (cached) return JSON.parse(cached) as AdminMenuResponse;
      const res2 = await api.get<AdminMenuResponse>("/admin/menu");
      if (res2.etag) safeLocalStorage.setItem(MENU_ETAG_KEY, res2.etag);
      if (res2.data) safeLocalStorage.setItem(MENU_CACHE_KEY, JSON.stringify(res2.data));
      return res2.data as AdminMenuResponse;
    }
    if (res.etag) safeLocalStorage.setItem(MENU_ETAG_KEY, res.etag);
    if (res.data) safeLocalStorage.setItem(MENU_CACHE_KEY, JSON.stringify(res.data));
    return res.data as AdminMenuResponse;
  } catch (e) {
    const cached = safeLocalStorage.getItem(MENU_CACHE_KEY);
    if (cached) return JSON.parse(cached) as AdminMenuResponse;
    throw e;
  }
}


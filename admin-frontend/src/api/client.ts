let csrfTokenMem: string | null =
  typeof sessionStorage !== "undefined" ? sessionStorage.getItem("csrfToken") : null;

// Храним access_token для Bearer, если cookie недоступны/не прикрепились
let accessTokenMem: string | null =
  typeof sessionStorage !== "undefined" ? sessionStorage.getItem("accessToken") : null;

export function setCsrfToken(token: string | null) {
  csrfTokenMem = token || null;
  if (typeof sessionStorage !== "undefined") {
    if (token) sessionStorage.setItem("csrfToken", token);
    else sessionStorage.removeItem("csrfToken");
  }
}

export function setAccessToken(token: string | null) {
  accessTokenMem = token || null;
  if (typeof sessionStorage !== "undefined") {
    if (token) sessionStorage.setItem("accessToken", token);
    else sessionStorage.removeItem("accessToken");
  }
}

// Пытаемся вытащить csrf_token из JSON-ответа и сохранить его
export async function syncCsrfFromResponse(resp: Response): Promise<void> {
  try {
    const cloned = resp.clone();
    const ct = cloned.headers.get("Content-Type") || "";
    if (ct.includes("application/json")) {
      const data = await cloned.json().catch(() => null) as any;
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
 */
export async function apiFetch(
  input: RequestInfo,
  init: RequestInit = {},
  _retry = true,
): Promise<Response> {
  const method = (init.method || "GET").toUpperCase();
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string> | undefined),
  };

  // Явно запрашиваем JSON, чтобы сервер мог отличать API-запросы от HTML SPA
  if (!Object.keys(headers).some((k) => k.toLowerCase() === "accept")) {
    headers["Accept"] = "application/json";
  }

  // Для безопасных методов (GET/HEAD) не отправляем CSRF, чтобы не вызывать preflight.
  const isSafeMethod = method === "GET" || method === "HEAD";
  const csrf = getCsrfToken();
  if (csrf && !isSafeMethod) {
    headers["X-CSRF-Token"] = csrf;
  }

  // Если явно не передали Authorization — берём токен из cookie/хранилища.
  // Для безопасных запросов, если уже есть cookie access_token, НЕ добавляем Authorization,
  // чтобы не триггерить CORS preflight. Для небезопасных — добавляем.
  const lowerCaseHeaders = Object.fromEntries(Object.entries(headers).map(([k, v]) => [k.toLowerCase(), v]));
  if (!("authorization" in lowerCaseHeaders)) {
    const at = getAccessToken();
    const hasCookieAccess =
      typeof document !== "undefined" && /(?:^|;\s*)access_token=/.test(document.cookie || "");
    if (at && (!isSafeMethod || !hasCookieAccess)) {
      headers["Authorization"] = `Bearer ${at}`;
    }
  }

  // В dev (порт 5173) или при VITE_API_BASE направляем запросы на стабильный backend origin
  const toUrl = (u: RequestInfo): RequestInfo => {
    if (typeof u !== "string") return u;
    if (!u.startsWith("/")) return u;
    let base = "";
    try {
      const envBase = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;
      if (envBase) base = envBase;
      else if (typeof window !== "undefined" && window.location && window.location.port === "5173") {
        base = `${window.location.protocol}//${window.location.hostname}:8000`;
      }
    } catch {
      // ignore
    }
    return base ? (base + u) : u;
  };

  const resp = await fetch(toUrl(input), {
    ...init,
    method,
    headers,
    credentials: "include",
  });

  // Единственная попытка рефреша при 401 (кроме вызовов самого /auth/refresh)
  const isRefreshCall = typeof input === "string" && input.startsWith("/auth/refresh");
  if (resp.status === 401 && _retry && !isRefreshCall) {
    try {
      const refreshHeaders: Record<string, string> = {};
      const csrfForRefresh = getCsrfToken();
      if (csrfForRefresh) refreshHeaders["X-CSRF-Token"] = csrfForRefresh;

      const refresh = await fetch(toUrl("/auth/refresh"), {
        method: "POST",
        headers: refreshHeaders,
        credentials: "include",
      });
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
}

export interface ApiResponse<T = unknown> {
  ok: boolean;
  status: number;
  etag?: string | null;
  data?: T;
  response: Response;
}

async function request<T = unknown>(url: string, opts: RequestOptions = {}): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string> | undefined),
  };
  if (opts.json !== undefined) headers["Content-Type"] = "application/json";
  if (opts.etag) headers["If-None-Match"] = opts.etag;

  const resp = await apiFetch(url, {
    ...opts,
    headers,
    body: opts.json !== undefined ? JSON.stringify(opts.json) : opts.body,
  });
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
      data = t as any;
    }
  }

  if (!resp.ok) {
    // Прокидываем ошибку наверх, чтобы страницы могли показать тост/сообщение
    const msg = (data && (data.message || data.error?.message)) || resp.statusText;
    throw new Error(typeof msg === "string" ? msg : "Request failed");
  }

  return { ok: true, status: resp.status, etag, data: data as T, response: resp };
}

export const api = {
  request,
  get: <T = unknown>(url: string, opts?: RequestOptions) => request<T>(url, { ...opts, method: "GET" }),
  post: <T = unknown>(url: string, json?: unknown, opts?: RequestOptions) => request<T>(url, { ...opts, method: "POST", json }),
  patch: <T = unknown>(url: string, json?: unknown, opts?: RequestOptions) => request<T>(url, { ...opts, method: "PATCH", json }),
  del:  <T = unknown>(url: string, opts?: RequestOptions) => request<T>(url, { ...opts, method: "DELETE" }),
};

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
}

export interface AdminMenuResponse {
  items: AdminMenuItem[];
  version?: string | number | null;
}

const MENU_ETAG_KEY = "adminMenuEtag";
const MENU_CACHE_KEY = "adminMenuCache";

export async function getAdminMenu(): Promise<AdminMenuResponse> {
  const etag = typeof localStorage !== "undefined" ? localStorage.getItem(MENU_ETAG_KEY) : null;
  try {
    const res = await api.get<AdminMenuResponse>("/admin/menu", { etag, acceptNotModified: true });
    if (res.status === 304) {
      const cached = typeof localStorage !== "undefined" ? localStorage.getItem(MENU_CACHE_KEY) : null;
      if (cached) return JSON.parse(cached) as AdminMenuResponse;
      const res2 = await api.get<AdminMenuResponse>("/admin/menu");
      if (res2.etag && typeof localStorage !== "undefined") localStorage.setItem(MENU_ETAG_KEY, res2.etag);
      if (res2.data && typeof localStorage !== "undefined") localStorage.setItem(MENU_CACHE_KEY, JSON.stringify(res2.data));
      return res2.data as AdminMenuResponse;
    }
    if (res.etag && typeof localStorage !== "undefined") localStorage.setItem(MENU_ETAG_KEY, res.etag);
    if (res.data && typeof localStorage !== "undefined") localStorage.setItem(MENU_CACHE_KEY, JSON.stringify(res.data));
    return res.data as AdminMenuResponse;
  } catch (e) {
    const cached = typeof localStorage !== "undefined" ? localStorage.getItem(MENU_CACHE_KEY) : null;
    if (cached) return JSON.parse(cached) as AdminMenuResponse;
    throw e;
  }
}


function getCsrfToken(): string {
  const match = document.cookie.match(/XSRF-TOKEN=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

/**
 * Низкоуровневый fetch с поддержкой Authorization (Bearer из localStorage)
 * и CSRF для небезопасных методов. НИКАКИХ автологаутов здесь — 401
 * пробрасывается выше и решается на уровне вызывающего кода.
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

  // Подставляем Bearer-токен из localStorage (совместимо с текущим бэкендом)
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Для небезопасных методов добавляем CSRF заголовок (double-submit)
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    headers["X-CSRF-Token"] = getCsrfToken();
  }

  const resp = await fetch(input, {
    ...init,
    method,
    headers,
    credentials: "include",
  });

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


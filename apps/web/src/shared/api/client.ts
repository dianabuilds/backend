
export function getCookie(nameContains: string): string | null {
  try {
    const cookies = document.cookie.split(';').map((c) => c.trim());
    const found = cookies.find((c) => c.toLowerCase().startsWith(nameContains.toLowerCase()));
    if (!found) return null;
    const idx = found.indexOf('=');
    return idx >= 0 ? decodeURIComponent(found.slice(idx + 1)) : null;
  } catch {
    return null;
  }
}

const CSRF_COOKIE = 'XSRF-TOKEN';
const CSRF_STORAGE_KEY = 'auth.csrf_token';
let csrfTokenCache: string | null = null;

function rememberCsrfToken(token: string | null | undefined): string | null {
  const normalized = typeof token === 'string' && token.trim() ? token.trim() : null;
  csrfTokenCache = normalized;
  try {
    if (typeof sessionStorage !== 'undefined') {
      if (normalized) sessionStorage.setItem(CSRF_STORAGE_KEY, normalized);
      else sessionStorage.removeItem(CSRF_STORAGE_KEY);
    }
  } catch {}
  try {
    if (typeof localStorage !== 'undefined') {
      if (normalized) localStorage.setItem(CSRF_STORAGE_KEY, normalized);
      else localStorage.removeItem(CSRF_STORAGE_KEY);
    }
  } catch {}
  return csrfTokenCache;
}

function loadStoredCsrfToken(): string | null {
  try {
    if (typeof sessionStorage !== 'undefined') {
      const value = sessionStorage.getItem(CSRF_STORAGE_KEY);
      if (value && value.length) return value;
    }
  } catch {}
  try {
    if (typeof localStorage !== 'undefined') {
      const value = localStorage.getItem(CSRF_STORAGE_KEY);
      if (value && value.length) return value;
    }
  } catch {}
  return null;
}

csrfTokenCache = loadStoredCsrfToken();

function parseCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const raw = document.cookie || '';
  const parts = raw.split(';');
  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    if (key === name) {
      const value = trimmed.slice(eq + 1);
      try {
        return decodeURIComponent(value);
      } catch {
        return value;
      }
    }
  }
  return null;
}

function csrfHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  const token = csrfTokenCache || parseCookie(CSRF_COOKIE);
  if (token) headers['X-CSRF-Token'] = token;
  return headers;
}

function syncCsrfFromResponse(res: Response) {
  const headerToken =
    res.headers.get('X-CSRF-Token') || res.headers.get('x-csrf-token') || res.headers.get('x-xsrf-token');
  if (headerToken) rememberCsrfToken(headerToken);
  if (typeof document !== 'undefined') {
    try {
      const domToken = parseCookie(CSRF_COOKIE);
      if (domToken && domToken !== csrfTokenCache) rememberCsrfToken(domToken);
    } catch {}
  }
}

type AuthLostHandler = () => void;
let authLostHandler: AuthLostHandler | null = null;

export function setAuthLostHandler(handler?: AuthLostHandler) {
  authLostHandler = handler || null;
}

function notifyAuthLost() {
  if (!authLostHandler) return;
  try {
    authLostHandler();
  } catch {}
}

const isDev = (import.meta as any)?.env?.DEV;
const base = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;

export function setCsrfToken(token?: string | null) {
  rememberCsrfToken(token ?? null);
}

export function clearCsrfToken() {
  rememberCsrfToken(null);
}

export function primeCsrfFromCookies() {
  const token = parseCookie(CSRF_COOKIE);
  if (token) rememberCsrfToken(token);
}

export function decodeJwt<T = any>(token: string | undefined | null): T | null {
  try {
    if (!token) return null;
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const json = atob(parts[1].replace(/-/g, '+').replace(/_/g, '/'));
    return JSON.parse(decodeURIComponent(escape(json)));
  } catch {
    return null;
  }
}

function url(u: string) {
  if (u.startsWith('http')) return u;
  return (isDev ? '' : base || '') + u;
}

function maybeWithAdminKey(headers: Record<string, string>, u: string) {
  try {
    const env: any = (import.meta as any)?.env || {};
    const adminKey = env?.VITE_ADMIN_API_KEY as string | undefined;
    const needsAdmin = (
      u.includes('/admin') ||
      u.startsWith('/v1/flags') ||
      u.startsWith('/v1/audit') ||
      u.startsWith('/v1/notifications/send')
    );
    if (adminKey && needsAdmin) headers['X-Admin-Key'] = adminKey;

    // Dev helper: force Admin role for moderation API in dev
    const dev = !!env?.DEV;
    const isModerationApi = u.startsWith('/api/moderation') || u.startsWith('/api/');
    if (dev && isModerationApi) {
      headers['X-Roles'] = headers['X-Roles'] || 'Admin';
      if (adminKey && !headers['X-Admin-Key']) headers['X-Admin-Key'] = adminKey;
    }
  } catch {}
  return headers;
}

async function handleResponse(res: Response) {
  syncCsrfFromResponse(res);
  if (!res.ok) {
    const errorBody = await res.text();
    if (res.status === 401 || (res.status === 403 && errorBody.includes('missing_token'))) {
      notifyAuthLost();
    }
    throw new Error(errorBody || `HTTP ${res.status}`);
  }
  return res;
}

export async function apiGetWithResponse<T = any>(u: string, opts: { omitCredentials?: boolean } = {}): Promise<{ data: T; response: Response }> {
  const headers: Record<string, string> = {};
  maybeWithAdminKey(headers, u);
  const res = await fetch(url(u), { credentials: opts.omitCredentials ? 'omit' : 'include', headers });
  const ok = await handleResponse(res);
  const text = await ok.text();
  const data = text ? (JSON.parse(text) as T) : (undefined as T);
  return { data, response: ok };
}

export async function apiGet<T = any>(u: string, opts: { omitCredentials?: boolean } = {}): Promise<T> {
  const { data } = await apiGetWithResponse<T>(u, opts);
  return data;
}

export async function apiPost<T = any>(u: string, body: any, opts: { omitCredentials?: boolean; headers?: Record<string, string> } = {}): Promise<T> {
  const res = await fetch(url(u), {
    method: 'POST',
    credentials: opts.omitCredentials ? 'omit' : 'include',
    headers: maybeWithAdminKey({ 'Content-Type': 'application/json', ...csrfHeaders(), ...(opts.headers || {}) }, u),
    body: JSON.stringify(body ?? {}),
  });
  const ok = await handleResponse(res);
  const text = await ok.text();
  return text ? (JSON.parse(text) as T) : (undefined as T);
}

export async function apiPatch<T = any>(u: string, body: any, opts: { omitCredentials?: boolean; headers?: Record<string, string> } = {}): Promise<T> {
  const res = await fetch(url(u), {
    method: 'PATCH',
    credentials: opts.omitCredentials ? 'omit' : 'include',
    headers: maybeWithAdminKey({ 'Content-Type': 'application/json', ...csrfHeaders(), ...(opts.headers || {}) }, u),
    body: JSON.stringify(body ?? {}),
  });
  const ok = await handleResponse(res);
  const text = await ok.text();
  return text ? (JSON.parse(text) as T) : (undefined as T);
}

export async function apiPutWithResponse<T = any>(
  u: string,
  body: any,
  opts: { omitCredentials?: boolean; headers?: Record<string, string> } = {}
): Promise<{ data: T; response: Response }> {
  const headers = maybeWithAdminKey({ 'Content-Type': 'application/json', ...csrfHeaders(), ...(opts.headers || {}) }, u);
  const res = await fetch(url(u), {
    method: 'PUT',
    credentials: opts.omitCredentials ? 'omit' : 'include',
    headers,
    body: JSON.stringify(body ?? {}),
  });
  const ok = await handleResponse(res);
  const text = await ok.text();
  const data = text ? (JSON.parse(text) as T) : (undefined as T);
  return { data, response: ok };
}

export async function apiPut<T = any>(
  u: string,
  body: any,
  opts: { omitCredentials?: boolean; headers?: Record<string, string> } = {}
): Promise<T> {
  const { data } = await apiPutWithResponse<T>(u, body, opts);
  return data;
}

export async function apiDelete<T = any>(u: string, opts: { omitCredentials?: boolean } = {}): Promise<T> {
  const res = await fetch(url(u), {
    method: 'DELETE',
    credentials: opts.omitCredentials ? 'omit' : 'include',
    headers: maybeWithAdminKey({ ...csrfHeaders() }, u),
  });
  const ok = await handleResponse(res);
  const text = await ok.text();
  return text ? (JSON.parse(text) as T) : (undefined as T);
}

export type UploadPayload =
  | FormData
  | File
  | Blob
  | {
      file?: File | Blob;
      files?: Array<File | Blob>;
      fields?: Record<string, string | Blob>;
      fieldName?: string;
    };

function toFormData(payload: UploadPayload): FormData {
  if (payload instanceof FormData) return payload;
  const fd = new FormData();
  if (payload instanceof File || payload instanceof Blob) {
    fd.append('file', payload);
    return fd;
  }
  const cast = payload as any;
  const name = typeof cast?.fieldName === 'string' && cast.fieldName.length ? cast.fieldName : 'file';
  if (cast?.file) fd.append(name, cast.file);
  if (Array.isArray(cast?.files)) for (const f of cast.files) fd.append(name, f);
  if (cast?.fields && typeof cast.fields === 'object') {
    for (const [k, v] of Object.entries(cast.fields)) fd.append(k, v as any);
  }
  return fd;
}

export type UploadOptions = { method?: string; omitCredentials?: boolean; headers?: Record<string, string> };

export function apiUploadMedia(path: string, payload: UploadPayload, opts?: UploadOptions): Promise<any>;
export function apiUploadMedia(payload: UploadPayload, opts?: UploadOptions): Promise<any>;
export async function apiUploadMedia(
  pathOrPayload: string | UploadPayload,
  payloadOrOpts?: UploadPayload | UploadOptions,
  maybeOpts: UploadOptions = {}
): Promise<any> {
  const path = typeof pathOrPayload === 'string' ? pathOrPayload : '/v1/media';
  const payload: UploadPayload = typeof pathOrPayload === 'string' ? (payloadOrOpts as UploadPayload) : (pathOrPayload as UploadPayload);
  if (payload == null) throw new Error('payload_required');
  const opts = typeof pathOrPayload === 'string' ? maybeOpts : (payloadOrOpts as UploadOptions | undefined) || {};
  const form = toFormData(payload);
  const baseHeaders: Record<string, string> = { ...csrfHeaders(), ...(opts.headers || {}) };
  const headers = maybeWithAdminKey(baseHeaders, path);
  delete (headers as any)['Content-Type'];
  delete (headers as any)['content-type'];
  const res = await fetch(url(path), {
    method: opts.method || 'POST',
    credentials: opts.omitCredentials ? 'omit' : 'include',
    headers,
    body: form,
  });
  const ok = await handleResponse(res);
  try {
    return await ok.json();
  } catch {
    return true;
  }
}






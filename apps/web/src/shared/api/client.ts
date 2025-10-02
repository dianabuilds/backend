import { extractErrorMessage } from '../utils/errors';

export function getCookie(nameContains: string): string | null {
  try {
    if (typeof document === 'undefined') return null;
    const normalized = nameContains.trim();
    if (!normalized) return null;
    const exact = parseCookie(normalized);
    if (exact !== null) return exact;
    const cookies = document.cookie.split(';');
    for (const entry of cookies) {
      const trimmed = entry.trim();
      if (!trimmed) continue;
      const eq = trimmed.indexOf('=');
      const key = eq === -1 ? trimmed : trimmed.slice(0, eq);
      if (key.toLowerCase().includes(normalized.toLowerCase())) {
        const value = eq >= 0 ? trimmed.slice(eq + 1) : '';
        try {
          return decodeURIComponent(value);
        } catch {
          return value;
        }
      }
    }
    return null;
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

function decodeBase64UrlSegment(segment: string): string {
  const normalized = segment.replace(/-/g, '+').replace(/_/g, '/');
  const padLength = (4 - (normalized.length % 4 || 4)) % 4;
  const padded = normalized.padEnd(normalized.length + padLength, '=');
  const binary = atob(padded);
  if (typeof TextDecoder !== 'undefined') {
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return new TextDecoder().decode(bytes);
  }
  let percentEncoded = '';
  for (let i = 0; i < binary.length; i += 1) {
    const hex = binary.charCodeAt(i).toString(16).padStart(2, '0');
    percentEncoded += `%${hex}`;
  }
  try {
    return decodeURIComponent(percentEncoded);
  } catch {
    return binary;
  }
}

export function decodeJwt<T = any>(token: string | undefined | null): T | null {
  try {
    if (!token) return null;
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const json = decodeBase64UrlSegment(parts[1]);
    return JSON.parse(json);
  } catch {
    return null;
  }
}

function url(u: string) {
  if (u.startsWith('http')) return u;
  return (isDev ? '' : base || '') + u;
}

const ADMIN_KEY_STORAGE_KEYS = ['admin.api.key', 'admin.apiKey'];

function readRuntimeAdminKey(): string | null {
  if (typeof window === 'undefined') return null;
  const candidates: Array<unknown> = [
    (window as any).__ADMIN_API_KEY,
    (window as any).__ADMIN_KEY__,
  ];
  for (const candidate of candidates) {
    if (typeof candidate === 'string' && candidate.trim()) return candidate.trim();
  }
  for (const storageName of ['sessionStorage', 'localStorage']) {
    try {
      const storage = (window as any)[storageName] as Storage | undefined;
      if (!storage) continue;
      for (const key of ADMIN_KEY_STORAGE_KEYS) {
        const value = storage.getItem(key);
        if (typeof value === 'string' && value.trim()) return value.trim();
      }
    } catch {}
  }
  return null;
}

function maybeWithAdminKey(headers: Record<string, string>, u: string) {
  try {
    const needsAdmin = (
      u.includes('/admin') ||
      u.startsWith('/v1/flags') ||
      u.startsWith('/v1/audit') ||
      u.startsWith('/v1/notifications/send')
    );
    if (needsAdmin) {
      const adminKey = readRuntimeAdminKey();
      if (adminKey) headers['X-Admin-Key'] = adminKey;
    }
  } catch {}
  return headers;
}

async function handleResponse(res: Response) {
  syncCsrfFromResponse(res);
  if (!res.ok) {
    let errorBody = '';
    try {
      errorBody = await res.text();
    } catch {
      errorBody = '';
    }
    const normalizedBody = errorBody || '';
    if (res.status === 401 || (res.status === 403 && normalizedBody.includes('missing_token'))) {
      notifyAuthLost();
    }
    const fallback = `Request failed (HTTP ${res.status})`;
    const message = normalizedBody ? extractErrorMessage(normalizedBody, fallback) : fallback;
    const error = new Error(message);
    (error as any).status = res.status;
    if (normalizedBody) {
      (error as any).body = normalizedBody;
    }
    throw error;
  }
  return res;
}

export type GetOptions = { omitCredentials?: boolean; signal?: AbortSignal; headers?: Record<string, string> };

export async function apiGetWithResponse<T = any>(
  u: string,
  opts: GetOptions = {},
): Promise<{ data: T; response: Response }> {
  const headers: Record<string, string> = { ...(opts.headers || {}) };
  maybeWithAdminKey(headers, u);
  const res = await fetch(url(u), {
    credentials: opts.omitCredentials ? 'omit' : 'include',
    headers,
    signal: opts.signal,
  });
  const ok = await handleResponse(res);
  const text = await ok.text();
  const data = text ? (JSON.parse(text) as T) : (undefined as T);
  return { data, response: ok };
}

export async function apiGet<T = any>(u: string, opts: GetOptions = {}): Promise<T> {
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


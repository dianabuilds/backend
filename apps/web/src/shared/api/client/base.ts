import { extractErrorMessage } from '../../utils/errors';
import { csrfHeaders, syncCsrfFromResponse } from './csrf';
import { applyAdminKey, notifyAuthLost } from './auth';

const isDev = (import.meta as any)?.env?.DEV;
const apiBase = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;

function buildUrl(path: string): string {
  if (path.startsWith('http')) return path;
  return (isDev ? '' : apiBase || '') + path;
}

function needsCsrf(method: string): boolean {
  const upper = method.toUpperCase();
  return upper !== 'GET' && upper !== 'HEAD';
}

type ErrorWithStatus = Error & { status?: number; body?: string };

async function handleResponse(res: Response): Promise<Response> {
  syncCsrfFromResponse(res);
  if (res.ok) return res;

  let errorBody: string;
  try {
    errorBody = await res.text();
  } catch {
    errorBody = '';
  }

  if (res.status === 401 || (res.status === 403 && errorBody.includes('missing_token'))) {
    notifyAuthLost();
  }

  const fallback = `Request failed (HTTP ${res.status})`;
  const message = errorBody ? extractErrorMessage(errorBody, fallback) : fallback;
  const error: ErrorWithStatus = new Error(message);
  error.status = res.status;
  if (errorBody) {
    error.body = errorBody;
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
  const init = prepareRequestInit(path, options);
  const response = await fetch(buildUrl(path), init);
  return handleResponse(response);
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
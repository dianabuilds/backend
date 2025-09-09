import { api, type ApiResponse, type RequestOptions as ApiRequestOptions } from './client';

export interface AccountRequestOptions<P extends Record<string, unknown> = Record<string, never>>
  extends ApiRequestOptions {
  params?: P;
  raw?: boolean;
  /** Account identifier to attach to the request. */
  accountId: string;
  /**
   * Configure account ID handling. By default the ID is appended as
   * `account_id` query parameter. Set to `false` to skip automatic
   * handling.
   */
  account?: 'query' | false;
}

// Overloads to support raw ApiResponse return when opts.raw === true
async function request<T = unknown, P extends Record<string, unknown> = Record<string, never>>(
  url: string,
  opts: AccountRequestOptions<P> & { raw: true },
): Promise<ApiResponse<T>>;
async function request<T = unknown, P extends Record<string, unknown> = Record<string, never>>(
  url: string,
  opts: AccountRequestOptions<P>,
): Promise<T>;
async function request<T = unknown, P extends Record<string, unknown> = Record<string, never>>(
  url: string,
  opts: AccountRequestOptions<P>,
): Promise<T | ApiResponse<T>> {
  const {
    params,
    headers: optHeaders,
    raw,
    accountId,
    account = 'query',
    ...rest
  } = opts as AccountRequestOptions<P> & {
    raw?: boolean;
  };

  const headers: Record<string, string> = {
    ...(optHeaders as Record<string, string> | undefined),
  };
  // Явно выставляем Accept для стабильного проксирования/маршрутизации API‑запросов
  if (!Object.keys(headers).some((k) => k.toLowerCase() === 'accept')) {
    headers['Accept'] = 'application/json';
  }

  let finalUrl = url;
  const finalParams: Record<string, unknown> = { ...(params || {}) };
  if (accountId && account === 'query') {
    if (finalParams.account_id === undefined) {
      finalParams.account_id = accountId;
    }
    // New param name; keep both for compatibility during transition
    if (finalParams.tenant_id === undefined) {
      finalParams.tenant_id = accountId;
    }
  }

  if (Object.keys(finalParams).length > 0) {
    const qs = new URLSearchParams();
    for (const [key, value] of Object.entries(finalParams)) {
      if (value === undefined || value === null) continue;
      if (Array.isArray(value)) {
        for (const v of value) qs.append(key, String(v));
      } else {
        qs.set(key, String(value));
      }
    }
    const qsStr = qs.toString();
    if (qsStr) {
      finalUrl += (finalUrl.includes('?') ? '&' : '?') + qsStr;
    }
  }

  const res = await api.request<T>(finalUrl, { ...rest, headers });
  return raw ? res : ((res.data as T) satisfies T);
}

export const accountApi = {
  request,
  get: <T = unknown, P extends Record<string, unknown> = Record<string, never>>(
    url: string,
    opts: AccountRequestOptions<P>,
  ) => request<T, P>(url, { ...opts, method: 'GET' }),
  post: <TReq = unknown, TRes = unknown, P extends Record<string, unknown> = Record<string, never>>(
    url: string,
    json?: TReq,
    opts?: AccountRequestOptions<P>,
  ) => request<TRes, P>(url, { ...(opts || ({} as AccountRequestOptions<P>)), method: 'POST', json }),
  put: <TReq = unknown, TRes = unknown, P extends Record<string, unknown> = Record<string, never>>(
    url: string,
    json?: TReq,
    opts?: AccountRequestOptions<P>,
  ) => request<TRes, P>(url, { ...(opts || ({} as AccountRequestOptions<P>)), method: 'PUT', json }),
  patch: <
    TReq = unknown,
    TRes = unknown,
    P extends Record<string, unknown> = Record<string, never>,
  >(
    url: string,
    json?: TReq,
    opts?: AccountRequestOptions<P>,
  ) => request<TRes, P>(url, { ...(opts || ({} as AccountRequestOptions<P>)), method: 'PATCH', json }),
  delete: <T = unknown, P extends Record<string, unknown> = Record<string, never>>(
    url: string,
    opts: AccountRequestOptions<P>,
  ) => request<T, P>(url, { ...opts, method: 'DELETE' }),
};

// Provide alias to reduce confusion, but prefer accountApi.delete across the codebase
export const del = accountApi.delete;

// type is already exported above; avoid duplicate re-export that confuses TS

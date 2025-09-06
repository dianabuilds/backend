import { safeLocalStorage } from "../utils/safeStorage";
import { api, type RequestOptions as ApiRequestOptions } from "./client";

function getAccountId(): string {
  return safeLocalStorage.getItem("accountId") || "";
}

function ensureAccountId(): string {
  const id = getAccountId();
  if (!id) {
    try {
      window.dispatchEvent(new Event("account-missing"));
    } catch {
      // ignore
    }
    throw new Error("Account is not selected");
  }
  return id;
}

export interface WsRequestOptions<P extends Record<string, unknown> = Record<string, never>>
  extends ApiRequestOptions {
  params?: P;
  raw?: boolean;
  /**
   * Configure account ID handling. By default the account ID is injected
   * into the URL path. Set to `false` to skip any automatic account handling
   * or to `"query"` to append the ID as `account_id` query parameter.
   */
  account?: "path" | "query" | false;
}

async function request<
  T = unknown,
  P extends Record<string, unknown> = Record<string, never>,
>(url: string, opts: WsRequestOptions<P> = {}): Promise<T> {
  const { params, headers: optHeaders, raw, account = "path", ...rest } = opts as WsRequestOptions<P> & {
    raw?: boolean;
  };

  let accountId: string | undefined;
  if (account !== false) {
    accountId = ensureAccountId();
  }
  const headers: Record<string, string> = {
    ...(optHeaders as Record<string, string> | undefined),
  };
  // Явно выставляем Accept для стабильного проксирования/маршрутизации API‑запросов
  if (!Object.keys(headers).some((k) => k.toLowerCase() === "accept")) {
    headers["Accept"] = "application/json";
  }

  let finalUrl = url;
  const finalParams: Record<string, unknown> = { ...(params || {}) };

  if (accountId && account === "path") {
    if (finalUrl.startsWith("/admin/") && !finalUrl.startsWith("/admin/accounts/")) {
      finalUrl = `/admin/accounts/${encodeURIComponent(accountId)}${finalUrl.slice(
        "/admin".length,
      )}`;
    }
  } else if (accountId && account === "query") {
    if (finalParams.account_id === undefined) {
      finalParams.account_id = accountId;
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
      finalUrl += (finalUrl.includes("?") ? "&" : "?") + qsStr;
    }
  }

  const res = await api.request<T>(finalUrl, { ...rest, headers });
  return raw ? res : (res.data as T);
}

export const wsApi = {
  request,
  get: <T = unknown, P extends Record<string, unknown> = Record<string, never>>(url: string, opts?: WsRequestOptions<P>) =>
    request<T, P>(url, { ...opts, method: "GET" }),
  post: <
    TReq = unknown,
    TRes = unknown,
    P extends Record<string, unknown> = Record<string, never>,
  >(
    url: string,
    json?: TReq,
    opts?: WsRequestOptions<P>,
  ) => request<TRes, P>(url, { ...opts, method: "POST", json }),
  put: <
    TReq = unknown,
    TRes = unknown,
    P extends Record<string, unknown> = Record<string, never>,
  >(
    url: string,
    json?: TReq,
    opts?: WsRequestOptions<P>,
  ) => request<TRes, P>(url, { ...opts, method: "PUT", json }),
  patch: <
    TReq = unknown,
    TRes = unknown,
    P extends Record<string, unknown> = Record<string, never>,
  >(
    url: string,
    json?: TReq,
    opts?: WsRequestOptions<P>,
  ) => request<TRes, P>(url, { ...opts, method: "PATCH", json }),
  delete: <T = unknown, P extends Record<string, unknown> = Record<string, never>>(url: string, opts?: WsRequestOptions<P>) =>
    request<T, P>(url, { ...opts, method: "DELETE" }),
};

// Provide alias to reduce confusion, but prefer wsApi.delete across the codebase
export const del = wsApi.delete;

export type { WsRequestOptions };

import { safeLocalStorage } from "../utils/safeStorage";
import { api, type RequestOptions as ApiRequestOptions } from "./client";

function getWorkspaceId(): string {
  return safeLocalStorage.getItem("workspaceId") || "";
}

function ensureWorkspaceId(): string {
  const id = getWorkspaceId();
  if (!id) {
    try {
      window.dispatchEvent(new Event("workspace-missing"));
    } catch {
      // ignore
    }
    throw new Error("Workspace is not selected");
  }
  return id;
}

export interface WsRequestOptions<P extends Record<string, unknown> = Record<string, never>>
  extends ApiRequestOptions {
  params?: P;
  raw?: boolean;
}

async function request<
  T = unknown,
  P extends Record<string, unknown> = Record<string, never>,
>(url: string, opts: WsRequestOptions<P> = {}): Promise<T> {
  const { params, headers: optHeaders, raw, ...rest } = opts as WsRequestOptions<P> & {
    raw?: boolean;
  };
  const workspaceId = ensureWorkspaceId();
  const headers: Record<string, string> = {
    ...(optHeaders as Record<string, string> | undefined),
  };

  let finalUrl = url;
  if (finalUrl.startsWith("/admin/") && !finalUrl.startsWith("/admin/workspaces/")) {
    finalUrl = `/admin/workspaces/${encodeURIComponent(workspaceId)}${finalUrl.slice(
      "/admin".length,
    )}`;
  }

  if (params && Object.keys(params).length > 0) {
    const qs = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
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
  del: <T = unknown, P extends Record<string, unknown> = Record<string, never>>(url: string, opts?: WsRequestOptions<P>) =>
    request<T, P>(url, { ...opts, method: "DELETE" }),
  delete: <T = unknown, P extends Record<string, unknown> = Record<string, never>>(url: string, opts?: WsRequestOptions<P>) =>
    request<T, P>(url, { ...opts, method: "DELETE" }),
};

export type { WsRequestOptions };

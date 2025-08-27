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

export interface WsRequestOptions extends ApiRequestOptions {
  params?: Record<string, unknown>;
}

async function request<T = unknown>(
  url: string,
  opts: WsRequestOptions = {},
): Promise<T> {
  const { params, headers: optHeaders, ...rest } = opts;
  const workspaceId = ensureWorkspaceId();
  const headers: Record<string, string> = {
    ...(optHeaders as Record<string, string> | undefined),
    "X-Workspace-Id": workspaceId,
  };

  let finalUrl = url;
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
  return res.data as T;
}

export const wsApi = {
  request,
  get: <T = unknown>(url: string, opts?: WsRequestOptions) =>
    request<T>(url, { ...opts, method: "GET" }),
  post: <TReq = unknown, TRes = unknown>(
    url: string,
    json?: TReq,
    opts?: WsRequestOptions,
  ) => request<TRes>(url, { ...opts, method: "POST", json }),
  put: <TReq = unknown, TRes = unknown>(
    url: string,
    json?: TReq,
    opts?: WsRequestOptions,
  ) => request<TRes>(url, { ...opts, method: "PUT", json }),
  patch: <TReq = unknown, TRes = unknown>(
    url: string,
    json?: TReq,
    opts?: WsRequestOptions,
  ) => request<TRes>(url, { ...opts, method: "PATCH", json }),
  del: <T = unknown>(url: string, opts?: WsRequestOptions) =>
    request<T>(url, { ...opts, method: "DELETE" }),
  delete: <T = unknown>(url: string, opts?: WsRequestOptions) =>
    request<T>(url, { ...opts, method: "DELETE" }),
};

export type { WsRequestOptions };

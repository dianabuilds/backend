import { safeLocalStorage } from "../utils/safeStorage";
import { request as baseRequest, type RequestOptions } from "./baseApi";

function getWorkspaceId(): string {
  return safeLocalStorage.getItem("workspaceId") || "";
}

function ensureWorkspaceId(): string {
  const id = getWorkspaceId();
  if (!id) {
    throw new Error("Workspace is not selected");
  }
  return id;
}

async function request<T = unknown>(url: string, opts: RequestOptions = {}): Promise<T> {
  const workspaceId = ensureWorkspaceId();
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string> | undefined),
    "X-Workspace-Id": workspaceId,
  };
  return baseRequest<T>(url, { ...opts, headers });
}

export const wsApi = {
  request,
  get: <T = unknown>(url: string, opts?: RequestOptions) =>
    request<T>(url, { ...opts, method: "GET" }),
  post: <TReq = unknown, TRes = unknown>(
    url: string,
    json?: TReq,
    opts?: RequestOptions,
  ) => request<TRes>(url, { ...opts, method: "POST", json }),
  put: <TReq = unknown, TRes = unknown>(
    url: string,
    json?: TReq,
    opts?: RequestOptions,
  ) => request<TRes>(url, { ...opts, method: "PUT", json }),
  patch: <TReq = unknown, TRes = unknown>(
    url: string,
    json?: TReq,
    opts?: RequestOptions,
  ) => request<TRes>(url, { ...opts, method: "PATCH", json }),
  del: <T = unknown>(url: string, opts?: RequestOptions) =>
    request<T>(url, { ...opts, method: "DELETE" }),
  delete: <T = unknown>(url: string, opts?: RequestOptions) =>
    request<T>(url, { ...opts, method: "DELETE" }),
};

export type { RequestOptions as WsRequestOptions };

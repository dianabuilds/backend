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
  /**
   * Configure workspace ID handling. By default the workspace ID is injected
   * into the URL path. Set to `false` to skip any automatic workspace handling
   * or to `"query"` to append the ID as `workspace_id` query parameter.
   */
  workspace?: "path" | "query" | false;
}

async function request<
  T = unknown,
  P extends Record<string, unknown> = Record<string, never>,
>(url: string, opts: WsRequestOptions<P> = {}): Promise<T> {
  const { params, headers: optHeaders, raw, workspace = "path", ...rest } = opts as WsRequestOptions<P> & {
    raw?: boolean;
  };

  let workspaceId: string | undefined;
  if (workspace !== false) {
    workspaceId = ensureWorkspaceId();
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

  if (workspaceId && workspace === "path") {
    if (finalUrl.startsWith("/admin/") && !finalUrl.startsWith("/admin/workspaces/")) {
      finalUrl = `/admin/workspaces/${encodeURIComponent(workspaceId)}${finalUrl.slice(
        "/admin".length,
      )}`;
    }
  } else if (workspaceId && workspace === "query") {
    if (finalParams.workspace_id === undefined) {
      finalParams.workspace_id = workspaceId;
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

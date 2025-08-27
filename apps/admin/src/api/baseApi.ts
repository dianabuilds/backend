export interface RequestOptions extends RequestInit {
  json?: unknown;
}

export async function request<T = unknown>(url: string, opts: RequestOptions = {}): Promise<T> {
  const { json, ...rest } = opts;
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(rest.headers as Record<string, string> | undefined),
  };
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    ...rest,
    headers,
    body: json !== undefined ? JSON.stringify(json) : rest.body,
    credentials: rest.credentials ?? "include",
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(text || response.statusText);
  }

  const contentType = response.headers.get("Content-Type") || "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }
  return (await response.text()) as unknown as T;
}

export const baseApi = {
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

export type { RequestOptions as BaseRequestOptions };

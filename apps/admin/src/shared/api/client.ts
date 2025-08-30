import { apiFetch } from "../../api/client";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const resp = await apiFetch(path, init);
  if (!resp.ok) {
    throw new Error(resp.statusText || `Request failed with ${resp.status}`);
  }
  const ct = resp.headers.get("content-type") || "";
  if (resp.status === 204 || !ct.includes("application/json")) {
    return undefined as T;
  }
  return (await resp.json()) as T;
}

export const client = {
  get<T>(path: string, init?: RequestInit) {
    return request<T>(path, { ...init, method: "GET" });
  },
  post<TBody, T>(path: string, body: TBody, init?: RequestInit) {
    return request<T>(path, {
      ...init,
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
  },
  patch<TBody, T>(path: string, body: TBody, init?: RequestInit) {
    return request<T>(path, {
      ...init,
      method: "PATCH",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
  },
  put<TBody, T>(path: string, body: TBody, init?: RequestInit) {
    return request<T>(path, {
      ...init,
      method: "PUT",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
  },
  del<T>(path: string, init?: RequestInit) {
    return request<T>(path, { ...init, method: "DELETE" });
  },
};

export type Client = typeof client;

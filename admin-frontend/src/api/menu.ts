import { apiFetch } from "./client";

export interface MenuItem {
  id: string;
  label: string;
  path?: string | null;
  icon?: string | null;
  order: number;
  children: MenuItem[];
  external?: boolean;
  divider?: boolean;
}

export interface MenuResponse {
  items: MenuItem[];
}

export async function getAdminMenu(etag?: string) {
  const headers: Record<string, string> = {};
  if (etag) headers["If-None-Match"] = etag;
  const resp = await apiFetch("/admin/menu", { headers });
  if (resp.status === 304) {
    return { items: null, etag: etag ?? null, status: 304 };
  }
  if (resp.status === 401 || resp.status === 403) {
    throw new Error("unauthorized");
  }
  const json: MenuResponse = await resp.json();
  return { items: json.items, etag: resp.headers.get("ETag"), status: 200 };
}

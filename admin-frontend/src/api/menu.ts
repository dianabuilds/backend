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
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (etag) headers["If-None-Match"] = etag;
  const resp = await fetch("/admin/menu", { headers });
  if (resp.status === 304) {
    return { items: null, etag: etag ?? null, status: 304 };
  }
  if (resp.status === 401 || resp.status === 403) {
    throw new Error("unauthorized");
  }
  const json: MenuResponse = await resp.json();
  return { items: json.items, etag: resp.headers.get("ETag"), status: 200 };
}

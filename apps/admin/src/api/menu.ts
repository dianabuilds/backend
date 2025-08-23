import { api } from "./client";

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
  const res = await api.get<MenuResponse>("/admin/menu", { etag, acceptNotModified: true });
  if (res.status === 304) {
    return { items: null, etag: etag ?? null, status: 304 };
  }
  return {
    items: (res.data?.items || []) as MenuItem[],
    etag: res.etag ?? null,
    status: res.status,
  };
}

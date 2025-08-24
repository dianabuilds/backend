import { api } from "./client";
import type { ListResponse } from "./types";

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

export async function getAdminMenu(etag?: string) {
  const res = await api.get<ListResponse<MenuItem>>("/admin/menu", {
    etag,
    acceptNotModified: true,
  });
  if (res.status === 304) {
    return { items: null, etag: etag ?? null, status: 304 } as const;
  }
  return {
    items: res.data?.items ?? [],
    etag: res.etag ?? null,
    status: res.status,
  };
}

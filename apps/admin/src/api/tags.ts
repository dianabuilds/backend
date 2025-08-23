import { api } from "./client";

export interface MergeReport {
  from: { id: string; name: string; slug: string };
  to: { id: string; name: string; slug: string };
  content_touched: number;
  aliases_moved: number;
  warnings: string[];
  errors: string[];
}

export async function dryRunMerge(from_id: string, to_id: string): Promise<MergeReport> {
  const res = await api.post<MergeReport>("/admin/tags/merge", { from_id, to_id, dryRun: true });
  return res.data as MergeReport;
}

export async function applyMerge(from_id: string, to_id: string, reason?: string): Promise<MergeReport> {
  const res = await api.post<MergeReport>("/admin/tags/merge", { from_id, to_id, dryRun: false, reason });
  return res.data as MergeReport;
}

export interface BlacklistItem {
  slug: string;
  reason?: string | null;
  created_at: string;
}

export async function getBlacklist(q?: string): Promise<BlacklistItem[]> {
  const qs = q ? `?q=${encodeURIComponent(q)}` : "";
  const res = await api.get<BlacklistItem[]>(`/admin/tags/blacklist${qs}`);
  return res.data as any;
}

export async function addToBlacklist(slug: string, reason?: string): Promise<BlacklistItem> {
  const res = await api.post<BlacklistItem>("/admin/tags/blacklist", { slug, reason });
  return res.data as any;
}

export async function removeFromBlacklist(slug: string): Promise<void> {
  await api.del(`/admin/tags/blacklist/${encodeURIComponent(slug)}`);
}

/** Admin list item returned by /admin/tags/list */
export type AdminTagListItem = {
  id: string;
  slug: string;
  name: string;
  created_at: string;
  usage_count: number;
  aliases_count: number;
  is_hidden: boolean;
};

export async function listAdminTags(params: { q?: string; limit?: number; offset?: number }): Promise<AdminTagListItem[]> {
  const { q, limit, offset } = params ?? {};
  const qs = [
    q ? `q=${encodeURIComponent(q)}` : "",
    typeof limit === "number" ? `limit=${limit}` : "",
    typeof offset === "number" ? `offset=${offset}` : "",
  ]
    .filter(Boolean)
    .join("&");
  const res = await api.get<AdminTagListItem[]>(`/admin/tags/list${qs ? `?${qs}` : ""}`);
  return res.data as any;
}

export async function createAdminTag(slug: string, name: string): Promise<AdminTagListItem> {
  const res = await api.post<AdminTagListItem>("/admin/tags", { slug, name });
  return res.data as any;
}

export async function deleteAdminTag(id: string): Promise<void> {
  await api.del(`/admin/tags/${encodeURIComponent(id)}`);
}

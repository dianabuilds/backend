import { api } from "./client";
import type { Workspace } from "./types";

export interface ListWorkspacesParams {
  q?: string;
  type?: string;
  limit?: number;
  offset?: number;
}

export async function listWorkspaces(
  params: ListWorkspacesParams = {},
): Promise<Workspace[]> {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.type) qs.set("type", params.type);
  if (typeof params.limit === "number") qs.set("limit", String(params.limit));
  if (typeof params.offset === "number") qs.set("offset", String(params.offset));
  const res = await api.get<Workspace[] | { workspaces: Workspace[] }>(
    `/admin/accounts${qs.size ? `?${qs.toString()}` : ""}`,
  );
  const data = res.data;
  if (Array.isArray(data)) return data;
  if (data && Array.isArray((data as any).workspaces)) {
    return (data as { workspaces: Workspace[] }).workspaces;
  }
  return [];
}

export type { Workspace } from "./types";

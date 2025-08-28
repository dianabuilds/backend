import type { NodeOut, ValidateResult, PublishIn } from "../openapi";
import type { ApiResponse } from "./client";
import { wsApi } from "./wsApi";

// The admin nodes list endpoint returns additional metadata compared to the
// public NodeOut model.  In particular it includes the `node_type` of each
// item and its `status`.  We extend the generated `NodeOut` type to capture
// these fields for stronger typing inside the admin UI.
export interface AdminNodeItem extends NodeOut {
  node_type: string;
  status: string;
}

const listCache = new Map<string, { etag: string | null; data: AdminNodeItem[] }>();

export interface NodeListParams {
  author?: string;
  tags?: string;
  match?: "any" | "all";
  sort?:
    | "updated_desc"
    | "created_desc"
    | "created_asc"
    | "views_desc"
    | "reactions_desc";
  is_public?: boolean;
  visible?: boolean;
  premium_only?: boolean;
  recommendable?: boolean;
  node_type?: string;
  limit?: number;
  offset?: number;
  date_from?: string;
  date_to?: string;
  q?: string;
  status?: string;
}

export interface NodePatchParams {
  title?: string | null;
  nodes?: null;
  media?: string[] | null;
  coverUrl?: string | null;
  tags?: string[] | null;
  isPublic?: boolean | null;
  isVisible?: boolean | null;
  allow_feedback?: boolean | null;
  isRecommendable?: boolean | null;
  premium_only?: boolean | null;
  nftRequired?: string | null;
  aiGenerated?: boolean | null;
  updatedAt?: string | null;
  publishedAt?: string | null;
}
export type NodePublishParams = PublishIn;
export interface NodePatchQuery {
  force?: 1;
  next?: 1;
}
export interface NodeSimulatePayload {
  [key: string]: unknown;
}

export async function listNodes(
  workspaceId: string,
  params: NodeListParams = {},
): Promise<AdminNodeItem[]> {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      qs.set(key, String(value));
    }
  }
  const url = `/admin/workspaces/${encodeURIComponent(
    workspaceId,
  )}/nodes${qs.toString() ? `?${qs.toString()}` : ""}`;
  const cacheKey = url;
  const cached = listCache.get(cacheKey);
  const res = (await wsApi.get(url, {
    etag: cached?.etag ?? undefined,
    acceptNotModified: true,
    raw: true,
    workspace: false,
  })) as ApiResponse<AdminNodeItem[]>;
  if (res.status === 304 && cached) return cached.data;
  const data = Array.isArray(res.data) ? res.data : [];
  if (res.etag) listCache.set(cacheKey, { etag: res.etag, data });
  return data;
}

export async function createNode(
  workspaceId: string,
  body: { node_type: string; title?: string },
): Promise<NodeOut> {
  // Для изолированных нод используем новый алиас /admin/articles
  const t = String(body.node_type);
  const payload = body.title ? { title: body.title } : undefined;
  let res: NodeOut;
  if (t === "article") {
    res = await wsApi.post<typeof payload, NodeOut>(
      `/admin/workspaces/${encodeURIComponent(workspaceId)}/articles`,
      payload,
      { workspace: false },
    );
  } else {
    const type = encodeURIComponent(t);
    res = await wsApi.post<typeof payload, NodeOut>(
      `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${type}`,
      payload,
      { workspace: false },
    );
  }
  return res;
}
export async function getNode(
  workspaceId: string,
  type: string,
  id: string,
): Promise<NodeOut> {
  const url =
    type === "article"
      ? `/admin/workspaces/${encodeURIComponent(workspaceId)}/articles/${encodeURIComponent(id)}`
      : `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}`;
  const res = await wsApi.get<NodeOut>(url);
  return res!;
}

export async function patchNode(
  workspaceId: string,
  type: string,
  id: string,
  patch: NodePatchParams,
  opts: { force?: boolean; signal?: AbortSignal; next?: boolean } = {},
): Promise<NodeOut> {
  const params: NodePatchQuery = {};
  if (opts.force) params.force = 1;
  if (opts.next) params.next = 1;
  const res = await wsApi.patch<NodePatchParams, NodeOut, NodePatchQuery>(
    type === "article"
      ? `/admin/workspaces/${encodeURIComponent(workspaceId)}/articles/${encodeURIComponent(id)}`
      : `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}`,
    patch,
    { params, signal: opts.signal, workspace: false },
  );
  return res!;
}

export async function publishNode(
  workspaceId: string,
  type: string,
  id: string,
  body: NodePublishParams | undefined = undefined,
): Promise<NodeOut> {
  const res = await wsApi.post<NodePublishParams | undefined, NodeOut>(
    type === "article"
      ? `/admin/workspaces/${encodeURIComponent(workspaceId)}/articles/${encodeURIComponent(id)}/publish`
      : `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/publish`,
    body,
    { workspace: false },
  );
  return res!;
}

export async function validateNode(
  workspaceId: string,
  type: string,
  id: string,
): Promise<ValidateResult> {
  const res = await wsApi.post<undefined, ValidateResult>(
    type === "article"
      ? `/admin/workspaces/${encodeURIComponent(workspaceId)}/articles/${encodeURIComponent(id)}/validate`
      : `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/validate`,
    undefined,
    { workspace: false },
  );
  return res!;
}

export async function simulateNode(
  workspaceId: string,
  type: string,
  id: string,
  payload: NodeSimulatePayload,
): Promise<any> {
  const res = await wsApi.post<NodeSimulatePayload, any>(
    `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/simulate`,
    payload,
    { workspace: false },
  );
  return res;
}

export async function recomputeNodeEmbedding(id: string): Promise<void> {
  await wsApi.post(
    `/admin/ai/nodes/${encodeURIComponent(id)}/embedding/recompute`,
  );
}

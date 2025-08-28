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

function normalizeTags<T extends { tags?: unknown }>(payload: T): T {
  if (!payload || typeof payload !== "object") return payload;
  const p = { ...payload } as Record<string, unknown>;
  const tags = p["tags"] as unknown;
  if (Array.isArray(tags)) {
    const normalized = tags
      .map((t) => {
        if (typeof t === "string") return t.trim();
        if (t && typeof t === "object") {
          const anyT = t as any;
          return (
            (typeof anyT.slug === "string" && anyT.slug) ||
            (typeof anyT.name === "string" && anyT.name) ||
            (typeof anyT.label === "string" && anyT.label) ||
            null
          );
        }
        return null;
      })
      .filter((v): v is string => typeof v === "string" && v.length > 0);
    (p as any)["tags"] = normalized;
    if (normalized.length === 0) {
      // чтобы не отправлять пустое поле, если оно не нужно
      delete (p as any)["tags"];
    }
  }
  return p as T;
}

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
  params: NodeListParams = {},
): Promise<AdminNodeItem[]> {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      qs.set(key, String(value));
    }
  }
  const url = `/admin/nodes${qs.toString() ? `?${qs.toString()}` : ""}`;
  const cacheKey = url;
  const cached = listCache.get(cacheKey);
  const res = (await wsApi.get(url, {
    etag: cached?.etag ?? undefined,
    acceptNotModified: true,
    raw: true,
  })) as ApiResponse<AdminNodeItem[]>;
  if (res.status === 304 && cached) return cached.data;
  const data = Array.isArray(res.data) ? res.data : [];
  if (res.etag) listCache.set(cacheKey, { etag: res.etag, data });
  return data;
}

export async function createNode(
  body: { node_type: string; title?: string },
): Promise<NodeOut> {
  // Для изолированных нод используем новый алиас /admin/articles
  const t = String(body.node_type);
  const payload = body.title ? { title: body.title } : undefined;
  let res: NodeOut;
  if (t === "article") {
    res = await wsApi.post<typeof payload, NodeOut>(`/admin/articles`, payload);
  } else {
    const type = encodeURIComponent(t);
    res = await wsApi.post<typeof payload, NodeOut>(`/admin/nodes/${type}`, payload);
  }
  return res;
}

export async function getNode(id: string): Promise<NodeOut>;
export async function getNode(type: string, id: string): Promise<NodeOut>;
export async function getNode(a: string, b?: string): Promise<NodeOut> {
  let url: string;
  if (b) {
    if (a === "article") url = `/admin/articles/${encodeURIComponent(b)}`;
    else url = `/admin/nodes/${encodeURIComponent(a)}/${encodeURIComponent(b)}`;
  } else {
    url = `/admin/nodes/${encodeURIComponent(a)}`;
  }
  const res = await wsApi.get<NodeOut>(url);
  return res!;
}

export async function patchNode(
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
      ? `/admin/articles/${encodeURIComponent(id)}`
      : `/admin/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}`,
    normalizeTags(patch),
    { params, signal: opts.signal },
  );
  return res!;
}

export async function publishNode(
  type: string,
  id: string,
  body: NodePublishParams | undefined = undefined,
): Promise<NodeOut> {
  const res = await wsApi.post<NodePublishParams | undefined, NodeOut>(
    type === "article"
      ? `/admin/articles/${encodeURIComponent(id)}/publish`
      : `/admin/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/publish`,
    body,
  );
  return res!;
}

export async function validateNode(
  type: string,
  id: string,
): Promise<ValidateResult> {
  const res = await wsApi.post<undefined, ValidateResult>(
    type === "article"
      ? `/admin/articles/${encodeURIComponent(id)}/validate`
      : `/admin/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/validate`,
  );
  return res!;
}

export async function simulateNode(
  type: string,
  id: string,
  payload: NodeSimulatePayload,
): Promise<any> {
  const res = await wsApi.post<NodeSimulatePayload, any>(
    `/admin/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/simulate`,
    payload,
  );
  return res;
}

export async function recomputeNodeEmbedding(id: string): Promise<void> {
  await wsApi.post(
    `/admin/ai/nodes/${encodeURIComponent(id)}/embedding/recompute`,
  );
}

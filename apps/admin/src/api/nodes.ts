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
  // Собираем query для cacheKey (те же параметры уйдут в wsApi через opts.params)
  // Собираем QS один раз
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      qs.set(key, String(value));
    }
  }

  // Helper: запрос с ETag-кэшем по явному URL (без workspace-переписываний)
  const getWithCache = async (url: string) => {
    const cached = listCache.get(url);
    const res = (await wsApi.get(url, {
      etag: cached?.etag ?? undefined,
      acceptNotModified: true,
      raw: true,
      workspace: false, // критично: ничего не переписываем автоматически
    })) as ApiResponse<AdminNodeItem[]>;
    if (res.status === 304 && cached) return cached.data;
    if (res.status === 404) {
      const err: any = new Error("Not Found");
      err.response = { status: 404 };
      throw err;
    }
    const data = Array.isArray(res.data) ? res.data : [];
    if (res.etag) listCache.set(url, { etag: res.etag, data });
    return data;
  };

  // 1) Основной админ-маршрут: /admin/workspaces/{ws}/nodes
  const adminByPath = `/admin/workspaces/${encodeURIComponent(
    workspaceId,
  )}/nodes${qs.toString() ? `?${qs.toString()}` : ""}`;
  try {
    return await getWithCache(adminByPath);
  } catch (e: any) {
    if (e?.response?.status !== 404) throw e;
  }

  // 2) Альтернативный админ-маршрут: /admin/nodes?workspace_id={ws}
  const adminByQuery = `/admin/nodes${
    qs.toString() ? `?${qs.toString()}&` : "?"
  }workspace_id=${encodeURIComponent(workspaceId)}`;
  try {
    return await getWithCache(adminByQuery);
  } catch (e: any) {
    if (e?.response?.status !== 404) throw e;
  }

  // 3) Публичный список (вернёт только видимые/опубликованные)
  const publicUrl = `/workspaces/${encodeURIComponent(
    workspaceId,
  )}/nodes${qs.toString() ? `?${qs.toString()}` : ""}`;
  return await getWithCache(publicUrl);
}

export async function createNode(
  workspaceId: string,
  body: { node_type: string; title?: string },
): Promise<NodeOut> {
  const payload: any = { node_type: body.node_type };
  if (body.title) payload.title = body.title;
  const res = await wsApi.post<typeof payload, NodeOut>(
    `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes`,
    payload,
    { workspace: false },
  );
  return res;
}
export interface NodeResponse extends NodeOut {
  cover_url?: string | null;
  tag_slugs?: string[];
  tagSlugs?: string[];
  cover?: { url?: string | null; cover_url?: string | null } | null;
}

export async function getNode(
  workspaceId: string,
  type: string,
  id: string,
): Promise<NodeResponse> {
  const url = `/admin/workspaces/${encodeURIComponent(
    workspaceId,
  )}/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}`;
  const res = await wsApi.get<NodeResponse>(url);
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
    `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}`,
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
    `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/publish`,
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
    `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(type)}/${encodeURIComponent(id)}/validate`,
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

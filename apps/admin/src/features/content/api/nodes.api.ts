import type { NodeOut } from "../../../openapi";
import { client } from "../../../shared/api/client";

const base = (workspaceId?: string) =>
  workspaceId
    ? `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes`
    : "/admin/nodes";

function withQuery(baseUrl: string, params?: Record<string, unknown>) {
  if (!params) return baseUrl;
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) qs.set(k, String(v));
  });
  const q = qs.toString();
  return q ? `${baseUrl}?${q}` : baseUrl;
}

export interface NodeMutationPayload {
  title?: string | null;
  slug?: string;
  coverUrl?: string | null;
  media?: string[] | null;
  tags?: string[] | null;
  tagSlugs?: string[] | null;
}

function enrichPayload(payload: NodeMutationPayload): Record<string, unknown> {
  const body: Record<string, unknown> = { ...payload };
  if (body.tags && !body.tagSlugs && !body.tag_slugs) {
    body.tagSlugs = body.tags;
    body.tag_slugs = body.tags;
  }
  if (body.coverUrl !== undefined && body.cover_url === undefined) {
    body.cover_url = body.coverUrl;
  }
  if (body.media !== undefined && !body.mediaUrls && !body.media_urls) {
    body.mediaUrls = body.media;
    body.media_urls = body.media;
  }
  return body;
}

export const nodesApi = {
  list(workspaceId?: string, params?: Record<string, unknown>) {
    return client.get<NodeOut[]>(withQuery(base(workspaceId), params));
  },
  get(workspaceId: string | undefined, id: number) {
    return client.get<NodeOut>(`${base(workspaceId)}/${encodeURIComponent(String(id))}`);
  },
  create(workspaceId: string | undefined, payload: NodeMutationPayload) {
    const body = enrichPayload(payload);
    return client.put<NodeMutationPayload, NodeOut>(
      withQuery(base(workspaceId), { next: 1 }),
      body,
    );
  },
  update(workspaceId: string | undefined, id: number, payload: NodeMutationPayload) {
    const body = enrichPayload(payload);
    const url = withQuery(
      `${base(workspaceId)}/${encodeURIComponent(String(id))}`,
      { next: 1 },
    );
    return client.patch<NodeMutationPayload, NodeOut>(url, body);
  },
  delete(workspaceId: string | undefined, id: number) {
    return client.del<void>(`${base(workspaceId)}/${encodeURIComponent(String(id))}`);
  },
};

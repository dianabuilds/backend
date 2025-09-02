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
  // EditorJS document
  content?: unknown;
}

function enrichPayload(payload: NodeMutationPayload): Record<string, unknown> {
  const body: Record<string, unknown> = { ...payload };
  // Дублируем теги вне зависимости от пустоты массива: ключевое — наличие ключа 'tags'
  if ('tags' in body && !('tagSlugs' in body) && !('tag_slugs' in body)) {
    body.tagSlugs = body.tags as unknown as string[] | null;
    body.tag_slugs = body.tags as unknown as string[] | null;
  }
  // Совместимость с более старыми эндпоинтами, ожидающими 'nodes' вместо 'content'
  if (body.content !== undefined && (body as any).nodes === undefined) {
    (body as any).nodes = body.content;
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
    // Backend expects POST /admin/workspaces/{ws}/nodes for creation
    return client.post<NodeMutationPayload, NodeOut>(
      base(workspaceId),
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

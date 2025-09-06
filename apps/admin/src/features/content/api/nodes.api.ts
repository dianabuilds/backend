import type { NodeOut } from "../../../openapi";
import { client } from "../../../shared/api/client";

const base = (workspaceId: string) =>
  `/admin/accounts/${encodeURIComponent(workspaceId)}/nodes`;

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
  // EditorJS document
  content?: unknown;
}

function enrichPayload(payload: NodeMutationPayload): Record<string, unknown> {
  return { ...payload };
}

export const nodesApi = {
  list(workspaceId: string, params?: Record<string, unknown>) {
    return client.get<NodeOut[]>(withQuery(base(workspaceId), params));
  },
  get(workspaceId: string, id: number) {
    return client.get<NodeOut>(`${base(workspaceId)}/${encodeURIComponent(String(id))}`);
  },
  create(workspaceId: string, payload: NodeMutationPayload) {
    const body = enrichPayload(payload);
    // Backend expects POST /admin/accounts/{ws}/nodes for creation
    return client.post<NodeMutationPayload, NodeOut>(
      base(workspaceId),
      body,
    );
  },
  update(workspaceId: string, id: number, payload: NodeMutationPayload) {
    const body = enrichPayload(payload);
    const url = withQuery(
      `${base(workspaceId)}/${encodeURIComponent(String(id))}`,
      { next: 1 },
    );
    return client.patch<NodeMutationPayload, NodeOut>(url, body);
  },
  delete(workspaceId: string, id: number) {
    return client.del<void>(`${base(workspaceId)}/${encodeURIComponent(String(id))}`);
  },
};

import type { NodeCreate, NodeOut, NodeUpdate } from "../../../openapi";
import { client } from "../../../shared/api/client";

const base = (workspaceId: string) =>
  `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes`;

function withQuery(baseUrl: string, params?: Record<string, unknown>) {
  if (!params) return baseUrl;
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) qs.set(k, String(v));
  });
  const q = qs.toString();
  return q ? `${baseUrl}?${q}` : baseUrl;
}

export const nodesApi = {
  list(workspaceId: string, params?: Record<string, unknown>) {
    return client.get<NodeOut[]>(withQuery(base(workspaceId), params));
  },
  get(workspaceId: string, id: number) {
    return client.get<NodeOut>(`${base(workspaceId)}/${encodeURIComponent(String(id))}`);
  },
  create(workspaceId: string, payload: NodeCreate) {
    return client.post<NodeCreate, NodeOut>(base(workspaceId), payload);
  },
  update(workspaceId: string, id: number, payload: NodeUpdate) {
    return client.patch<NodeUpdate, NodeOut>(
      `${base(workspaceId)}/${encodeURIComponent(String(id))}`,
      payload,
    );
  },
  delete(workspaceId: string, id: number) {
    return client.del<void>(`${base(workspaceId)}/${encodeURIComponent(String(id))}`);
  },
};

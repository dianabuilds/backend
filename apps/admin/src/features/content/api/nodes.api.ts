import type { NodeCreate, NodeOut, NodeUpdate } from "../../../openapi";
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

export const nodesApi = {
  list(workspaceId?: string, params?: Record<string, unknown>) {
    return client.get<NodeOut[]>(withQuery(base(workspaceId), params));
  },
  get(workspaceId: string | undefined, id: number) {
    return client.get<NodeOut>(`${base(workspaceId)}/${encodeURIComponent(String(id))}`);
  },
  create(workspaceId: string | undefined, payload: NodeCreate) {
    return client.put<NodeCreate, NodeOut>(base(workspaceId), payload);
  },
  update(workspaceId: string | undefined, id: number, payload: NodeUpdate) {
    return client.put<NodeUpdate, NodeOut>(
      `${base(workspaceId)}/${encodeURIComponent(String(id))}`,
      payload,
    );
  },
  delete(workspaceId: string | undefined, id: number) {
    return client.del<void>(`${base(workspaceId)}/${encodeURIComponent(String(id))}`);
  },
};

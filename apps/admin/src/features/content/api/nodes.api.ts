import type { NodeOut } from '../../../openapi';
import { client } from '../../../shared/api/client';

const base = `/admin/nodes`;

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
  list(params?: Record<string, unknown>) {
    return client.get<NodeOut[]>(withQuery(base, params));
  },
  get(id: number) {
    return client.get<NodeOut>(`${base}/${encodeURIComponent(String(id))}`);
  },
  create(payload: NodeMutationPayload) {
    const body = enrichPayload(payload);
    return client.post<NodeMutationPayload, NodeOut>(base, body);
  },
  update(id: number, payload: NodeMutationPayload) {
    const body = enrichPayload(payload);
    const url = withQuery(`${base}/${encodeURIComponent(String(id))}`, { next: 1 });
    return client.patch<NodeMutationPayload, NodeOut>(url, body);
  },
  delete(id: number) {
    return client.del<void>(`${base}/${encodeURIComponent(String(id))}`);
  },
};

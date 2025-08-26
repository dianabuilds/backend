import type { NodeOut, ValidateResult } from "../openapi";
import { api } from "./client";

export async function listNodes(
  params: Record<string, unknown> = {},
): Promise<NodeOut[]> {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      qs.set(key, String(value));
    }
  }
  const res = await api.get<NodeOut[]>(
    `/admin/nodes${qs.toString() ? `?${qs.toString()}` : ""}`,
  );
  return res.data ?? [];
}

export async function createNode(
  body: { node_type: string; title?: string },
): Promise<NodeOut> {
  const res = await api.post<NodeOut>("/admin/nodes", body);
  return res.data!;
}

export async function getNode(id: string): Promise<NodeOut> {
  const res = await api.get<NodeOut>(`/admin/nodes/${encodeURIComponent(id)}`);
  return res.data!;
}

export async function patchNode(
  id: string,
  patch: Record<string, unknown>,
  opts: { force?: boolean; signal?: AbortSignal; next?: boolean } = {},
): Promise<NodeOut> {
  const params: Record<string, number> = {};
  if (opts.force) params.force = 1;
  if (opts.next) params.next = 1;
  const res = await api.patch<NodeOut>(
    `/admin/nodes/${encodeURIComponent(id)}`,
    patch,
    { params, signal: opts.signal },
  );
  return res.data!;
}

export async function publishNode(
  id: string,
  body: Record<string, unknown> | undefined = undefined,
): Promise<NodeOut> {
  const res = await api.post<NodeOut>(
    `/admin/nodes/${encodeURIComponent(id)}/publish`,
    body,
  );
  return res.data!;
}

export async function validateNode(id: string): Promise<ValidateResult> {
  const res = await api.post<ValidateResult>(
    `/admin/nodes/${encodeURIComponent(id)}/validate`,
  );
  return res.data!;
}

export async function simulateNode(
  id: string,
  payload: Record<string, unknown>,
): Promise<any> {
  const res = await api.post(
    `/admin/nodes/${encodeURIComponent(id)}/simulate`,
    payload,
  );
  return res.data;
}

export async function recomputeNodeEmbedding(id: string): Promise<void> {
  await api.post(
    `/admin/ai/nodes/${encodeURIComponent(id)}/embedding/recompute`,
  );
}

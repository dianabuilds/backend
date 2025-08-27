import type { NodeOut, ValidateResult } from "../openapi";
import { wsApi } from "./wsApi";

// The admin nodes list endpoint returns additional metadata compared to the
// public NodeOut model.  In particular it includes the `node_type` of each
// item and its `status`.  We extend the generated `NodeOut` type to capture
// these fields for stronger typing inside the admin UI.
export interface AdminNodeItem extends NodeOut {
  node_type: string;
  status: string;
}

function normalizeTags(payload: Record<string, unknown>): Record<string, unknown> {
  if (!payload || typeof payload !== "object") return payload;
  const p = { ...payload };
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
    p["tags"] = normalized;
    if (normalized.length === 0) {
      // чтобы не отправлять пустое поле, если оно не нужно
      delete p["tags"];
    }
  }
  return p;
}

export async function listNodes(
  params: Record<string, unknown> = {},
): Promise<AdminNodeItem[]> {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      qs.set(key, String(value));
    }
  }
  const res = await wsApi.get<AdminNodeItem[]>(
    `/admin/nodes${qs.toString() ? `?${qs.toString()}` : ""}`,
  );
  return res ?? [];
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
  patch: Record<string, unknown>,
  opts: { force?: boolean; signal?: AbortSignal; next?: boolean } = {},
): Promise<NodeOut> {
  const params: Record<string, number> = {};
  if (opts.force) params.force = 1;
  if (opts.next) params.next = 1;
  const res = await wsApi.patch<Record<string, unknown>, NodeOut>(
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
  body: Record<string, unknown> | undefined = undefined,
): Promise<NodeOut> {
  const res = await wsApi.post<Record<string, unknown> | undefined, NodeOut>(
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
  payload: Record<string, unknown>,
): Promise<any> {
  const res = await wsApi.post<Record<string, unknown>, any>(
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

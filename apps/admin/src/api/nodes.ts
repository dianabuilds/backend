import type { NodeOut, Status } from '../openapi';
import { api } from './client';

// Admin list item with a couple of extra fields used in the UI
export interface AdminNodeItem extends NodeOut {
  status: string;
  nodeId?: number | null;
  space?: string;
}

type RawAdminNodeItem = Omit<AdminNodeItem, 'createdAt' | 'updatedAt'> & {
  createdAt?: string;
  updatedAt?: string;
  created_at?: string;
  updated_at?: string;
};

export interface NodeListParams {
  author?: string;
  tags?: string;
  match?: 'any' | 'all';
  sort?: 'updated_desc' | 'created_desc' | 'created_asc' | 'views_desc' | 'reactions_desc';
  is_public?: boolean;
  visible?: boolean;
  premium_only?: boolean;
  recommendable?: boolean;
  limit?: number;
  offset?: number;
  date_from?: string;
  date_to?: string;
  q?: string;
  status?: Status;
  scope_mode?: string;
}

export interface NodePatchParams {
  title?: string | null;
  content?: unknown;
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

export type NodePublishParams = {
  access?: 'everyone' | 'premium_only' | 'early_access';
  cover?: string | null;
  scheduled_at?: string | null;
};

export async function listNodes(params: NodeListParams = {}): Promise<AdminNodeItem[]> {
  try {
    const fromUrl = new URLSearchParams(window.location.search);
    if (!params.scope_mode) {
      const scope = fromUrl.get('scope');
      if (scope) params.scope_mode = scope;
    }
    if (!params.author) {
      const author = fromUrl.get('author');
      if (author) params.author = author;
    }
  } catch {
    // ignore on server/non-browser
  }
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) qs.set(key, String(value));
  }
  const url = `/admin/nodes${qs.toString() ? `?${qs.toString()}` : ''}`;
  const res = await api.get<RawAdminNodeItem[]>(url);
  const raw = Array.isArray(res.data) ? (res.data as RawAdminNodeItem[]) : [];
  return raw.map(({ created_at, updated_at, createdAt, updatedAt, ...rest }) => ({
    ...rest,
    createdAt: createdAt ?? created_at ?? '',
    updatedAt: updatedAt ?? updated_at ?? '',
  })) as AdminNodeItem[];
}

export interface CreateNodePayload {
  title?: string | null;
  slug?: string | null;
  isVisible?: boolean;
  premiumOnly?: boolean;
  allowFeedback?: boolean;
}

export async function createNode(payload: CreateNodePayload = {}): Promise<NodeOut> {
  const res = await api.post<CreateNodePayload, NodeOut>(`/admin/nodes`, payload);
  return (res.data as NodeOut) ?? ({} as NodeOut);
}

export interface NodeResponse extends NodeOut {
  cover?: { url?: string | null } | null;
  nodeId?: number | null;
  contentId?: number;
}

export async function getNode(id: number): Promise<NodeResponse> {
  const res = await api.get<NodeResponse>(`/admin/nodes/${encodeURIComponent(String(id))}`);
  return (res.data as NodeResponse) ?? ({} as NodeResponse);
}

export async function patchNode(
  id: number,
  patch: NodePatchParams,
  opts: { signal?: AbortSignal; next?: boolean } = {},
): Promise<NodeResponse> {
  const body: Record<string, unknown> = { ...patch };
  const suffix = opts.next === false ? '?next=0' : '?next=1';
  const res = await api.patch<typeof body, NodeResponse>(
    `/admin/nodes/${encodeURIComponent(String(id))}${suffix}`,
    body,
    { signal: opts.signal },
  );
  return (res.data as NodeResponse) ?? ({} as NodeResponse);
}

export async function publishNode(
  id: number,
  body: NodePublishParams | undefined = undefined,
): Promise<NodeOut> {
  const res = await api.post<typeof body, NodeOut>(
    `/admin/nodes/${encodeURIComponent(String(id))}/publish`,
    body,
  );
  return (res.data as NodeOut) ?? ({} as NodeOut);
}

export async function listNodesGlobal(params: NodeListParams = {}): Promise<AdminNodeItem[]> {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) qs.set(key, String(value));
  }
  if (!qs.has('scope_mode')) qs.set('scope_mode', 'global');
  const url = `/admin/nodes${qs.toString() ? `?${qs.toString()}` : ''}`;
  const res = await api.get<RawAdminNodeItem[]>(url);
  const raw = Array.isArray(res.data) ? (res.data as RawAdminNodeItem[]) : [];
  return raw.map(({ created_at, updated_at, createdAt, updatedAt, ...rest }) => ({
    ...rest,
    createdAt: createdAt ?? created_at ?? '',
    updatedAt: updatedAt ?? updated_at ?? '',
  })) as AdminNodeItem[];
}



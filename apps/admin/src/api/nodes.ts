import type { NodeOut, Status } from '../openapi';
import { accountApi } from './accountApi';
import { api, type ApiResponse } from './client';

// The admin nodes list endpoint returns additional metadata compared to the
// public NodeOut model. In particular, it includes the `status` of each item.
// We extend the generated `NodeOut` type to capture these fields for stronger
// typing inside the admin UI.
export interface AdminNodeItem extends NodeOut {
  status: string;
  nodeId?: number | null;
  space?: string;
}

const listCache = new Map<string, { etag: string | null; data: AdminNodeItem[] }>();

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
  /** Node content as EditorJS document. */
  content?: unknown;
  media?: string[] | null;
  coverUrl?: string | null;
  /** List of tag slugs. */
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

export interface NodeSimulatePayload {
  [key: string]: unknown;
}

export async function listNodes(
  accountId: string,
  params: NodeListParams = {},
): Promise<AdminNodeItem[]> {
  // Profile-centric path: no account → use personal nodes API
  if (!accountId) {
    const res = await api.get<NodeOut[]>(`/users/me/nodes`);
    const data = (Array.isArray(res.data) ? res.data : []) as RawAdminNodeItem[];
    return data.map(({ created_at, updated_at, createdAt, updatedAt, ...rest }) => {
      const r = rest as Partial<AdminNodeItem> & { id?: number | null };
      return {
        ...rest,
        status: r.status ?? 'draft',
        nodeId: r.nodeId ?? r.id ?? null,
        space: undefined,
        createdAt: createdAt ?? created_at ?? '',
        updatedAt: updatedAt ?? updated_at ?? '',
      } as AdminNodeItem;
    }) as AdminNodeItem[];
  }
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
    // ignore in non-browser contexts
  }
  // Собираем query для cacheKey (те же параметры уйдут в accountApi через opts.params)
  // Собираем QS один раз
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      qs.set(key, String(value));
    }
  }

  // Helper: запрос с ETag-кэшем по явному URL (без account-переписываний)
  const getWithCache = async (url: string) => {
    const cached = listCache.get(url);
    const res = (await accountApi.get(url, {
      etag: cached?.etag ?? undefined,
      acceptNotModified: true,
      raw: true,
      accountId, // kept only for telemetry headers; not used in URL
      account: false, // критично: ничего не переписываем автоматически
    })) as ApiResponse<AdminNodeItem[]>;
    if (res.status === 304 && cached) return cached.data;
    if (res.status === 404) {
      const err = new Error('Not Found') as Error & {
        response?: { status: number };
      };
      err.response = { status: 404 };
      throw err;
    }
    const raw: RawAdminNodeItem[] = Array.isArray(res.data) ? (res.data as RawAdminNodeItem[]) : [];
    const data = raw.map(({ created_at, updated_at, createdAt, updatedAt, ...rest }) => ({
      ...rest,
      createdAt: createdAt ?? created_at ?? '',
      updatedAt: updatedAt ?? updated_at ?? '',
    })) as AdminNodeItem[];
    if (res.etag) listCache.set(url, { etag: res.etag, data });
    return data;
  };

  // Accounts removed: use unified admin alias
  const url = `/admin/nodes${qs.toString() ? `?${qs.toString()}` : ''}`;
  return await getWithCache(url);
}

export interface CreateNodePayload {
  title?: string | null;
  slug?: string | null;
  isVisible?: boolean;
  premiumOnly?: boolean;
  allowFeedback?: boolean;
}

export async function createNode(
  accountId: string,
  payload: CreateNodePayload = {},
): Promise<NodeOut> {
  if (!accountId) {
    const res = await api.post<CreateNodePayload, NodeOut>(`/users/me/nodes`, payload);
    return res.data as NodeOut;
  }
  const url = `/admin/nodes`;
  return await accountApi.post<CreateNodePayload, NodeOut>(url, payload, {
    accountId: '',
    account: false,
  });
}

export interface NodeResponse extends NodeOut {
  cover?: { url?: string | null } | null;
  nodeId?: number | null;
  contentId?: number;
}

export async function getNode(accountId: string, id: number): Promise<NodeResponse> {
  try {
    if (accountId) {
      const url = `/admin/nodes/${encodeURIComponent(String(id))}`;
      return (await accountApi.get<NodeResponse>(url, {
        accountId: '',
        account: false,
      })) as NodeResponse;
    }
    const res = await api.get<NodeResponse>(`/users/me/nodes/${encodeURIComponent(String(id))}`);
    return res.data as NodeResponse;
  } catch (e: unknown) {
    const status =
      (e as { status?: number; response?: { status?: number } }).status ??
      (e as { response?: { status?: number } }).response?.status;
    if (status !== 404) throw e;
    // Try admin alias as a fallback for personal mode when not found
    try {
      return (await accountApi.get<NodeResponse>(`/admin/nodes/${encodeURIComponent(String(id))}`, {
        accountId: '',
        account: false,
      })) as NodeResponse;
    } catch {
      const err = new Error('Not Found') as Error & { response?: { status: number } };
      err.response = { status: 404 };
      throw err;
    }
  }
}

export async function patchNode(
  accountId: string,
  id: number,
  patch: NodePatchParams,
  opts: { signal?: AbortSignal; next?: boolean } = {},
): Promise<NodeResponse> {
  const body: Record<string, unknown> = { ...patch };
  if (accountId) {
    return (await accountApi.patch<typeof body, NodeResponse, { next: number }>(
      `/admin/nodes/${encodeURIComponent(String(id))}`,
      body,
      { accountId: '', account: false, params: { next: opts.next === false ? 0 : 1 } },
    )) as NodeResponse;
  }
  const res = await api.patch<typeof body, NodeResponse>(
    `/users/me/nodes/${encodeURIComponent(String(id))}`,
    body,
    { signal: opts.signal },
  );
  return res.data as NodeResponse;
}

export async function publishNode(
  _accountId: string,
  id: number,
  body: NodePublishParams | undefined = undefined,
): Promise<NodeOut> {
  return await accountApi.post<typeof body, NodeOut>(
    `/admin/nodes/${encodeURIComponent(String(id))}/publish`,
    body,
    { accountId: '', account: false },
  );
}

// Removed unused legacy helpers (archive/duplicate/preview/simulate/recompute embedding)

// Convenience helper for personal mode with global scope
export async function listNodesGlobal(params: NodeListParams = {}): Promise<AdminNodeItem[]> {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) qs.set(key, String(value));
  }
  if (!qs.has('scope_mode')) qs.set('scope_mode', 'global');
  const url = `/admin/nodes${qs.toString() ? `?${qs.toString()}` : ''}`;
  const res = (await accountApi.get(url, {
    etag: undefined,
    acceptNotModified: false,
    raw: true,
    accountId: '',
    account: false,
  })) as ApiResponse<AdminNodeItem[]>;
  const raw: RawAdminNodeItem[] = Array.isArray(res.data) ? (res.data as RawAdminNodeItem[]) : [];
  return raw.map(({ created_at, updated_at, createdAt, updatedAt, ...rest }) => ({
    ...rest,
    createdAt: createdAt ?? created_at ?? '',
    updatedAt: updatedAt ?? updated_at ?? '',
  })) as AdminNodeItem[];
}

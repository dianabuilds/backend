import {AdminService, type NodeOut, type PublishIn, type Status} from '../openapi';
import {accountApi} from './accountApi';
import { api, type ApiResponse } from './client';

// The admin nodes list endpoint returns additional metadata compared to the
// public NodeOut model. In particular it includes the `status` of each item.
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

export type NodePublishParams = PublishIn;

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
        return data.map(({ created_at, updated_at, createdAt, updatedAt, ...rest }) => ({
            status: (rest as any).status ?? 'draft',
            nodeId: (rest as any).nodeId ?? (rest as any).id,
            space: undefined,
            ...rest,
            createdAt: createdAt ?? created_at ?? '',
            updatedAt: updatedAt ?? updated_at ?? '',
        })) as AdminNodeItem[];
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
            accountId,
            account: false, // критично: ничего не переписываем автоматически
        })) as ApiResponse<AdminNodeItem[]>;
        if (res.status === 304 && cached) return cached.data;
        if (res.status === 404) {
            const err = new Error('Not Found') as Error & {
                response?: { status: number };
            };
            err.response = {status: 404};
            throw err;
        }
        const raw: RawAdminNodeItem[] = Array.isArray(res.data) ? (res.data as RawAdminNodeItem[]) : [];
        const data = raw.map(({ created_at, updated_at, createdAt, updatedAt, ...rest }) => ({
            ...rest,
            createdAt: createdAt ?? created_at ?? '',
            updatedAt: updatedAt ?? updated_at ?? '',
        })) as AdminNodeItem[];
        if (res.etag) listCache.set(url, {etag: res.etag, data});
        return data;
    };

    // Per-account route retained for legacy/admin screens
    const url = `/admin/accounts/${encodeURIComponent(accountId)}/nodes${qs.toString() ? `?${qs.toString()}` : ''}`;
    return await getWithCache(url);
}

export async function createNode(accountId: string): Promise<NodeOut> {
    if (!accountId) {
        const res = await api.post<NodeOut>(`/users/me/nodes`, {});
        return res.data as NodeOut;
    }
    const url = `/admin/accounts/${encodeURIComponent(accountId)}/nodes`;
    return await accountApi.post<undefined, NodeOut>(url, undefined, { accountId, account: false });
}

export interface NodeResponse extends NodeOut {
    cover?: { url?: string | null } | null;
    nodeId?: number | null;
  contentId?: number;
}

export async function getNode(accountId: string, id: number): Promise<NodeResponse> {
    try {
        if (accountId) {
            const res = await AdminService.getNodeByIdAdminAccountsAccountIdNodesNodeIdGet(
                id,
                accountId,
            );
            return res as NodeResponse;
        }
        const res = await api.get<NodeResponse>(`/users/me/nodes/${encodeURIComponent(String(id))}`);
        return res.data as NodeResponse;
    } catch (e: unknown) {
        const status =
            (e as { status?: number; response?: { status?: number } }).status ??
            (e as { response?: { status?: number } }).response?.status;
        if (status !== 404) throw e;
        if (!accountId || accountId.toLowerCase() === 'global') {
            const res = await AdminService.getGlobalNodeByIdAdminNodesNodeIdGet(id);
            return res as NodeResponse;
        }
        if (accountId) {
            await AdminService.replaceNodeByIdAdminAccountsAccountIdNodesNodeIdPut(
                id,
                accountId,
                {},
            );
            const res = await AdminService.getNodeByIdAdminAccountsAccountIdNodesNodeIdGet(
                id,
                accountId,
            );
            return res as NodeResponse;
        }
        // No more alias path without account; fall back to 404
        const err = new Error('Not Found') as Error & { response?: { status: number } };
        err.response = { status: 404 };
        throw err;
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
        const res = await AdminService.updateNodeByIdAdminAccountsAccountIdNodesNodeIdPatch(
            id,
            accountId,
            body,
            opts.next === false ? undefined : 1,
        );
        return res as NodeResponse;
    }
    const res = await api.patch<NodeResponse>(
        `/users/me/nodes/${encodeURIComponent(String(id))}`,
        body,
        { signal: opts.signal },
    );
    return res.data as NodeResponse;
}

export async function publishNode(
    accountId: string,
    id: number,
    body: NodePublishParams | undefined = undefined,
): Promise<NodeOut> {
    if (accountId) {
        const res = await AdminService.publishNodeByIdAdminAccountsAccountIdNodesNodeIdPublishPost(
            id,
            accountId,
            body,
        );
        return res as NodeOut;
    }
    const res = await accountApi.post<typeof body, NodeOut>(
        `/admin/nodes/${encodeURIComponent(String(id))}/publish`,
        body,
        { accountId: "", account: false },
    );
    return res;
}

export async function archiveNode(accountId: string, id: number): Promise<void> {
        await accountApi.post(
        `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(id))}/archive`,
        undefined,
        { accountId, account: false },
    );
}

export async function duplicateNode(accountId: string, id: number): Promise<NodeOut> {
    const res = await accountApi.post<undefined, NodeOut>(
        `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(id))}/duplicate`,
        undefined,
        { accountId, account: false },
    );
    return res;
}

export async function previewNode(accountId: string, id: number): Promise<void> {
        await accountApi.post(
        `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(id))}/preview`,
        undefined,
        { accountId, account: false },
    );
}

export async function simulateNode(
    accountId: string,
    id: number,
    payload: NodeSimulatePayload,
): Promise<unknown> {
    const res = await accountApi.post<NodeSimulatePayload, unknown>(
        `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(id))}/simulate`,
        payload,
        { accountId, account: false },
    );
    return res;
}

export async function recomputeNodeEmbedding(accountId: string, id: number): Promise<void> {
        await accountApi.post(
        `/admin/ai/nodes/${encodeURIComponent(id)}/embedding/recompute`,
        undefined,
        { accountId, account: false },
    );
}

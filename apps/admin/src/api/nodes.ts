import {AdminService, type NodeOut, type PublishIn, type Status, type ValidateResult} from '../openapi';
import type {ApiResponse} from './client';
import {wsApi} from './wsApi';

// The admin nodes list endpoint returns additional metadata compared to the
// public NodeOut model. In particular it includes the `status` of each item.
// We extend the generated `NodeOut` type to capture these fields for stronger
// typing inside the admin UI.
export interface AdminNodeItem extends NodeOut {
    status: string;
    nodeId?: number | null;
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
    workspaceId: string,
    params: NodeListParams = {},
): Promise<AdminNodeItem[]> {
    // Собираем query для cacheKey (те же параметры уйдут в wsApi через opts.params)
    // Собираем QS один раз
    const qs = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null) {
            qs.set(key, String(value));
        }
    }

    // Helper: запрос с ETag-кэшем по явному URL (без workspace-переписываний)
    const getWithCache = async (url: string) => {
        const cached = listCache.get(url);
        const res = (await wsApi.get(url, {
            etag: cached?.etag ?? undefined,
            acceptNotModified: true,
            raw: true,
            workspace: false, // критично: ничего не переписываем автоматически
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

    // Единственный актуальный маршрут: /admin/workspaces/{ws}/nodes
    const url = `/admin/workspaces/${encodeURIComponent(
        workspaceId,
    )}/nodes${qs.toString() ? `?${qs.toString()}` : ''}`;
    return await getWithCache(url);
}

export async function createNode(workspaceId: string): Promise<NodeOut> {
    const res = await wsApi.post<undefined, NodeOut>(
        `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes`,
        undefined,
        { workspace: false },
    );
    return res;
}

export interface NodeResponse extends NodeOut {
    cover?: { url?: string | null } | null;
    nodeId?: number | null;
  contentId?: number;
}

export async function getNode(workspaceId: string, id: number): Promise<NodeResponse> {
    try {
        const res = await AdminService.getNodeByIdAdminWorkspacesWorkspaceIdNodesNodeIdGet(
            id,
            workspaceId,
        );
        return res as NodeResponse;
    } catch (e: unknown) {
        const status =
            (e as { status?: number; response?: { status?: number } }).status ??
            (e as { response?: { status?: number } }).response?.status;
        if (status !== 404) throw e;
        if (!workspaceId || workspaceId.toLowerCase() === 'global') {
            const res = await AdminService.getGlobalNodeByIdAdminNodesNodeIdGet(id);
            return res as NodeResponse;
        }
        await AdminService.replaceNodeByIdAdminWorkspacesWorkspaceIdNodesNodeIdPut(
            id,
            workspaceId,
            {},
        );
        const res = await AdminService.getNodeByIdAdminWorkspacesWorkspaceIdNodesNodeIdGet(
            id,
            workspaceId,
        );
        return res as NodeResponse;
    }
}

export async function patchNode(
    workspaceId: string,
    id: number,
    patch: NodePatchParams,
    opts: { signal?: AbortSignal; next?: boolean } = {},
): Promise<NodeResponse> {
    const body: Record<string, unknown> = { ...patch };

    const res = await AdminService.updateNodeByIdAdminWorkspacesWorkspaceIdNodesNodeIdPatch(
        id,
        workspaceId,
        body,
        opts.next === false ? undefined : 1,
    );
    return res as NodeResponse;
}

export async function publishNode(
    workspaceId: string,
    id: number,
    body: NodePublishParams | undefined = undefined,
): Promise<NodeOut> {
    const res = await AdminService.publishNodeByIdAdminWorkspacesWorkspaceIdNodesNodeIdPublishPost(
        id,
        workspaceId,
        body,
    );
    return res as NodeOut;
}

export async function validateNode(workspaceId: string, id: number): Promise<ValidateResult> {
    const res =
        await AdminService.validateArticleAdminWorkspacesWorkspaceIdArticlesNodeIdValidatePost(
            id,
            workspaceId,
        );
    return res;
}

export async function simulateNode(
    workspaceId: string,
    id: number,
    payload: NodeSimulatePayload,
): Promise<unknown> {
    const res = await wsApi.post<NodeSimulatePayload, unknown>(
        `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(String(id))}/simulate`,
        payload,
        {workspace: false},
    );
    return res;
}

export async function recomputeNodeEmbedding(id: number): Promise<void> {
    await wsApi.post(`/admin/ai/nodes/${encodeURIComponent(id)}/embedding/recompute`);
}

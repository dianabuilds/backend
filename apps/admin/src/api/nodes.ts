import {AdminService, type NodeOut, type PublishIn, type ValidateResult} from '../openapi';
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
    status?: string;
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
        const data = Array.isArray(res.data) ? res.data : [];
        if (res.etag) listCache.set(url, {etag: res.etag, data});
        return data;
    };

    // 1) Основной админ-маршрут: /admin/workspaces/{ws}/nodes
    const adminByPath = `/admin/workspaces/${encodeURIComponent(
        workspaceId,
    )}/nodes${qs.toString() ? `?${qs.toString()}` : ''}`;
    try {
        return await getWithCache(adminByPath);
    } catch (e: unknown) {
        const status = (e as { response?: { status?: number } }).response?.status;
        if (status !== 404) throw e;
    }

    // 2) Альтернативный админ-маршрут: /admin/nodes?workspace_id={ws}
    const adminByQuery = `/admin/nodes${
        qs.toString() ? `?${qs.toString()}&` : '?'
    }workspace_id=${encodeURIComponent(workspaceId)}`;
    try {
        return await getWithCache(adminByQuery);
    } catch (e: unknown) {
        const status = (e as { response?: { status?: number } }).response?.status;
        if (status !== 404) throw e;
    }

    // 3) Публичный список (вернёт только видимые/опубликованные)
    const publicUrl = `/workspaces/${encodeURIComponent(
        workspaceId,
    )}/nodes${qs.toString() ? `?${qs.toString()}` : ''}`;
    return await getWithCache(publicUrl);
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

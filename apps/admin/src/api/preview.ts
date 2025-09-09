import {accountApi} from './accountApi';

export interface SimulatePreviewRequest {
    account_id: string;
    start: string;
    history?: string[];
    preview_mode?: string;
    role?: string;
    plan?: string;
    seed?: number;
    locale?: string;
    device?: string;
    time?: string;

    [k: string]: unknown;
}

export interface SimulatePreviewResponse {
    next?: string | null;
    reason?: string | null;
    trace?: unknown[];
    metrics?: {
        tag_entropy?: number;
        source_diversity?: number;
        tags?: string[];
        sources?: string[];
        [k: string]: unknown;
    };
}

export async function simulatePreview(
    body: SimulatePreviewRequest,
): Promise<SimulatePreviewResponse> {
    const res = await accountApi.post<SimulatePreviewRequest, SimulatePreviewResponse>(
        `/admin/preview/transitions/simulate`,
        body,
        {
            accountId: body.account_id,
            account: false,
        },
    );
    return res ?? {};
}

export interface PreviewLinkResponse {
    url: string;
}

export async function createPreviewLink(account_id: string): Promise<PreviewLinkResponse> {
    return await accountApi.post<{ account_id: string }, PreviewLinkResponse>(
        `/admin/preview/link`,
        {account_id},
        {
            accountId: account_id,
            account: false,
        },
    );
}

/**
 * Открывает превью ноды в новой вкладке.
 * Универсально обрабатывает:
 * - числовой id (например, 60) или строку с числом ("60")
 * - путь вида "/nodes/article/60"
 * - slug строки (в этом случае используем токен‑превью со start=<slug>)
 *
 * Для id всегда формируем admin‑маршрут:
 *   /admin/nodes/{type}/{id}/preview?account_id=...
 * Тип по умолчанию: "article".
 */

import { api } from './client';

export interface SimulatePreviewRequest {
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
  const res = await api.post<SimulatePreviewRequest, SimulatePreviewResponse>(
    `/admin/preview/transitions/simulate`,
    body,
  );
  return (res?.data as SimulatePreviewResponse) ?? {};
}

export interface PreviewLinkResponse {
  url: string;
}

export async function createPreviewLink(ttl?: number): Promise<PreviewLinkResponse> {
  const res = await api.post<{ ttl?: number }, PreviewLinkResponse>(
    `/admin/preview/link`,
    ttl ? { ttl } : undefined,
  );
  return (res?.data as PreviewLinkResponse) ?? { url: '/preview' };
}

/**
 * Открывает превью ноды в новой вкладке.
 * Универсально обрабатывает:
 * - числовой id (например, 60) или строку с числом ("60")
 * - путь вида "/nodes/article/60"
 * - slug строки (в этом случае используем токен‑превью со start=<slug>)
 *
 * Для id всегда формируем admin‑маршрут:
 *   /admin/nodes/{type}/{id}/preview
 * Тип по умолчанию: "article".
 */

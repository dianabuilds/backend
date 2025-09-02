import { wsApi } from "./wsApi";

export interface SimulatePreviewRequest {
  workspace_id: string;
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
  const res = await wsApi.post<
    SimulatePreviewRequest,
    SimulatePreviewResponse
  >(`/admin/preview/transitions/simulate`, body, { workspace: false });
  return res ?? {};
}

export interface PreviewLinkResponse {
  url: string;
}

export async function createPreviewLink(
  workspace_id: string,
): Promise<PreviewLinkResponse> {
  // Корректный эндпоинт — без workspace в пути. workspace_id передаём в теле.
  const res = await wsApi.post<
    { workspace_id: string },
    PreviewLinkResponse
  >(`/admin/preview/link`, { workspace_id }, { workspace: false });
  return res;
}

/**
 * Открывает превью ноды в новой вкладке.
 * Если передан slug — добавляет ?start=<slug> к URL превью.
 * Использует тот же механизм, что и превью в карточке редактирования.
 */
export async function openNodePreview(
  workspace_id: string,
  slug?: string | null,
): Promise<void> {
  const { url } = await createPreviewLink(workspace_id);
  const withStart =
    slug && slug.trim()
      ? `${url}${url.includes("?") ? "&" : "?"}start=${encodeURIComponent(slug)}`
      : url;
  window.open(withStart, "_blank", "noopener");
}


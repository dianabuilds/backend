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
 * Универсально обрабатывает:
 * - числовой id (например, 60) или строку с числом ("60")
 * - путь вида "/nodes/60"
 * - slug строки (в этом случае используем токен‑превью со start=<slug>)
 *
 * Для id всегда формируем admin‑маршрут:
 *   /admin/nodes/{type}/{id}/preview?workspace_id=...
 * Тип по умолчанию: "article".
 */
export async function openNodePreview(
  workspace_id: string,
  ref?: string | number | null,
  nodeType: string = 'article',
): Promise<void> {
  const raw = ref == null ? '' : String(ref).trim();

  // 1) Если это путь "/nodes/{id}" — вытащим id
  let idStr: string | null = null;
  if (raw.startsWith('/nodes/')) {
    idStr = raw.split('/').filter(Boolean).pop() || null;
  } else if (/^\d+$/.test(raw)) {
    // 2) Если это числовой id в строке
    idStr = raw;
  } else if (typeof ref === 'number' && Number.isFinite(ref)) {
    // 3) Если это number
    idStr = String(ref);
  }

  if (idStr) {
    const adminUrl = `/admin/nodes/${encodeURIComponent(nodeType)}/${encodeURIComponent(
      idStr,
    )}/preview?workspace_id=${encodeURIComponent(workspace_id)}`;
    window.open(adminUrl, '_blank', 'noopener');
    return;
  }

  // 4) Иначе — считаем, что это slug: используем токен‑превью со start
  const { url } = await createPreviewLink(workspace_id);
  const withStart =
    raw
      ? `${url}${url.includes('?') ? '&' : '?'}start=${encodeURIComponent(raw)}`
      : url;
  window.open(withStart, '_blank', 'noopener');
}


import { api } from "./client";

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
  const res = await api.post<SimulatePreviewResponse>(
    "/admin/preview/transitions/simulate",
    body,
  );
  return res.data ?? {};
}

export interface PreviewLinkResponse {
  url: string;
}

export async function createPreviewLink(
  workspace_id: string,
): Promise<PreviewLinkResponse> {
  const res = await api.post<PreviewLinkResponse>("/admin/preview/link", {
    workspace_id,
  });
  return res.data as PreviewLinkResponse;
}


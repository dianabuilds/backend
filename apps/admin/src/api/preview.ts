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
  metrics?: Record<string, unknown>;
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


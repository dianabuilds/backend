import { api } from "./client";
import type { Page } from "./types";

export interface CaseListItem {
  id: string;
  type: string;
  status: string;
  priority: string;
  summary: string;
  target_type?: string | null;
  target_id?: string | null;
  assignee_id?: string | null;
  labels: string[];
  created_at: string;
  due_at?: string | null;
  last_event_at?: string | null;
}

export interface CaseCreateIn {
  type: string;
  summary: string;
  details?: string;
  target_type?: string;
  target_id?: string;
  reporter_id?: string;
  reporter_contact?: string;
  priority?: string;
  labels?: string[];
  assignee_id?: string;
}

export interface CasePatchIn {
  summary?: string;
  details?: string;
  priority?: string;
  status?: string;
  assignee_id?: string;
  due_at?: string;
}

export async function listCases(
  params: Record<string, unknown> = {},
): Promise<Page<CaseListItem>> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    if (Array.isArray(v)) v.forEach((x) => qs.append(k, String(x)));
    else qs.set(k, String(v));
  });
  const res = await api.get<Page<CaseListItem>>(
    `/admin/moderation/cases?${qs.toString()}`,
  );
  return res.data!;
}

export async function createCase(data: CaseCreateIn): Promise<string> {
  const res = await api.post<{ id: string }>("/admin/moderation/cases", data);
  return res.data!.id;
}

export async function patchCase(id: string, patch: CasePatchIn): Promise<void> {
  await api.patch(`/admin/moderation/cases/${id}`, patch);
}

export interface CaseNote {
  id: string;
  author_id?: string | null;
  created_at: string;
  text: string;
  internal: boolean;
}
export async function addNote(
  caseId: string,
  text: string,
  internal = true,
): Promise<CaseNote> {
  const res = await api.post<CaseNote>(
    `/admin/moderation/cases/${caseId}/notes`,
    { text, internal },
  );
  return res.data!;
}

export interface CaseOut {
  id: string;
  type: string;
  status: string;
  priority: string;
  summary: string;
  details?: string | null;
  target_type?: string | null;
  target_id?: string | null;
  assignee_id?: string | null;
  labels: string[];
}

export interface CaseAttachment {
  id: string;
  author_id?: string | null;
  created_at: string;
  url: string;
  title?: string | null;
  media_type?: string | null;
}

export interface CaseEvent {
  id: string;
  actor_id?: string | null;
  created_at: string;
  kind: string;
  payload?: Record<string, unknown> | null;
}

export interface CaseFullResponse {
  case: CaseOut;
  notes: CaseNote[];
  attachments: CaseAttachment[];
  events: CaseEvent[];
}
export async function getCaseFull(id: string): Promise<CaseFullResponse> {
  const res = await api.get<CaseFullResponse>(`/admin/moderation/cases/${id}`);
  return res.data!;
}

export async function closeCase(
  id: string,
  resolution: "resolved" | "rejected",
  reason_code?: string,
  reason_text?: string,
): Promise<void> {
  await api.post(`/admin/moderation/cases/${id}/actions/close`, {
    resolution,
    reason_code,
    reason_text,
  });
}

export interface CaseLabelsPatch {
  add?: string[];
  remove?: string[];
}

export async function patchLabels(
  id: string,
  patch: CaseLabelsPatch,
): Promise<void> {
  await api.patch(`/admin/moderation/cases/${id}/labels`, patch);
}

export interface CaseAttachmentCreate {
  url: string;
  title?: string;
  media_type?: string;
}

export async function addAttachment(
  id: string,
  data: CaseAttachmentCreate,
): Promise<void> {
  await api.post(`/admin/moderation/cases/${id}/attachments`, data);
}

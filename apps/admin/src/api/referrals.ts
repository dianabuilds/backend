import { withQueryParams } from "../shared/utils";
import { api } from "./client";

export interface ReferralCodeAdmin {
  id: string;
  workspace_id: number;
  owner_user_id?: string | null;
  code: string;
  uses_count: number;
  active: boolean;
  created_at?: string | null;
}

export interface ReferralEventAdmin {
  id: string;
  workspace_id: number;
  code_id?: string | null;
  code?: string | null;
  referrer_user_id?: string | null;
  referee_user_id: string;
  event_type: string;
  occurred_at: string;
}

export async function listReferralCodes(params: {
  workspace_id: number;
  owner_user_id?: string;
  active?: boolean;
  limit?: number;
  offset?: number;
}): Promise<ReferralCodeAdmin[]> {
  const url = withQueryParams("/admin/referrals/codes", params);
  const res = await api.get<ReferralCodeAdmin[]>(url);
  return Array.isArray(res.data) ? res.data : [];
}

export async function activateReferralCode(owner_user_id: string, workspace_id: number, reason?: string): Promise<{ ok: boolean; code: string }>{
  const url = withQueryParams(`/admin/referrals/codes/${encodeURIComponent(owner_user_id)}/activate`, { workspace_id });
  const res = await api.post<{ ok: boolean; code: string }>(url, reason ? { reason } : undefined);
  return res.data;
}

export async function deactivateReferralCode(owner_user_id: string, workspace_id: number, reason?: string): Promise<{ ok: boolean }>{
  const url = withQueryParams(`/admin/referrals/codes/${encodeURIComponent(owner_user_id)}/deactivate`, { workspace_id });
  const res = await api.post<{ ok: boolean }>(url, reason ? { reason } : undefined);
  return res.data;
}

export async function listReferralEvents(params: {
  workspace_id: number;
  referrer_user_id?: string;
  limit?: number;
  offset?: number;
  date_from?: string;
  date_to?: string;
}): Promise<ReferralEventAdmin[]> {
  const url = withQueryParams("/admin/referrals/events", params);
  const res = await api.get<ReferralEventAdmin[]>(url);
  return Array.isArray(res.data) ? res.data : [];
}

export async function exportReferralEventsCSV(params: {
  workspace_id: number;
  referrer_user_id?: string;
  limit?: number;
  offset?: number;
  date_from?: string;
  date_to?: string;
}): Promise<Blob> {
  const url = withQueryParams("/admin/referrals/events/export", params);
  const res = await api.get(url, { headers: { Accept: "text/csv" } });
  const text = typeof res.data === "string" ? res.data : String(res.data as any);
  return new Blob([text], { type: "text/csv" });
}

export async function getMyReferralCode(workspace_id: number): Promise<{ code: string; active: boolean }>{
  const url = withQueryParams("/referrals/me/code", { workspace_id });
  const res = await api.get<{ code: string; active: boolean }>(url);
  return res.data;
}

export async function getMyReferralStats(): Promise<{ total_signups: number }>{
  const res = await api.get<{ total_signups: number }>("/referrals/me/stats");
  return res.data;
}


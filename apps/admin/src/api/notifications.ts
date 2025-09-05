import type {
  BroadcastCreate,
  BroadcastFilters,
  SendNotificationPayload,
} from "../openapi";
import { api } from "./client";
import { ensureArray } from "../shared/utils";
import type { ListResponse } from "./types";

export interface Campaign {
  id: string;
  title: string;
  status: string;
  total: number;
  sent: number;
  failed: number;
  type: string;
  created_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface DraftCampaign {
  id: string;
  title: string;
  message: string;
  status: string;
  created_at?: string | null;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type?: string | null;
  read_at?: string | null;
  created_at: string;
}

export async function createBroadcast(
  payload: BroadcastCreate,
): Promise<unknown> {
  const res = await api.post<unknown>(
    "/admin/notifications/broadcast",
    payload,
  );
  return res.data;
}

export async function listBroadcasts(): Promise<Campaign[]> {
  const res = await api.get<ListResponse<Campaign> | Campaign[]>(
    "/admin/notifications/broadcast",
  );
  const d = res.data;
  if (Array.isArray(d)) return d;
  return d?.items ?? [];
}

export async function getCampaign(id: string): Promise<Campaign> {
  const res = await api.get<Campaign>(`/admin/notifications/broadcast/${id}`);
  return res.data!;
}

export async function cancelCampaign(id: string): Promise<unknown> {
  const res = await api.post<unknown>(
    `/admin/notifications/broadcast/${id}/cancel`,
    {},
  );
  return res.data;
}

export async function listCampaigns(): Promise<DraftCampaign[]> {
  const res = await api.get<DraftCampaign[]>("/admin/notifications/campaigns");
  return res.data ?? [];
}

export async function getDraftCampaign(id: string): Promise<DraftCampaign> {
  const res = await api.get<DraftCampaign>(
    `/admin/notifications/campaigns/${id}`,
  );
  return res.data!;
}

export async function updateDraftCampaign(
  id: string,
  payload: { title: string; message: string },
): Promise<unknown> {
  const res = await api.patch<unknown>(
    `/admin/notifications/campaigns/${id}`,
    payload,
  );
  return res.data;
}

export async function sendDraftCampaign(id: string): Promise<unknown> {
  const res = await api.post<unknown>(
    `/admin/notifications/campaigns/${id}/send`,
    {},
  );
  return res.data;
}

export async function listNotifications(
  workspaceId?: string,
): Promise<NotificationItem[]> {
  const res = await api.get<NotificationItem[]>("/notifications", {
    params: workspaceId ? { workspace_id: workspaceId } : undefined,
  });
  return ensureArray<NotificationItem>(res.data);
}

export async function markNotificationRead(
  id: string,
  workspaceId?: string,
): Promise<unknown> {
  const res = await api.post<unknown>(
    `/notifications/${id}/read`,
    {},
    { params: workspaceId ? { workspace_id: workspaceId } : undefined },
  );
  return res.data;
}

export async function sendNotification(
  payload: SendNotificationPayload,
): Promise<unknown> {
  const res = await api.post<unknown>(
    "/admin/notifications",
    payload,
  );
  return res.data;
}

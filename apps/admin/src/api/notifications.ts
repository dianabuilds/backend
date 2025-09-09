import type {
  CampaignCreate,
  CampaignFilters,
  CampaignUpdate,
  SendNotificationPayload,
} from '../openapi';
import { ensureArray } from '../shared/utils';
import { api } from './client';
import type { ListResponse } from './types';

export interface Campaign {
  id: string;
  title: string;
  message?: string;
  status: string;
  total: number;
  sent: number;
  failed: number;
  type: string;
  created_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  filters?: Record<string, unknown>;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type?: string | null;
  placement?: string | null;
  read_at?: string | null;
  created_at: string;
}

export interface DraftCampaign extends Campaign {
  message: string;
}

export async function estimateCampaign(filters: CampaignFilters): Promise<unknown> {
  const res = await api.post<unknown>('/admin/notifications/campaigns/estimate', filters);
  return res.data;
}

export async function createCampaign(payload: CampaignCreate): Promise<unknown> {
  const res = await api.post<unknown>('/admin/notifications/campaigns', payload);
  return res.data;
}

export async function listCampaigns(): Promise<Campaign[]> {
  const res = await api.get<ListResponse<Campaign> | Campaign[]>('/admin/notifications/campaigns');
  const d = res.data;
  if (Array.isArray(d)) return d;
  return d?.items ?? [];
}

export async function getCampaign(id: string): Promise<Campaign> {
  const res = await api.get<Campaign>(`/admin/notifications/campaigns/${id}`);
  return res.data!;
}

export async function updateCampaign(id: string, payload: CampaignUpdate): Promise<unknown> {
  const res = await api.patch<unknown>(`/admin/notifications/campaigns/${id}`, payload);
  return res.data;
}

export async function deleteCampaign(id: string): Promise<unknown> {
  const res = await api.delete<unknown>(`/admin/notifications/campaigns/${id}`);
  return res.data;
}

export async function startCampaign(id: string): Promise<unknown> {
  const res = await api.post<unknown>(`/admin/notifications/campaigns/${id}/start`, {});
  return res.data;
}

export async function cancelCampaign(id: string): Promise<unknown> {
  const res = await api.post<unknown>(`/admin/notifications/campaigns/${id}/cancel`, {});
  return res.data;
}

export async function getDraftCampaign(id: string): Promise<DraftCampaign> {
  const res = await api.get<DraftCampaign>(`/admin/notifications/campaigns/${id}`);
  return res.data!;
}

export async function updateDraftCampaign(
  id: string,
  payload: { title: string; message: string },
): Promise<unknown> {
  const res = await api.patch<unknown>(`/admin/notifications/campaigns/${id}`, payload);
  return res.data;
}

export async function sendDraftCampaign(id: string): Promise<unknown> {
  const res = await api.post<unknown>(`/admin/notifications/campaigns/${id}/start`, {});
  return res.data;
}

export async function listNotifications(
  accountId?: string,
  placement?: string,
): Promise<NotificationItem[]> {
  const params: Record<string, string> = {};
  if (accountId) params.account_id = accountId;
  if (placement) params.placement = placement;
  const res = await api.get<NotificationItem[]>('/notifications', {
    params: Object.keys(params).length ? params : undefined,
  });
  return ensureArray<NotificationItem>(res.data);
}

export async function markNotificationRead(id: string, accountId?: string): Promise<unknown> {
  const res = await api.post<unknown>(
    `/notifications/${id}/read`,
    {},
    { params: accountId ? { account_id: accountId } : undefined },
  );
  return res.data;
}

export async function sendNotification(payload: SendNotificationPayload): Promise<unknown> {
  const res = await api.post<unknown>('/admin/notifications', payload);
  return res.data;
}

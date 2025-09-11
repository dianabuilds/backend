import type { CampaignCreate, CampaignFilters, CampaignUpdate } from '../openapi';
import { ensureArray, withQueryParams } from '../shared/utils';
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

export async function listNotifications(placement?: string): Promise<NotificationItem[]> {
  const url = withQueryParams('/notifications', {
    placement,
  });
  const res = await api.get<NotificationItem[]>(url);
  return ensureArray<NotificationItem>(res.data);
}

export async function markNotificationRead(id: string): Promise<unknown> {
  const url = withQueryParams(`/notifications/${id}/read`, {});
  const res = await api.post<unknown>(url, {});
  return res.data;
}

export type SendNotificationInput = {
  user_id: string;
  title: string;
  message: string;
  type?: string;
  placement?: string;
};

export async function sendNotification(payload: SendNotificationInput): Promise<unknown> {
  const res = await api.post<unknown>('/admin/notifications', payload);
  return res.data;
}

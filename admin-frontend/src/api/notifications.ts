import { api } from "./client";

export interface BroadcastFilters {
  role?: string | null;
  is_active?: boolean | null;
  is_premium?: boolean | null;
  created_from?: string | null;
  created_to?: string | null;
}

export interface BroadcastCreate {
  title: string;
  message: string;
  type?: "system" | "info" | "warning" | "quest";
  filters?: BroadcastFilters;
  dry_run?: boolean;
}

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

export async function createBroadcast(payload: BroadcastCreate) {
  const res = await api.post("/admin/notifications/broadcast", payload);
  return res.data as any;
}

export async function listBroadcasts(): Promise<Campaign[]> {
  const res = await api.get<{ items?: Campaign[] } | Campaign[]>("/admin/notifications/broadcast");
  const d = (res.data as any);
  if (Array.isArray(d)) return d as Campaign[];
  return (d?.items || []) as Campaign[];
}

export async function getCampaign(id: string): Promise<Campaign> {
  const res = await api.get<Campaign>(`/admin/notifications/broadcast/${id}`);
  return res.data as Campaign;
}

export async function cancelCampaign(id: string) {
  const res = await api.post(`/admin/notifications/broadcast/${id}/cancel`, {});
  return res.data as any;
}

import { api } from "./client";

export interface FeatureFlag {
  key: string;
  value: boolean;
  description?: string | null;
  updated_at?: string | null;
  updated_by?: string | null;
}

export interface FeatureFlagUpdate {
  value?: boolean;
  description?: string;
}

export async function listFlags(): Promise<FeatureFlag[]> {
  const res = await api.get<FeatureFlag[]>("/admin/flags");
  return (res.data || []) as FeatureFlag[];
}

export async function updateFlag(key: string, patch: FeatureFlagUpdate): Promise<FeatureFlag> {
  const res = await api.patch<FeatureFlag>(`/admin/flags/${encodeURIComponent(key)}`, patch);
  return res.data as FeatureFlag;
}

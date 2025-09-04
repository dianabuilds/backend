import { ensureArray, withQueryParams } from "../shared/utils";
import { api } from "./client";

export interface AchievementAdmin {
  id: string;
  code: string;
  title: string;
  description?: string | null;
  icon?: string | null;
  visible: boolean;
  condition: Record<string, unknown>;
}

export async function listAdminAchievements(params: {
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<AchievementAdmin[]> {
  const res = await api.get<AchievementAdmin[]>(
    withQueryParams("/admin/achievements", params),
  );
  return ensureArray<AchievementAdmin>(res.data);
}

export async function createAdminAchievement(
  body: Partial<AchievementAdmin> & { code: string; title: string },
): Promise<AchievementAdmin> {
  const res = await api.post<AchievementAdmin>("/admin/achievements", body);
  return res.data as AchievementAdmin;
}

export async function updateAdminAchievement(
  id: string,
  patch: Partial<AchievementAdmin>,
): Promise<AchievementAdmin> {
  const res = await api.patch<AchievementAdmin>(
    `/admin/achievements/${encodeURIComponent(id)}`,
    patch,
  );
  return res.data as AchievementAdmin;
}

export async function deleteAdminAchievement(id: string): Promise<void> {
  await api.del(`/admin/achievements/${encodeURIComponent(id)}`);
}

export async function grantAchievement(
  id: string,
  user_id: string,
  reason?: string,
): Promise<void> {
  await api.post(`/admin/achievements/${id}/grant`, { user_id, reason });
}

export async function revokeAchievement(
  id: string,
  user_id: string,
  reason?: string,
): Promise<void> {
  await api.post(`/admin/achievements/${id}/revoke`, { user_id, reason });
}


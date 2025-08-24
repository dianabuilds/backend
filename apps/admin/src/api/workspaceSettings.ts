import { api } from "./client";

export async function getAIPresets(workspaceId: string): Promise<Record<string, any>> {
  const res = await api.get<Record<string, any>>(
    `/admin/workspaces/${workspaceId}/settings/ai-presets`,
  );
  return res.data ?? {};
}

export async function saveAIPresets(
  workspaceId: string,
  presets: Record<string, any>,
): Promise<Record<string, any>> {
  const res = await api.put<Record<string, any>>(
    `/admin/workspaces/${workspaceId}/settings/ai-presets`,
    presets,
  );
  return res.data ?? {};
}

export async function getNotificationRules(
  workspaceId: string,
): Promise<Record<string, any>> {
  const res = await api.get<Record<string, any>>(
    `/admin/workspaces/${workspaceId}/settings/notifications`,
  );
  return res.data ?? {};
}

export async function saveNotificationRules(
  workspaceId: string,
  rules: Record<string, any>,
): Promise<Record<string, any>> {
  const res = await api.put<Record<string, any>>(
    `/admin/workspaces/${workspaceId}/settings/notifications`,
    rules,
  );
  return res.data ?? {};
}

export async function getLimits(
  workspaceId: string,
): Promise<Record<string, number>> {
  const res = await api.get<Record<string, number>>(
    `/admin/workspaces/${workspaceId}/settings/limits`,
  );
  return res.data ?? {};
}

export async function saveLimits(
  workspaceId: string,
  limits: Record<string, number>,
): Promise<Record<string, number>> {
  const res = await api.put<Record<string, number>>(
    `/admin/workspaces/${workspaceId}/settings/limits`,
    limits,
  );
  return res.data ?? {};
}


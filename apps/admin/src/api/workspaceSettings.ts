import { api } from "./client";

export type AIPresets = {
  provider?: string;
  model?: string;
  temperature?: number;
  system_prompt?: string;
  forbidden?: string[];
};

export type NotificationChannel = "in-app" | "email" | "webhook";

export type NotificationRules = {
  achievement: NotificationChannel[];
  publish: NotificationChannel[];
};

export type WorkspaceLimits = {
  ai_tokens: number;
  notif_per_day: number;
  compass_calls: number;
};

export async function getAIPresets(workspaceId: string): Promise<AIPresets> {
  const res = await api.get<AIPresets>(
    `/admin/accounts/${workspaceId}/settings/ai-presets`,
  );
  return res.data ?? {};
}

export async function saveAIPresets(
  workspaceId: string,
  presets: AIPresets,
): Promise<AIPresets> {
  const res = await api.put<AIPresets>(
    `/admin/accounts/${workspaceId}/settings/ai-presets`,
    presets,
  );
  return res.data ?? {};
}

export async function validateAIPresets(
  workspaceId: string,
  presets: AIPresets,
): Promise<void> {
  await api.post(
    `/admin/accounts/${workspaceId}/settings/ai-presets/validate`,
    presets,
  );
}

export async function getNotificationRules(
  workspaceId: string,
): Promise<NotificationRules> {
  const res = await api.get<NotificationRules>(
    `/admin/accounts/${workspaceId}/settings/notifications`,
  );
  return (
    res.data ?? {
      achievement: [],
      publish: [],
    }
  );
}

export async function saveNotificationRules(
  workspaceId: string,
  rules: NotificationRules,
): Promise<NotificationRules> {
  const res = await api.put<NotificationRules>(
    `/admin/accounts/${workspaceId}/settings/notifications`,
    rules,
  );
  return res.data ?? {
    achievement: [],
    publish: [],
  };
}

export async function validateNotificationRules(
  workspaceId: string,
  rules: NotificationRules,
): Promise<void> {
  await api.post(
    `/admin/accounts/${workspaceId}/settings/notifications/validate`,
    rules,
  );
}

export async function getLimits(
  workspaceId: string,
): Promise<WorkspaceLimits> {
  const res = await api.get<WorkspaceLimits>(
    `/admin/accounts/${workspaceId}/settings/limits`,
  );
  return (
    res.data ?? {
      ai_tokens: 0,
      notif_per_day: 0,
      compass_calls: 0,
    }
  );
}

export async function saveLimits(
  workspaceId: string,
  limits: WorkspaceLimits,
): Promise<WorkspaceLimits> {
  const res = await api.put<WorkspaceLimits>(
    `/admin/accounts/${workspaceId}/settings/limits`,
    limits,
  );
  return res.data ?? {
    ai_tokens: 0,
    notif_per_day: 0,
    compass_calls: 0,
  };
}

export async function validateLimits(
  workspaceId: string,
  limits: WorkspaceLimits,
): Promise<void> {
  await api.post(
    `/admin/accounts/${workspaceId}/settings/limits/validate`,
    limits,
  );
}


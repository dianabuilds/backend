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

export type AccountLimits = {
  ai_tokens: number;
  notif_per_day: number;
  compass_calls: number;
};

export async function getAIPresets(accountId: string): Promise<AIPresets> {
  const res = await api.get<AIPresets>(
    `/admin/accounts/${accountId}/settings/ai-presets`,
  );
  return res.data ?? {};
}

export async function saveAIPresets(
  accountId: string,
  presets: AIPresets,
): Promise<AIPresets> {
  const res = await api.put<AIPresets>(
    `/admin/accounts/${accountId}/settings/ai-presets`,
    presets,
  );
  return res.data ?? {};
}

export async function validateAIPresets(
  accountId: string,
  presets: AIPresets,
): Promise<void> {
  await api.post(
    `/admin/accounts/${accountId}/settings/ai-presets/validate`,
    presets,
  );
}

export async function getNotificationRules(
  accountId: string,
): Promise<NotificationRules> {
  const res = await api.get<NotificationRules>(
    `/admin/accounts/${accountId}/settings/notifications`,
  );
  return (
    res.data ?? {
      achievement: [],
      publish: [],
    }
  );
}

export async function saveNotificationRules(
  accountId: string,
  rules: NotificationRules,
): Promise<NotificationRules> {
  const res = await api.put<NotificationRules>(
    `/admin/accounts/${accountId}/settings/notifications`,
    rules,
  );
  return res.data ?? {
    achievement: [],
    publish: [],
  };
}

export async function validateNotificationRules(
  accountId: string,
  rules: NotificationRules,
): Promise<void> {
  await api.post(
    `/admin/accounts/${accountId}/settings/notifications/validate`,
    rules,
  );
}

export async function getLimits(
  accountId: string,
): Promise<AccountLimits> {
  const res = await api.get<AccountLimits>(
    `/admin/accounts/${accountId}/settings/limits`,
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
  accountId: string,
  limits: AccountLimits,
): Promise<AccountLimits> {
  const res = await api.put<AccountLimits>(
    `/admin/accounts/${accountId}/settings/limits`,
    limits,
  );
  return res.data ?? {
    ai_tokens: 0,
    notif_per_day: 0,
    compass_calls: 0,
  };
}

export async function validateLimits(
  accountId: string,
  limits: AccountLimits,
): Promise<void> {
  await api.post(
    `/admin/accounts/${accountId}/settings/limits/validate`,
    limits,
  );
}


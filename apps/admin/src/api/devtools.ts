import { api } from "./client";

export interface DevToolsSettings {
  env_mode?: string;
  preview_default?: string;
  allow_external_calls?: boolean;
  rng_seed_strategy?: string;
  providers?: Record<string, string>;
}

export async function getDevToolsSettings(): Promise<DevToolsSettings> {
  const res = await api.get<DevToolsSettings>("/admin/devtools");
  return res.data ?? {};
}

export async function updateDevToolsSettings(
  body: Partial<DevToolsSettings>,
): Promise<DevToolsSettings> {
  const res = await api.put<DevToolsSettings>("/admin/devtools", body);
  return res.data ?? {};
}


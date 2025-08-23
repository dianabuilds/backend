import type { FeatureFlagOut, FeatureFlagUpdateIn } from "../openapi";
import { api } from "./client";

export async function listFlags(): Promise<FeatureFlagOut[]> {
  const res = await api.get<FeatureFlagOut[]>("/admin/flags");
  return res.data ?? [];
}

export async function updateFlag(
  key: string,
  patch: FeatureFlagUpdateIn,
): Promise<FeatureFlagOut> {
  const res = await api.patch<FeatureFlagOut>(
    `/admin/flags/${encodeURIComponent(key)}`,
    patch,
  );
  return res.data!;
}

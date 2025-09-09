import type { FeatureFlagOut, FeatureFlagUpdateIn } from '../openapi';
import { api } from './client';

export interface ListFlagsParams {
  q?: string;
  limit?: number;
  offset?: number;
}

export async function listFlags(params: ListFlagsParams = {}): Promise<FeatureFlagOut[]> {
  const qs = new URLSearchParams();
  if (params.q) qs.set('q', params.q);
  if (typeof params.limit === 'number') qs.set('limit', String(params.limit));
  if (typeof params.offset === 'number') qs.set('offset', String(params.offset));
  const res = await api.get<FeatureFlagOut[]>(`/admin/flags${qs.size ? `?${qs.toString()}` : ''}`);
  return res.data ?? [];
}

export async function updateFlag(key: string, patch: FeatureFlagUpdateIn): Promise<FeatureFlagOut> {
  const res = await api.patch<FeatureFlagUpdateIn, FeatureFlagOut>(
    `/admin/flags/${encodeURIComponent(key)}`,
    patch,
  );
  return res.data!;
}

export type { FeatureFlagOut as FeatureFlag } from '../openapi';

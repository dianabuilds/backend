import { apiDelete, apiGet, apiPost } from '../client';
import type {
  FeatureFlag,
  FeatureFlagTester,
  FeatureFlagUpsertPayload,
  FeatureFlagStatus,
} from '../../types/management';
import { ensureArray, isObjectRecord, pickBoolean, pickNullableString, pickNumber, pickString } from './utils';

type FetchFlagsOptions = {
  signal?: AbortSignal;
};

type SaveFlagOptions = {
  signal?: AbortSignal;
};

type DeleteFlagOptions = {
  signal?: AbortSignal;
};

type SearchTestersOptions = {
  limit?: number;
  signal?: AbortSignal;
};

const FLAGS_ENDPOINT = '/v1/flags';

const FLAG_TESTERS_ENDPOINT = '/v1/users/search';
const FLAG_STATUSES: FeatureFlagStatus[] = ['disabled', 'testers', 'premium', 'all', 'custom'];

function normalizeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => pickString(item))
    .filter((item): item is string => Boolean(item && item.length));
}

function normalizeFlagRule(value: unknown) {
  if (!isObjectRecord(value)) {
    return null;
  }
  const type = pickString(value.type);
  const ruleValue = pickString(value.value);
  if (!type || !ruleValue) {
    return null;
  }
  return {
    type,
    value: ruleValue,
    rollout: pickNumber(value.rollout) ?? null,
    priority: pickNumber(value.priority) ?? 0,
    meta: isObjectRecord(value.meta) ? value.meta : undefined,
  };
}

function normalizeFlag(value: unknown): FeatureFlag | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const slug = pickString(value.slug);
  if (!slug) {
    return null;
  }
  const statusRaw = pickString(value.status) ?? 'disabled';
  const status = (FLAG_STATUSES.includes(statusRaw as FeatureFlagStatus)
    ? (statusRaw as FeatureFlagStatus)
    : 'disabled');

  const flag: FeatureFlag = {
    slug,
    status,
    label: pickNullableString(value.label) ?? undefined,
    description: pickNullableString(value.description) ?? undefined,
    status_label: pickNullableString(value.status_label) ?? undefined,
    audience: pickNullableString(value.audience) ?? undefined,
    enabled: pickBoolean(value.enabled) ?? false,
    effective: pickBoolean(value.effective) ?? null,
    rollout: pickNumber(value.rollout) ?? null,
    release_percent: pickNumber(value.release_percent) ?? null,
    testers: normalizeStringArray(value.testers),
    roles: normalizeStringArray(value.roles),
    segments: normalizeStringArray(value.segments),
    rules: ensureArray(value.rules, normalizeFlagRule),
    meta: isObjectRecord(value.meta) ? value.meta : null,
    created_at: pickNullableString(value.created_at),
    updated_at: pickNullableString(value.updated_at),
    evaluated_at: pickNullableString(value.evaluated_at),
  };

  return flag;
}

function normalizeTester(value: unknown): FeatureFlagTester | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  if (!id) {
    return null;
  }
  return {
    id,
    username: pickNullableString(value.username) ?? undefined,
  };
}

export async function fetchFeatureFlags({ signal }: FetchFlagsOptions = {}): Promise<FeatureFlag[]> {
  const response = await apiGet<{ items?: unknown[] }>(FLAGS_ENDPOINT, { signal });
  return ensureArray(response?.items, normalizeFlag);
}

export async function saveFeatureFlag(payload: FeatureFlagUpsertPayload, { signal }: SaveFlagOptions = {}): Promise<void> {
  await apiPost(FLAGS_ENDPOINT, payload, { signal });
}

export async function deleteFeatureFlag(slug: string, { signal }: DeleteFlagOptions = {}): Promise<void> {
  const trimmed = slug.trim();
  if (!trimmed) {
    throw new Error('flag_slug_missing');
  }
  await apiDelete(`${FLAGS_ENDPOINT}/${encodeURIComponent(trimmed)}`, { signal });
}
export async function searchFeatureFlagUsers(
  query: string,
  { limit = 10, signal }: SearchTestersOptions = {},
): Promise<FeatureFlagTester[]> {
  const trimmed = query.trim();
  if (!trimmed) {
    return [];
  }
  const params = new URLSearchParams({ q: trimmed });
  if (limit) {
    params.set('limit', String(limit));
  }
  const response = await apiGet<unknown[]>(`${FLAG_TESTERS_ENDPOINT}?${params.toString()}`, { signal });
  return ensureArray(response, normalizeTester);
}
export const managementFlagsApi = {
  fetchFeatureFlags,
  saveFeatureFlag,
  deleteFeatureFlag,
  searchFeatureFlagUsers,
};





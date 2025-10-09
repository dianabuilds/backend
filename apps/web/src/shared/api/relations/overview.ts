import { apiGet } from '../client';
import type {
  RelationLink,
  RelationsDiversitySnapshot,
  RelationsOverview,
  RelationStrategyOverview,
} from '../../types/relations';
import {
  ensureArray,
  isObjectRecord,
  pickBoolean,
  pickNullableString,
  pickNumber,
  pickString,
} from './utils';

const RELATIONS_OVERVIEW_ENDPOINT = '/v1/navigation/relations/overview';
const RELATIONS_TOP_ENDPOINT = '/v1/navigation/relations/top';

function normalizeStrategy(value: unknown): RelationStrategyOverview | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const key = pickString(value.key);
  if (!key) {
    return null;
  }
  return {
    key,
    weight: pickNumber(value.weight) ?? 0,
    enabled: pickBoolean(value.enabled) ?? false,
    usageShare: pickNumber(value.usage_share) ?? null,
    links: pickNumber(value.links) ?? null,
    updatedAt: pickNullableString(value.updated_at) ?? null,
  };
}

function normalizeLink(value: unknown): RelationLink | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const sourceId = pickString(value.source_id) ?? pickString(value.sourceId);
  const targetId = pickString(value.target_id) ?? pickString(value.targetId);
  if (!sourceId || !targetId) {
    return null;
  }
  return {
    sourceId,
    sourceTitle: pickNullableString(value.source_title) ?? pickNullableString(value.sourceTitle) ?? null,
    sourceSlug: pickNullableString(value.source_slug) ?? pickNullableString(value.sourceSlug) ?? null,
    targetId,
    targetTitle: pickNullableString(value.target_title) ?? pickNullableString(value.targetTitle) ?? null,
    targetSlug: pickNullableString(value.target_slug) ?? pickNullableString(value.targetSlug) ?? null,
    score: pickNumber(value.score) ?? null,
    algo: pickNullableString(value.algo) ?? null,
    updatedAt: pickNullableString(value.updated_at) ?? pickNullableString(value.updatedAt) ?? null,
  };
}

function normalizeDiversity(value: unknown): RelationsDiversitySnapshot {
  if (!isObjectRecord(value)) {
    return {
      coverage: null,
      entropy: null,
      gini: null,
    };
  }
  return {
    coverage: pickNumber(value.coverage) ?? null,
    entropy: pickNumber(value.entropy) ?? null,
    gini: pickNumber(value.gini) ?? null,
  };
}

function normalizePopularMap(value: unknown): Record<string, RelationLink[]> {
  if (!isObjectRecord(value)) {
    return {};
  }
  const result: Record<string, RelationLink[]> = {};
  for (const [key, list] of Object.entries(value)) {
    const normalizedKey = pickString(key);
    if (!normalizedKey) continue;
    result[normalizedKey] = ensureArray(list, normalizeLink);
  }
  return result;
}

function normalizeOverview(payload: unknown): RelationsOverview {
  if (!isObjectRecord(payload)) {
    return {
      strategies: [],
      diversity: {
        coverage: null,
        entropy: null,
        gini: null,
      },
      popular: {},
    };
  }
  return {
    strategies: ensureArray(payload.strategies, normalizeStrategy),
    diversity: normalizeDiversity(payload.diversity),
    popular: normalizePopularMap(payload.popular),
  };
}

export async function fetchRelationsOverview(options: { signal?: AbortSignal } = {}): Promise<RelationsOverview> {
  const raw = await apiGet<unknown>(RELATIONS_OVERVIEW_ENDPOINT, { signal: options.signal });
  return normalizeOverview(raw);
}

export async function fetchTopRelations(algoKey: string, options: { signal?: AbortSignal } = {}): Promise<RelationLink[]> {
  const trimmed = algoKey.trim();
  if (!trimmed) {
    return [];
  }
  const response = await apiGet<unknown>(`${RELATIONS_TOP_ENDPOINT}?algo=${encodeURIComponent(trimmed)}`, {
    signal: options.signal,
  });
  if (Array.isArray((response as any)?.items)) {
    return ensureArray((response as any).items, normalizeLink);
  }
  if (Array.isArray((response as any)?.relations)) {
    return ensureArray((response as any).relations, normalizeLink);
  }
  return ensureArray(response, normalizeLink);
}

export function computeStrategiesMetrics(strategies: RelationStrategyOverview[]): {
  total: number;
  enabled: number;
  disabled: number;
  totalLinks: number;
  avgWeight: number;
} {
  if (!strategies.length) {
    return { total: 0, enabled: 0, disabled: 0, totalLinks: 0, avgWeight: 0 };
  }
  const total = strategies.length;
  const enabled = strategies.filter((strategy) => strategy.enabled).length;
  const totalLinks = strategies.reduce((acc, strategy) => acc + (strategy.links ?? 0), 0);
  const avgWeight = strategies.reduce((acc, strategy) => acc + (strategy.weight ?? 0), 0) / total;
  return { total, enabled, disabled: total - enabled, totalLinks, avgWeight };
}

export function computeLastUpdated(strategies: RelationStrategyOverview[]): string | null {
  const timestamps = strategies
    .map((strategy) => {
      const value = strategy.updatedAt;
      if (!value) return null;
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? null : date.getTime();
    })
    .filter((value): value is number => typeof value === 'number');
  if (!timestamps.length) {
    return null;
  }
  const latest = Math.max(...timestamps);
  return new Date(latest).toISOString();
}



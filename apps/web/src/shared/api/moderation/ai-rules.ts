import { apiDelete, apiGet, apiPatch, apiPost } from '../client';
import type { ModerationAIRule, ModerationAIRulesList } from '../../types/moderation';
import {
  ensureArray,
  isObjectRecord,
  pickBoolean,
  pickNullableString,
  pickNumber,
  pickString,
} from './utils';

export type FetchModerationAIRulesParams = {
  limit?: number;
  offset?: number;
  search?: string;
  enabled?: boolean;
  signal?: AbortSignal;
};

export type CreateModerationAIRulePayload = {
  category: string;
  description?: string | null;
  defaultAction?: string | null;
  threshold?: number | null;
  enabled?: boolean;
};

export type UpdateModerationAIRulePayload = {
  description?: string | null;
  defaultAction?: string | null;
  threshold?: number | null;
  enabled?: boolean;
};

function normalizeRule(raw: unknown, index: number): ModerationAIRule | null {
  const source = isObjectRecord(raw) ? raw : {};
  const id = pickString(source.id) ?? `rule-${index}`;
  const category = pickString(source.category) ?? id;
  const enabled = pickBoolean(source.enabled) ?? false;
  const description = pickNullableString(source.description) ?? null;
  const defaultAction = pickNullableString(source.default_action ?? source.defaultAction) ?? null;
  const threshold = pickNumber(source.threshold) ?? null;
  const updatedBy = pickNullableString(source.updated_by ?? source.updatedBy) ?? null;
  const updatedAt = pickNullableString(source.updated_at ?? source.updatedAt) ?? null;
  const metrics = isObjectRecord(source.metrics) ? source.metrics : undefined;
  const meta = isObjectRecord(source.meta) ? source.meta : undefined;

  if (!id) return null;

  return {
    id,
    category,
    enabled,
    description,
    default_action: defaultAction,
    threshold,
    updated_by: updatedBy,
    updated_at: updatedAt,
    metrics,
    meta,
  };
}

function buildListPath({ limit, offset, search, enabled }: FetchModerationAIRulesParams): string {
  const params = new URLSearchParams();
  params.set('limit', String(limit ?? 10));
  params.set('offset', String(offset ?? 0));
  if (search && search.trim()) {
    params.set('q', search.trim());
  }
  if (typeof enabled === 'boolean') {
    params.set('enabled', enabled ? 'true' : 'false');
  }
  const query = params.toString();
  return query ? `/api/moderation/ai-rules?${query}` : '/api/moderation/ai-rules';
}

function mapRulePayload(payload: UpdateModerationAIRulePayload | CreateModerationAIRulePayload): Record<string, unknown> {
  const body: Record<string, unknown> = {};
  if ('category' in payload) {
    const trimmedCategory = payload.category.trim();
    if (!trimmedCategory) {
      throw new Error('moderation_air_rule_category_missing');
    }
    body.category = trimmedCategory;
  }
  if (payload.description !== undefined) {
    const description = payload.description ?? null;
    body.description = description && description.trim() ? description.trim() : null;
  }
  if (payload.defaultAction !== undefined) {
    const action = payload.defaultAction ?? null;
    body.default_action = action && action.trim() ? action.trim() : null;
  }
  if (payload.threshold !== undefined) {
    const value = payload.threshold;
    body.threshold = value == null ? null : value;
  }
  if (payload.enabled !== undefined) {
    body.enabled = Boolean(payload.enabled);
  }
  return body;
}

export async function fetchModerationAIRules(
  params: FetchModerationAIRulesParams = {},
): Promise<ModerationAIRulesList> {
  const { limit = 10, offset = 0, signal } = params;
  const path = buildListPath({ ...params, limit, offset });
  const payload = await apiGet<unknown>(path, { signal });
  const source = isObjectRecord(payload) ? payload : {};

  const items = ensureArray(source.items, (item, index) => normalizeRule(item, index)).filter(
    (rule): rule is ModerationAIRule => rule !== null,
  );
  const total = pickNumber(source.total);
  const hasNext = total != null ? offset + limit < total : items.length === limit;

  return {
    items,
    total: total ?? undefined,
    hasNext,
  };
}

export async function createModerationAIRule(
  payload: CreateModerationAIRulePayload,
  options: { signal?: AbortSignal } = {},
): Promise<ModerationAIRule> {
  const body = mapRulePayload(payload);
  const response = await apiPost<unknown>('/api/moderation/ai-rules', body, { signal: options.signal });
  const normalized = normalizeRule(response, 0);
  if (!normalized) {
    throw new Error('moderation_air_rule_create_failed');
  }
  return normalized;
}

export async function updateModerationAIRule(
  ruleId: string,
  payload: UpdateModerationAIRulePayload,
  options: { signal?: AbortSignal } = {},
): Promise<ModerationAIRule> {
  const trimmed = ruleId.trim();
  if (!trimmed) {
    throw new Error('moderation_air_rule_id_missing');
  }
  const body = mapRulePayload(payload);
  const response = await apiPatch<unknown>(`/api/moderation/ai-rules/${encodeURIComponent(trimmed)}`, body, {
    signal: options.signal,
  });
  const normalized = normalizeRule(response, 0);
  if (!normalized) {
    throw new Error('moderation_air_rule_update_failed');
  }
  return normalized;
}

export async function deleteModerationAIRule(ruleId: string, options: { signal?: AbortSignal } = {}): Promise<void> {
  const trimmed = ruleId.trim();
  if (!trimmed) {
    throw new Error('moderation_air_rule_id_missing');
  }
  await apiDelete(`/api/moderation/ai-rules/${encodeURIComponent(trimmed)}`, { signal: options.signal });
}

import { apiPatch } from '../client';
import type { RelationStrategyUpdatePayload } from '../../types/relations';

const RELATIONS_STRATEGIES_ENDPOINT = '/v1/navigation/relations/strategies';

type RequestOptions = {
  signal?: AbortSignal;
};

function normalizeKey(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    throw new Error('relations_strategy_key_missing');
  }
  return trimmed;
}

export async function updateRelationStrategy(
  key: string,
  payload: RelationStrategyUpdatePayload,
  options: RequestOptions = {},
): Promise<void> {
  const normalizedKey = normalizeKey(key);
  if (typeof payload.weight !== 'number' || Number.isNaN(payload.weight)) {
    throw new Error('relations_strategy_weight_invalid');
  }
  const body: Record<string, unknown> = {
    weight: payload.weight,
    enabled: Boolean(payload.enabled),
  };
  await apiPatch(
    `${RELATIONS_STRATEGIES_ENDPOINT}/${encodeURIComponent(normalizedKey)}`,
    body,
    { signal: options.signal },
  );
}

export const relationsStrategiesApi = {
  updateRelationStrategy,
};



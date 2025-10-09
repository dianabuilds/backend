import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
  apiPatch: vi.fn(),
}));

import { apiGet, apiPatch } from './client';
import type { RelationStrategyOverview } from '../types/relations';
import {
  computeLastUpdated,
  computeStrategiesMetrics,
  fetchRelationsOverview,
  fetchTopRelations,
  updateRelationStrategy,
} from './relations';

const mockedApiGet = vi.mocked(apiGet);
const mockedApiPatch = vi.mocked(apiPatch);

describe('relations api', () => {
  beforeEach(() => {
    mockedApiGet.mockReset();
    mockedApiPatch.mockReset();
  });

  it('normalizes relations overview response', async () => {
    mockedApiGet.mockResolvedValue({
      strategies: [
        {
          key: 'embedding',
          weight: '0.35',
          enabled: 'true',
          usage_share: '0.42',
          links: '120',
          updated_at: '2025-10-05T12:00:00Z',
        },
        { key: 'fts', weight: null, enabled: false },
        {},
      ],
      diversity: { coverage: '0.73', entropy: '1.23', gini: '0.12' },
      popular: {
        embedding: [
          {
            source_id: 1,
            source_title: 'Node A',
            target_id: '2',
            target_slug: 'node-b',
            score: '0.89',
            updated_at: '2025-10-05T12:10:00Z',
          },
          'invalid',
        ],
      },
    });

    const overview = await fetchRelationsOverview();

    expect(mockedApiGet).toHaveBeenCalledWith('/v1/navigation/relations/overview', { signal: undefined });
    expect(overview.strategies).toEqual([
      {
        key: 'embedding',
        weight: 0.35,
        enabled: true,
        usageShare: 0.42,
        links: 120,
        updatedAt: '2025-10-05T12:00:00Z',
      },
      {
        key: 'fts',
        weight: 0,
        enabled: false,
        usageShare: null,
        links: null,
        updatedAt: null,
      },
    ]);
    expect(overview.diversity).toEqual({ coverage: 0.73, entropy: 1.23, gini: 0.12 });
    expect(overview.popular.embedding).toEqual([
      {
        sourceId: '1',
        sourceTitle: 'Node A',
        sourceSlug: null,
        targetId: '2',
        targetTitle: null,
        targetSlug: 'node-b',
        score: 0.89,
        algo: null,
        updatedAt: '2025-10-05T12:10:00Z',
      },
    ]);
  });

  it('returns empty overview for malformed payload', async () => {
    mockedApiGet.mockResolvedValue(null);
    const overview = await fetchRelationsOverview();
    expect(overview).toEqual({ strategies: [], diversity: { coverage: null, entropy: null, gini: null }, popular: {} });
  });

  it('fetches top relations from legacy payload shape', async () => {
    mockedApiGet.mockResolvedValue({ items: [{ source_id: 'a', target_id: 'b' }] });
    const relations = await fetchTopRelations(' embedding ');
    expect(mockedApiGet).toHaveBeenCalledWith('/v1/navigation/relations/top?algo=embedding', { signal: undefined });
    expect(relations).toEqual([
      {
        sourceId: 'a',
        sourceTitle: null,
        sourceSlug: null,
        targetId: 'b',
        targetTitle: null,
        targetSlug: null,
        score: null,
        algo: null,
        updatedAt: null,
      },
    ]);
  });

  it('falls back to empty list when algo key missing', async () => {
    const relations = await fetchTopRelations('   ');
    expect(relations).toEqual([]);
    expect(mockedApiGet).not.toHaveBeenCalled();
  });

  it('updates relation strategy with trimmed key', async () => {
    mockedApiPatch.mockResolvedValue(undefined);
    await updateRelationStrategy('  mix  ', { weight: 0.42, enabled: true });
    expect(mockedApiPatch).toHaveBeenCalledWith(
      '/v1/navigation/relations/strategies/mix',
      { weight: 0.42, enabled: true },
      { signal: undefined },
    );
  });

  it('throws when strategy key is missing', async () => {
    await expect(updateRelationStrategy('   ', { weight: 0.3, enabled: true })).rejects.toThrow(
      'relations_strategy_key_missing',
    );
  });

  it('computes metrics and last updated helpers', () => {
    const strategies: RelationStrategyOverview[] = [
      { key: 'a', weight: 0.5, enabled: true, usageShare: 0.2, links: 10, updatedAt: '2025-10-01T00:00:00Z' },
      { key: 'b', weight: 0.25, enabled: false, usageShare: 0.1, links: 5, updatedAt: '2025-10-02T00:00:00Z' },
    ];

    const metrics = computeStrategiesMetrics(strategies);
    expect(metrics).toEqual({ total: 2, enabled: 1, disabled: 1, totalLinks: 15, avgWeight: 0.375 });
    expect(computeLastUpdated(strategies)).toBe('2025-10-02T00:00:00.000Z');
  });
});



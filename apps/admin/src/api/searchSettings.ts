import { api } from './client';

export interface RelevanceWeights {
  title: number;
  body: number;
  tags: number;
  author: number;
}

export interface RelevanceBoosts {
  freshness: { half_life_days: number };
  popularity: { weight: number };
}

export interface RelevanceQueryParams {
  fuzziness: string;
  min_should_match: string;
  phrase_slop: number;
  tie_breaker?: number | null;
}

export interface RelevancePayload {
  weights: RelevanceWeights;
  boosts: RelevanceBoosts;
  query: RelevanceQueryParams;
}

export interface RelevanceGetOut {
  version: number;
  payload: RelevancePayload;
  updated_at: string;
}

export interface DryRunDiffItem {
  query: string;
  topBefore: string[];
  topAfter: string[];
  moved: { id: string; from: number; to: number }[];
}

export interface RelevanceDryRunOut {
  diff: DryRunDiffItem[];
  warnings: string[];
}

export async function getRelevance(): Promise<RelevanceGetOut> {
  const res = await api.get<RelevanceGetOut>('/admin/search/relevance');
  return res.data!;
}

export async function dryRunRelevance(
  payload: RelevancePayload,
  sample: string[],
): Promise<RelevanceDryRunOut> {
  const res = await api.put<
    { payload: RelevancePayload; dryRun: boolean; sample: string[] },
    RelevanceDryRunOut
  >('/admin/search/relevance', {
    payload,
    dryRun: true,
    sample,
  });
  return res.data!;
}

export async function applyRelevance(
  payload: RelevancePayload,
  comment?: string,
): Promise<RelevanceGetOut> {
  const res = await api.put<
    { payload: RelevancePayload; dryRun: boolean; comment?: string },
    RelevanceGetOut
  >('/admin/search/relevance', {
    payload,
    dryRun: false,
    comment,
  });
  return res.data!;
}

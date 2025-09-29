import type { FallbackRule, LLMSummary, UsageRow } from './types';

export function buildUsageRows(metrics: LLMSummary | null): UsageRow[] {
  const rows = new Map<string, UsageRow>();

  const ensure = (provider?: string, model?: string) => {
    const key = `${provider || 'n/a'}:${model || 'n/a'}`;
    if (!rows.has(key)) {
      rows.set(key, {
        key,
        provider: provider || 'n/a',
        model: model || 'n/a',
        calls: 0,
        errors: 0,
        promptTokens: 0,
        completionTokens: 0,
        costUsd: 0,
        latencyMs: null,
      });
    }
    return rows.get(key)!;
  };

  (metrics?.calls || []).forEach((row) => {
    const entry = ensure(row.provider, row.model);
    if (row.type === 'errors') entry.errors += row.count || 0;
    if (row.type === 'calls') entry.calls += row.count || 0;
  });

  (metrics?.tokens_total || []).forEach((row) => {
    const entry = ensure(row.provider, row.model);
    if (row.type === 'prompt') entry.promptTokens += row.total || 0;
    if (row.type === 'completion') entry.completionTokens += row.total || 0;
  });

  (metrics?.cost_usd_total || []).forEach((row) => {
    const entry = ensure(row.provider, row.model);
    entry.costUsd += row.total_usd || 0;
  });

  (metrics?.latency_avg_ms || []).forEach((row) => {
    const entry = ensure(row.provider, row.model);
    if (typeof row.avg_ms === 'number') entry.latencyMs = Math.round(row.avg_ms);
  });

  return Array.from(rows.values()).sort((a, b) => b.calls - a.calls);
}

export function groupFallbacksByPrimary(fallbacks: FallbackRule[]): Map<string, FallbackRule[]> {
  const map = new Map<string, FallbackRule[]>();
  fallbacks.forEach((rule) => {
    if (!rule.primary_model) return;
    const list = map.get(rule.primary_model) || [];
    list.push(rule);
    map.set(rule.primary_model, list);
  });
  return map;
}

export function groupFallbacksBySecondary(fallbacks: FallbackRule[]): Map<string, FallbackRule[]> {
  const map = new Map<string, FallbackRule[]>();
  fallbacks.forEach((rule) => {
    if (!rule.fallback_model) return;
    const list = map.get(rule.fallback_model) || [];
    list.push(rule);
    map.set(rule.fallback_model, list);
  });
  return map;
}

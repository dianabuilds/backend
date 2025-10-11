import React from 'react';
import { ContentLayout } from '@shared/layouts/content';
import { Card, Button, Input, Switch, Badge, Spinner, Skeleton, useToast } from '@ui';
import { Table as UITable } from '@ui/table';
import { apiGet, apiPatch } from '@shared/api/client';
import { extractErrorMessage } from '@shared/utils/errors';
import { translate } from '@shared/i18n/locale';

type StrategyOverview = {
  key: string;
  weight: number;
  enabled: boolean;
  usage_share?: number;
  links?: number;
  updated_at?: string;
};

type DiversitySnapshot = {
  coverage?: number;
  entropy?: number;
  gini?: number;
};

type Relation = {
  source_id: number;
  source_title?: string;
  source_slug?: string;
  target_id: number;
  target_title?: string;
  target_slug?: string;
  score?: number;
  algo?: string;
  updated_at?: string;
};

type OverviewResponse = {
  strategies: StrategyOverview[];
  popular: Record<string, Relation[]>;
  diversity: DiversitySnapshot;
};

type StrategyGuide = {
  title?: string;
  summary: string;
  tips: string[];
};

const FALLBACK_GUIDE: Required<StrategyGuide> = {
  title: 'Strategy',
  summary: 'Preview cached relations and tune how much this strategy should influence the transition engine.',
  tips: [
    'Select a strategy in the library to inspect its cached relations and current settings.',
    'Adjust the weight to rebalance this strategy relative to the other enabled ones.',
    'Refresh the snapshot after you save to pull the newest cache from the backend.',
  ],
};

const STRATEGY_GUIDE: Record<string, StrategyGuide> = {
  tags: {
    title: 'Tag overlap',
    summary: 'Connects nodes that share tags. Reliable when metadata is curated and you want deliberate continuity.',
    tips: [
      'Raise the weight when tags are trustworthy and you need predictable follow-ups.',
      'Lower the weight if tag coverage is sparse or you want more exploratory suggestions.',
    ],
  },
  embedding: {
    title: 'Semantic embeddings',
    summary: 'Surfaces nodes whose embeddings are close in vector space for organic, theme-aware jumps.',
    tips: [
      'Keep the weight moderate if you want embeddings to complement deterministic strategies.',
      'Refresh after bulk content updates so the cache reflects the newest vectors.',
    ],
  },
  fts: {
    title: 'Full-text search',
    summary: 'Uses textual similarity to recommend the next node when tags are missing or inconsistent.',
    tips: [
      'Increase the weight when titles and descriptions are descriptive and accurate.',
      'Disable temporarily if text inputs are noisy to avoid irrelevant jumps.',
    ],
  },
  mix: {
    title: 'Exploration blend',
    summary: 'Alternates between deterministic (tags) and discovery (search or embeddings) picks to keep flows varied.',
    tips: [
      'Great default when you want both relevance and surprise in a single feed.',
      'Tune the weight down if players should mostly stay within curated tracks.',
    ],
  },
  explore: {
    title: 'Exploration mode',
    summary: 'Prioritises novelty by rotating through lesser used nodes, ideal for playtesting and discovery cohorts.',
    tips: [
      'Use for beta cohorts or creative sessions where repetition should stay low.',
      'Combine with lower weights on deterministic strategies so exploration does not overpower the experience.',
    ],
  },
  auto: {
    title: 'Auto orchestrator',
    summary: 'Delegates to the backend to pick whichever strategy currently performs best for the active cohort.',
    tips: [
      'Keep enabled to let telemetry steer players dynamically.',
      'Review cached relations regularly; the mix can shift as the system learns.',
    ],
  },
};

const RELATIONS_TOASTS = {
  updateError: { en: 'Failed to update strategy', ru: 'Не удалось обновить стратегию' },
};

function titleize(value: string): string {
  if (!value) return '';
  return value
    .split(/[-_]/g)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function getStrategyGuide(key: string): Required<StrategyGuide> {
  const preset = STRATEGY_GUIDE[key];
  const fallbackTitle = titleize(key) || FALLBACK_GUIDE.title;
  if (!preset) {
    return { ...FALLBACK_GUIDE, title: fallbackTitle };
  }
  return {
    title: preset.title ?? fallbackTitle,
    summary: preset.summary,
    tips: preset.tips.length > 0 ? preset.tips : FALLBACK_GUIDE.tips,
  };
}

function formatPercent(value?: number): string {
  if (value == null || Number.isNaN(value)) {
    return 'n/a';
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function formatWeight(value?: number): string {
  if (value == null || Number.isNaN(value)) {
    return '0.00';
  }
  return value.toFixed(2);
}

function formatCount(value?: number): string {
  if (value == null || Number.isNaN(value)) {
    return '0';
  }
  return value.toLocaleString();
}

function humanizeTimestamp(value?: string | Date | null): string {
  if (!value) {
    return 'n/a';
  }
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'n/a';
  }
  return date.toLocaleString();
}
export default function RelationsPage() {
  const [strategies, setStrategies] = React.useState<StrategyOverview[]>([]);
  const [diversity, setDiversity] = React.useState<DiversitySnapshot>({});
  const [selectedKey, setSelectedKey] = React.useState<string>('');
  const [relations, setRelations] = React.useState<Relation[]>([]);
  const [loadingRelations, setLoadingRelations] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [editWeight, setEditWeight] = React.useState<number>(0.25);
  const [editEnabled, setEditEnabled] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const [refreshing, setRefreshing] = React.useState(false);
  const [loadingOverview, setLoadingOverview] = React.useState(false);
  const [lastRefreshAt, setLastRefreshAt] = React.useState<Date | null>(null);
  const { pushToast } = useToast();

  const selectedStrategy = React.useMemo(
    () => strategies.find((strategy) => strategy.key === selectedKey),
    [strategies, selectedKey],
  );

  const loadOverview = React.useCallback(
    async (preferredKey?: string) => {
      setLoadingOverview(true);
      try {
        const data = await apiGet<OverviewResponse>('/v1/navigation/relations/overview');
        if (!data) {
          return;
        }
        const available = data.strategies ?? [];
        setStrategies(available);
        setDiversity(data.diversity ?? {});

        if (available.length > 0) {
          let nextKey = preferredKey || selectedKey;
          if (!nextKey || !available.some((strategy) => strategy.key === nextKey)) {
            nextKey = available[0].key;
          }
          const active = available.find((strategy) => strategy.key === nextKey);
          setSelectedKey(nextKey);
          setEditWeight(Number(active?.weight ?? 0));
          setEditEnabled(Boolean(active?.enabled));
          setRelations(data.popular?.[nextKey] ?? []);
        } else {
          setSelectedKey('');
          setRelations([]);
        }
        setError(null);
        setLastRefreshAt(new Date());
      } catch (err: any) {
        setError(String(err?.message || err || 'Failed to load relations overview'));
      } finally {
        setLoadingOverview(false);
      }
    },
    [selectedKey],
  );

  React.useEffect(() => {
    void loadOverview();
  }, [loadOverview]);

  const loadRelations = React.useCallback(async (key: string) => {
    if (!key) {
      setRelations([]);
      return;
    }
    setLoadingRelations(true);
    try {
      const data = await apiGet<{ items?: Relation[] } | { relations?: Relation[] }>(
        `/v1/navigation/relations/top?algo=${encodeURIComponent(key)}`,
      );
      if (Array.isArray((data as any)?.items)) setRelations((data as any).items);
      else if (Array.isArray((data as any)?.relations)) setRelations((data as any).relations);
      else setRelations([]);
    } catch (err) {
      console.warn('Failed to load top relations', err);
      setRelations([]);
    } finally {
      setLoadingRelations(false);
    }
  }, []);

  React.useEffect(() => {
    if (!selectedKey) {
      setRelations([]);
      return;
    }
    if (selectedStrategy) {
      setEditWeight(Number(selectedStrategy.weight ?? 0));
      setEditEnabled(Boolean(selectedStrategy.enabled));
    }
    void loadRelations(selectedKey);
  }, [selectedKey, selectedStrategy, loadRelations]);

  const strategyMetrics = React.useMemo(() => {
    if (!strategies.length) {
      return { total: 0, enabled: 0, disabled: 0, totalLinks: 0, avgWeight: 0 };
    }
    const total = strategies.length;
    const enabled = strategies.filter((strategy) => strategy.enabled).length;
    const totalLinks = strategies.reduce((acc, strategy) => acc + (strategy.links ?? 0), 0);
    const avgWeight =
      strategies.reduce((acc, strategy) => acc + (strategy.weight ?? 0), 0) / total;
    return { total, enabled, disabled: total - enabled, totalLinks, avgWeight };
  }, [strategies]);

  const lastUpdatedAt = React.useMemo(() => {
    const timestamps = strategies
      .map((strategy) => (strategy.updated_at ? new Date(strategy.updated_at).getTime() : 0))
      .filter((value) => Number.isFinite(value) && value > 0);
    if (!timestamps.length) {
      return null;
    }
    const fresh = Math.max(...timestamps);
    return new Date(fresh);
  }, [strategies]);

  const selectedGuide = React.useMemo(() => getStrategyGuide(selectedKey), [selectedKey]);

  const baselineWeight = Number(selectedStrategy?.weight ?? 0);
  const baselineEnabled = Boolean(selectedStrategy?.enabled);
  const hasChanges = selectedStrategy
    ? Math.abs(editWeight - baselineWeight) > 0.0001 || editEnabled !== baselineEnabled
    : false;
  const disableSave = !selectedStrategy || !hasChanges || saving;

  const showStrategySkeleton = loadingOverview && strategies.length === 0;
  const isRefreshingSnapshot = refreshing || loadingOverview;

  const headerStats = [
    {
      label: 'Coverage',
      value:
        diversity.coverage != null && !Number.isNaN(diversity.coverage)
          ? `${Math.round(diversity.coverage * 100)}%`
          : 'n/a',
    },
    {
      label: 'Entropy',
      value:
        diversity.entropy != null && !Number.isNaN(diversity.entropy)
          ? diversity.entropy.toFixed(2)
          : 'n/a',
    },
    {
      label: 'Gini (diversity)',
      value:
        diversity.gini != null && !Number.isNaN(diversity.gini)
          ? diversity.gini.toFixed(2)
          : 'n/a',
    },
  ];
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadOverview(selectedKey || undefined);
    } finally {
      setRefreshing(false);
    }
  };

  const handleReset = () => {
    if (!selectedStrategy) return;
    setEditWeight(Number(selectedStrategy.weight ?? 0));
    setEditEnabled(Boolean(selectedStrategy.enabled));
  };

  const saveStrategy = async () => {
    if (!selectedStrategy || !hasChanges) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await apiPatch(`/v1/navigation/relations/strategies/${encodeURIComponent(selectedKey)}`, {
        weight: editWeight,
        enabled: editEnabled,
      });
      await loadOverview(selectedKey);
    } catch (err: any) {
      const message = extractErrorMessage(err, translate(RELATIONS_TOASTS.updateError));
      setError(message);
      pushToast({ intent: 'error', description: message });
    } finally {
      setSaving(false);
    }
  };

  return (
    <ContentLayout
      context="nodes"
      title="Transition strategies"
      description="Balance exploration and relevance for how players travel across the narrative graph."
      stats={headerStats}
    >
      {error && (
        <Card className="border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900/50 dark:bg-rose-900/20">
          {error}
        </Card>
      )}

      <Card className="space-y-5 p-4 lg:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-xl space-y-3">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-dark-50">
              Shape how players move between nodes
            </h2>
            <p className="text-sm text-gray-600 dark:text-dark-200">
              Transition strategies decide which nodes appear next. Pick one, review the cached
              relations, then adjust the weight or disable it to steer the blend.
            </p>
            <ul className="list-disc space-y-1 pl-5 text-sm text-gray-600 dark:text-dark-200">
              <li>Select a strategy from the library to inspect its sample transitions.</li>
              <li>Tune the weight to rebalance its impact against other enabled strategies.</li>
              <li>Refresh the snapshot after you save to see the newest cached relations.</li>
            </ul>
          </div>
          <div className="flex w-full flex-col gap-2 sm:w-auto">
            <Button
              onClick={handleRefresh}
              disabled={isRefreshingSnapshot}
              className="w-full sm:w-auto"
            >
              {isRefreshingSnapshot ? (
                <span className="flex items-center justify-center gap-2">
                  <Spinner size="sm" />
                  Refreshing...
                </span>
              ) : (
                'Refresh snapshot'
              )}
            </Button>
            <div className="text-xs text-gray-500 dark:text-dark-300">
              Snapshot {lastRefreshAt ? `refreshed ${humanizeTimestamp(lastRefreshAt)}` : 'not loaded yet'}
              {lastUpdatedAt ? (
                <div>Latest change saved {humanizeTimestamp(lastUpdatedAt)}</div>
              ) : null}
            </div>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          {['Enabled strategies', 'Cached relations', 'Average weight'].map((label, index) => {
            const cardBase =
              'rounded-lg border border-gray-200 bg-white p-3 text-sm shadow-sm dark:border-dark-600 dark:bg-dark-800/80';
            if (showStrategySkeleton) {
              return (
                <div key={label} className={cardBase}>
                  <Skeleton className="h-3 w-24 rounded" />
                  <Skeleton className="mt-3 h-6 w-16 rounded" />
                  <Skeleton className="mt-3 h-3 w-20 rounded" />
                </div>
              );
            }
            const value =
              index === 0
                ? strategyMetrics.enabled
                : index === 1
                  ? formatCount(strategyMetrics.totalLinks)
                  : formatWeight(strategyMetrics.avgWeight);
            const helper =
              index === 0
                ? `of ${strategyMetrics.total} total`
                : index === 1
                  ? 'cached transitions across strategies'
                  : 'relative strength across enabled strategies';
            return (
              <div key={label} className={cardBase}>
                <div className="text-xs uppercase text-gray-500 dark:text-dark-300">{label}</div>
                <div className="mt-1 text-2xl font-semibold text-gray-900 dark:text-dark-100">
                  {value}
                </div>
                <div className="text-xs text-gray-400 dark:text-dark-400">{helper}</div>
              </div>
            );
          })}
        </div>
      </Card>
      <div className="grid gap-4 xl:grid-cols-[1.6fr,1fr]">
        <Card className="space-y-4 p-4 lg:p-5">
          <div className="flex items-start justify-between gap-2">
            <div className="space-y-1">
              <h2 className="text-base font-semibold text-gray-900 dark:text-dark-50">
                Strategy library
              </h2>
              <p className="text-sm text-gray-600 dark:text-dark-200">
                Pick a strategy to preview its cached relations and unlock tuning controls.
              </p>
            </div>
            {loadingOverview && strategies.length > 0 ? (
              <Badge color="info" variant="soft">
                Updating...
              </Badge>
            ) : null}
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {showStrategySkeleton
              ? Array.from({ length: 4 }).map((_, index) => (
                  <div
                    key={`strategy-skeleton-${index}`}
                    className="rounded-2xl border border-gray-200 bg-white p-4 dark:border-dark-600 dark:bg-dark-800/80"
                  >
                    <Skeleton className="h-4 w-28 rounded" />
                    <Skeleton className="mt-3 h-3 w-full rounded" />
                    <Skeleton className="mt-2 h-3 w-3/4 rounded" />
                    <Skeleton className="mt-4 h-3 w-1/2 rounded" />
                  </div>
                ))
              : strategies.map((strategy) => {
                  const active = strategy.key === selectedKey;
                  const guide = getStrategyGuide(strategy.key);
                  const buttonBase =
                    'group relative flex h-full flex-col rounded-2xl border p-4 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500';
                  const buttonVariant = active
                    ? 'border-primary-300 bg-primary-50 shadow-sm dark:border-primary-700/60 dark:bg-primary-900/10'
                    : 'border-gray-200 bg-white hover:border-primary-300 hover:bg-primary-50/50 dark:border-dark-600 dark:bg-dark-800/80 dark:hover:border-primary-600/60 dark:hover:bg-dark-750';
                  return (
                    <button
                      type="button"
                      key={strategy.key}
                      className={`${buttonBase} ${buttonVariant}`}
                      onClick={() => setSelectedKey(strategy.key)}
                      aria-pressed={active}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-gray-900 dark:text-dark-100">
                            {guide.title}
                          </div>
                          <div className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-400">
                            {titleize(strategy.key)}
                          </div>
                        </div>
                        <Badge color={strategy.enabled ? 'success' : 'neutral'} variant="soft">
                          {strategy.enabled ? 'Enabled' : 'Disabled'}
                        </Badge>
                      </div>
                      <p className="mt-3 text-sm text-gray-600 dark:text-dark-200">
                        {guide.summary}
                      </p>
                      <div className="mt-4 flex flex-wrap gap-3 text-xs text-gray-500 dark:text-dark-300">
                        <span>
                          Weight{' '}
                          <strong className="text-gray-800 dark:text-dark-100">
                            {formatWeight(strategy.weight)}
                          </strong>
                        </span>
                        <span>
                          Usage{' '}
                          <strong className="text-gray-800 dark:text-dark-100">
                            {formatPercent(strategy.usage_share)}
                          </strong>
                        </span>
                        <span>
                          Cached links{' '}
                          <strong className="text-gray-800 dark:text-dark-100">
                            {formatCount(strategy.links)}
                          </strong>
                        </span>
                      </div>
                      <div className="mt-3 text-xs text-gray-400 dark:text-dark-400">
                        Updated {humanizeTimestamp(strategy.updated_at)}
                      </div>
                    </button>
                  );
                })}
          </div>

          {!loadingOverview && strategies.length === 0 ? (
            <div className="rounded-lg border border-dashed border-gray-200 p-6 text-center text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
              No strategies have been configured yet. Configure them in the backend or import a
              preset to start ranking transitions.
            </div>
          ) : null}
        </Card>

        <Card className="space-y-5 p-4 lg:p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <h2 className="text-base font-semibold text-gray-900 dark:text-dark-50">
                Strategy controls
              </h2>
              <p className="text-sm text-gray-600 dark:text-dark-200">
                {selectedStrategy
                  ? `Fine-tune the ${selectedGuide.title} strategy to influence how players exit the current node.`
                  : 'Select a strategy from the library to unlock the tuning controls.'}
              </p>
            </div>
            {selectedStrategy ? (
              <Badge color={selectedStrategy.enabled ? 'success' : 'warning'} variant="soft">
                {selectedStrategy.enabled ? 'Enabled' : 'Disabled'}
              </Badge>
            ) : null}
          </div>

          {selectedStrategy ? (
            <>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-600 shadow-sm dark:bg-dark-800/60 dark:text-dark-200">
                  <div className="text-xs uppercase text-gray-500 dark:text-dark-300">Usage share</div>
                  <div className="mt-1 text-lg font-semibold text-gray-900 dark:text-dark-100">
                    {formatPercent(selectedStrategy.usage_share)}
                  </div>
                  <div className="text-[11px] text-gray-400 dark:text-dark-400">
                    Portion of cached links coming from this strategy.
                  </div>
                </div>
                <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-600 shadow-sm dark:bg-dark-800/60 dark:text-dark-200">
                  <div className="text-xs uppercase text-gray-500 dark:text-dark-300">Cached links</div>
                  <div className="mt-1 text-lg font-semibold text-gray-900 dark:text-dark-100">
                    {formatCount(selectedStrategy.links)}
                  </div>
                  <div className="text-[11px] text-gray-400 dark:text-dark-400">
                    Update after recomputing relations to see fresh counts.
                  </div>
                </div>
                <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-600 shadow-sm dark:bg-dark-800/60 dark:text-dark-200">
                  <div className="text-xs uppercase text-gray-500 dark:text-dark-300">Last updated</div>
                  <div className="mt-1 text-lg font-semibold text-gray-900 dark:text-dark-100">
                    {humanizeTimestamp(selectedStrategy.updated_at)}
                  </div>
                  <div className="text-[11px] text-gray-400 dark:text-dark-400">
                    Saved whenever you update the weight or toggle.
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
                    Weight
                  </label>
                  <Input
                    type="number"
                    step="0.05"
                    min="0"
                    value={editWeight}
                    onChange={(event) => setEditWeight(Number(event.target.value))}
                    disabled={loadingOverview || saving}
                  />
                  <p className="text-xs text-gray-500 dark:text-dark-300">
                    Heavier weights give this strategy more influence relative to other enabled ones.
                  </p>
                </div>

                <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2 dark:border-dark-600 dark:bg-dark-800/80">
                  <div className="space-y-1">
                    <div className="text-sm font-medium text-gray-700 dark:text-dark-100">
                      Enabled
                    </div>
                    <p className="text-xs text-gray-500 dark:text-dark-300">
                      Disabled strategies stay in the library but stop contributing to live transitions.
                    </p>
                  </div>
                  <Switch
                    checked={editEnabled}
                    onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
                      setEditEnabled(event.target.checked)
                    }
                    disabled={loadingOverview || saving}
                  />
                </div>

                <div className="rounded-lg bg-gray-50 p-4 text-sm text-gray-600 dark:bg-dark-800/60 dark:text-dark-200">
                  <div className="text-sm font-semibold text-gray-700 dark:text-dark-100">
                    {selectedGuide.title}
                  </div>
                  <p className="mt-1 text-sm text-gray-600 dark:text-dark-200">
                    {selectedGuide.summary}
                  </p>
                  <ul className="mt-3 list-disc space-y-1 pl-5 text-xs text-gray-500 dark:text-dark-300">
                    {selectedGuide.tips.map((tip) => (
                      <li key={tip}>{tip}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  color="neutral"
                  size="sm"
                  onClick={handleReset}
                  disabled={!hasChanges || saving}
                >
                  Reset to saved
                </Button>
                <Button type="button" onClick={saveStrategy} disabled={disableSave}>
                  {saving ? (
                    <span className="flex items-center gap-2">
                      <Spinner size="sm" />
                      Saving...
                    </span>
                  ) : (
                    'Save changes'
                  )}
                </Button>
              </div>
            </>
          ) : (
            <div className="rounded-lg border border-dashed border-gray-200 p-6 text-center text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
              Select a strategy from the library to see its controls.
            </div>
          )}
        </Card>
      </div>
      <Card className="p-4 lg:p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <h2 className="text-base font-semibold text-gray-900 dark:text-dark-50">
              Preview: {selectedGuide.title}
            </h2>
            <p className="text-sm text-gray-600 dark:text-dark-200">
              Top cached relations produced by {selectedKey ? titleize(selectedKey) : 'this strategy'}.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="ghost"
              color="neutral"
              size="sm"
              onClick={() => void loadRelations(selectedKey)}
              disabled={loadingRelations || !selectedKey}
            >
              {loadingRelations ? (
                <span className="flex items-center gap-2">
                  <Spinner size="sm" />
                  Reloading...
                </span>
              ) : (
                'Reload preview'
              )}
            </Button>
            <Badge color="neutral" variant="outline">
              {relations.length} rows
            </Badge>
          </div>
        </div>

        {selectedStrategy && !selectedStrategy.enabled ? (
          <div className="mt-3 rounded-md bg-amber-50 p-3 text-xs text-amber-700 dark:bg-amber-900/20 dark:text-amber-200">
            This strategy is disabled. Its cached relations remain available for review but will not
            influence live navigation until you enable it.
          </div>
        ) : null}


        <div className="mt-4 overflow-x-auto">
          <UITable preset="surface" className="min-w-[720px]" hover>
            <UITable.THead>
              <UITable.TR>
                <UITable.TH className="min-w-[220px]">Source</UITable.TH>
                <UITable.TH className="min-w-[220px]">Target</UITable.TH>
                <UITable.TH className="w-32">Score</UITable.TH>
                <UITable.TH className="w-40">Updated</UITable.TH>
              </UITable.TR>
            </UITable.THead>
            <UITable.TBody>
              {loadingRelations ? (
                Array.from({ length: 4 }).map((_, index) => (
                  <UITable.TR key={`relation-skeleton-${index}`}>
                    <UITable.TD>
                      <Skeleton className="h-4 w-48 rounded" />
                      <Skeleton className="mt-2 h-3 w-24 rounded" />
                    </UITable.TD>
                    <UITable.TD>
                      <Skeleton className="h-4 w-48 rounded" />
                      <Skeleton className="mt-2 h-3 w-24 rounded" />
                    </UITable.TD>
                    <UITable.TD>
                      <Skeleton className="h-4 w-16 rounded" />
                    </UITable.TD>
                    <UITable.TD>
                      <Skeleton className="h-4 w-24 rounded" />
                    </UITable.TD>
                  </UITable.TR>
                ))
              ) : relations.length === 0 ? (
                <UITable.Empty
                  colSpan={4}
                  title="No cached relations"
                  description="Reload or adjust the strategy to inspect its related nodes."
                />
              ) : (
                relations.map((rel) => (
                  <UITable.TR
                    key={`${rel.source_id}-${rel.target_id}`}
                    className="bg-white/80 transition hover:bg-white dark:bg-dark-800/80 dark:hover:bg-dark-750"
                  >
                    <UITable.TD className="text-gray-700 dark:text-dark-100">
                      <div className="font-medium text-gray-900 dark:text-white">
                        {rel.source_title ?? rel.source_id}
                      </div>
                      {rel.source_slug ? (
                        <div className="text-xs text-gray-400 dark:text-dark-300">/{rel.source_slug}</div>
                      ) : null}
                    </UITable.TD>
                    <UITable.TD className="text-gray-700 dark:text-dark-100">
                      <div className="font-medium text-gray-900 dark:text-white">
                        {rel.target_title ?? rel.target_id}
                      </div>
                      {rel.target_slug ? (
                        <div className="text-xs text-gray-400 dark:text-dark-300">/{rel.target_slug}</div>
                      ) : null}
                    </UITable.TD>
                    <UITable.TD className="text-gray-700 dark:text-dark-100">
                      {typeof rel.score === 'number' ? rel.score.toFixed(4) : 'N/A'}
                    </UITable.TD>
                    <UITable.TD className="text-gray-700 dark:text-dark-100">
                      {rel.updated_at ? new Date(rel.updated_at).toLocaleString() : 'N/A'}
                    </UITable.TD>
                  </UITable.TR>
                ))
              )}
            </UITable.TBody>
          </UITable>
        </div>
      </Card>
    </ContentLayout>
  );
}

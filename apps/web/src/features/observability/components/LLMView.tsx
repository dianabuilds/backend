import React from 'react';
import {
  ArrowPathIcon,
  BanknotesIcon,
  BoltIcon,
  ChartBarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  FunnelIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import {
  ApexChart,
  Badge,
  Button,
  Input,
  MetricCard,
  Select,
  Skeleton,
  Surface,
  Table,
  TablePagination,
} from '@ui';
import { ObservabilityLayout } from './ObservabilityLayout';
import { fetchLLMSummary } from '@shared/api/observability';
import { useTelemetryQuery } from '../hooks/useTelemetryQuery';
import {
  LLMCallMetric,
  LLMCostMetric,
  LLMLatencyMetric,
  LLMSummary,
  LLMTokensMetric,
} from '@shared/types/observability';
import type { PageHeroMetric } from '@ui/patterns/PageHero';

type StageMetrics = {
  key: string;
  provider: string;
  model: string;
  stage: string;
  calls: number;
  errors: number;
  avgLatencyMs: number;
  promptTokens: number;
  completionTokens: number;
  costUsd: number;
};

const numberFormatter = new Intl.NumberFormat('en-US');
const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
});
const timeFormatter = new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

function formatNumber(value: number | null | undefined) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'вЂ”';
  return numberFormatter.format(value);
}

function formatUpdated(date: Date | null): string {
  if (!date) return 'вЂ”';
  return timeFormatter.format(date);
}

function formatLatency(value: number | null | undefined) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'вЂ”';
  return `${Math.round(value)} ms`;
}

const LLM_POLL_INTERVAL_MS = 30_000;

function formatCurrency(value: number | null | undefined) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'вЂ”';
  return currencyFormatter.format(value);
}

function makeStageKey(provider: string, model: string, stage: string | null | undefined) {
  const normalizedStage = stage && stage.trim().length ? stage.trim() : 'default';
  return `${provider}::${model}::${normalizedStage}`;
}

function buildStageMetrics(data: LLMSummary | null): StageMetrics[] {
  if (!data) return [];
  const buckets = new Map<string, StageMetrics>();

  const ensure = (provider: string, model: string, stage: string | null | undefined) => {
    const key = makeStageKey(provider, model, stage);
    if (!buckets.has(key)) {
      buckets.set(key, {
        key,
        provider,
        model,
        stage: stage && stage.trim().length ? stage.trim() : 'default',
        calls: 0,
        errors: 0,
        avgLatencyMs: 0,
        promptTokens: 0,
        completionTokens: 0,
        costUsd: 0,
      });
    }
    return buckets.get(key)!;
  };

  (data.calls ?? []).forEach((entry: LLMCallMetric) => {
    const bucket = ensure(entry.provider, entry.model, entry.stage);
    const count = entry.count || 0;
    if (entry.type === 'errors') bucket.errors += count;
    else bucket.calls += count;
  });

  (data.latency_avg_ms ?? []).forEach((entry: LLMLatencyMetric) => {
    const bucket = ensure(entry.provider, entry.model, entry.stage);
    bucket.avgLatencyMs = entry.avg_ms || 0;
  });

  (data.tokens_total ?? []).forEach((entry: LLMTokensMetric) => {
    const bucket = ensure(entry.provider, entry.model, entry.stage);
    const total = entry.total || 0;
    if (entry.type === 'completion') bucket.completionTokens += total;
    else bucket.promptTokens += total;
  });

  (data.cost_usd_total ?? []).forEach((entry: LLMCostMetric) => {
    const bucket = ensure(entry.provider, entry.model, entry.stage);
    bucket.costUsd += entry.total_usd || 0;
  });

  return Array.from(buckets.values()).sort((a, b) => b.calls + b.errors - (a.calls + a.errors));
}

function aggregateTotals(metrics: StageMetrics[]) {
  if (!metrics.length) {
    return {
      totalCalls: 0,
      totalErrors: 0,
      averageLatency: 0,
      totalPromptTokens: 0,
      totalCompletionTokens: 0,
      totalCostUsd: 0,
    };
  }
  const totalCalls = metrics.reduce((acc, row) => acc + row.calls, 0);
  const totalErrors = metrics.reduce((acc, row) => acc + row.errors, 0);
  const totalPromptTokens = metrics.reduce((acc, row) => acc + row.promptTokens, 0);
  const totalCompletionTokens = metrics.reduce((acc, row) => acc + row.completionTokens, 0);
  const totalCostUsd = metrics.reduce((acc, row) => acc + row.costUsd, 0);
  const averageLatency = metrics.reduce((acc, row) => acc + row.avgLatencyMs, 0) / metrics.length;
  return {
    totalCalls,
    totalErrors,
    averageLatency,
    totalPromptTokens,
    totalCompletionTokens,
    totalCostUsd,
  };
}

function findExtremes(metrics: StageMetrics[]) {
  if (!metrics.length) {
    return {
      topVolume: null,
      topLatency: null,
      topCost: null,
    } as const;
  }
  return metrics.reduce(
    (acc, row) => {
      if (!acc.topVolume || row.calls > acc.topVolume.calls) acc.topVolume = row;
      if (!acc.topLatency || row.avgLatencyMs > acc.topLatency.avgLatencyMs) acc.topLatency = row;
      if (!acc.topCost || row.costUsd > acc.topCost.costUsd) acc.topCost = row;
      return acc;
    },
    { topVolume: null as StageMetrics | null, topLatency: null as StageMetrics | null, topCost: null as StageMetrics | null },
  );
}

export function ObservabilityLLM(): React.ReactElement {
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [providerFilter, setProviderFilter] = React.useState('ALL');
  const [search, setSearch] = React.useState('');

  const { data, loading, error, refresh, lastUpdated } = useTelemetryQuery<LLMSummary>({
    fetcher: (signal) => fetchLLMSummary({ signal }),
    pollIntervalMs: LLM_POLL_INTERVAL_MS,
  });

  const stageMetrics = React.useMemo(() => buildStageMetrics(data ?? null), [data]);

  React.useEffect(() => {
    setPage(1);
  }, [stageMetrics.length]);

  const providers = React.useMemo(() => {
    const set = new Set(stageMetrics.map((row) => row.provider));
    return Array.from(set.values()).sort();
  }, [stageMetrics]);

  const trimmedSearch = search.trim().toLowerCase();

  const filteredMetrics = React.useMemo(() => {
    return stageMetrics.filter((row) => {
      const providerMatches = providerFilter === 'ALL' || row.provider === providerFilter;
      const searchMatches = trimmedSearch
        ? `${row.provider} ${row.model} ${row.stage}`.toLowerCase().includes(trimmedSearch)
        : true;
      return providerMatches && searchMatches;
    });
  }, [stageMetrics, providerFilter, trimmedSearch]);

  React.useEffect(() => {
    setPage(1);
  }, [providerFilter, trimmedSearch]);

  const totals = React.useMemo(() => aggregateTotals(stageMetrics), [stageMetrics]);
  const extremes = React.useMemo(() => findExtremes(stageMetrics), [stageMetrics]);
  const filteredTotals = React.useMemo(() => aggregateTotals(filteredMetrics), [filteredMetrics]);

  const totalRows = filteredMetrics.length;
  const paginatedRows = React.useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredMetrics.slice(start, start + pageSize);
  }, [filteredMetrics, page, pageSize]);
  const hasNext = page * pageSize < totalRows;

  const topByVolume = React.useMemo(
    () =>
      filteredMetrics
        .slice()
        .sort((a, b) => b.calls - a.calls)
        .slice(0, 12),
    [filteredMetrics],
  );

  const stageLabels = topByVolume.map((row) => `${row.provider}:${row.model}@${row.stage}`);

  const hasData = Boolean(data) && !loading && !error;
  const isLoading = loading || (!data && !error);

  const heroActions = React.useMemo(
    () => (
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-gray-500 dark:text-dark-200/80">
          Updated {formatUpdated(lastUpdated)}
        </span>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          color="neutral"
          onClick={() => {
            void refresh();
          }}
          disabled={loading}
          data-testid="observability-llm-refresh"
        >
          <ArrowPathIcon className="size-4" aria-hidden="true" />
          Refresh
        </Button>
      </div>
    ),
    [lastUpdated, loading, refresh],
  );

  const heroMetrics: PageHeroMetric[] | undefined = hasData
    ? [
        {
          id: 'llm-calls',
          label: 'Total LLM calls',
          value: formatNumber(totals.totalCalls),
          helper: `${formatNumber(totals.totalErrors)} errors`,
          icon: <BoltIcon className="size-4" aria-hidden="true" />,
        },
        {
          id: 'llm-latency',
          label: 'Average latency',
          value: formatLatency(totals.averageLatency),
          helper: extremes.topLatency
            ? `${extremes.topLatency.provider}:${extremes.topLatency.model}@${extremes.topLatency.stage}`
            : 'Awaiting data',
          icon: <ClockIcon className="size-4" aria-hidden="true" />,
          accent: 'warning',
        },
        {
          id: 'llm-spend',
          label: 'Total spend',
          value: formatCurrency(totals.totalCostUsd),
          helper: `${formatNumber(totals.totalPromptTokens + totals.totalCompletionTokens)} tokens`,
          icon: <BanknotesIcon className="size-4" aria-hidden="true" />,
          accent: 'danger',
        },
      ]
    : undefined;

  if (error) {
    return (
      <ObservabilityLayout title="LLM telemetry" actions={heroActions} metrics={heroMetrics}>
        <Surface
          variant="soft"
          className="border border-rose-200/60 bg-rose-50/60 text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/20 dark:text-rose-200"
          role="alert"
          data-testid="observability-llm-error"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <ExclamationTriangleIcon className="mt-0.5 size-6 shrink-0" aria-hidden="true" />
              <div className="space-y-1">
                <h2 className="text-sm font-semibold">LLM telemetry failed to load</h2>
                <p className="text-sm opacity-80">{error}</p>
              </div>
            </div>
            <Button onClick={() => refresh()} variant="outlined" color="error" data-testid="observability-llm-retry">
              Retry request
            </Button>
          </div>
        </Surface>
      </ObservabilityLayout>
    );
  }

  const metricCards = hasData
    ? [
        {
          id: 'top-volume',
          label: 'Top stage by volume',
          value: extremes.topVolume ? formatNumber(extremes.topVolume.calls) : '—',
          description: extremes.topVolume
            ? `${extremes.topVolume.provider}:${extremes.topVolume.model}@${extremes.topVolume.stage}`
            : 'Awaiting data',
          icon: <ChartBarIcon className="size-5" aria-hidden="true" />,
          tone: 'primary' as const,
        },
        {
          id: 'top-latency',
          label: 'Slowest stage',
          value: extremes.topLatency ? formatLatency(extremes.topLatency.avgLatencyMs) : '—',
          description: extremes.topLatency
            ? `${extremes.topLatency.provider}:${extremes.topLatency.model}@${extremes.topLatency.stage}`
            : 'Awaiting data',
          icon: <ClockIcon className="size-5" aria-hidden="true" />,
          tone: 'warning' as const,
        },
        {
          id: 'top-cost',
          label: 'Most expensive stage',
          value: extremes.topCost ? formatCurrency(extremes.topCost.costUsd) : '—',
          description: extremes.topCost
            ? `${extremes.topCost.provider}:${extremes.topCost.model}@${extremes.topCost.stage}`
            : 'Awaiting data',
          icon: <BanknotesIcon className="size-5" aria-hidden="true" />,
          tone: 'secondary' as const,
        },
        {
          id: 'tokens',
          label: 'Tokens consumed (filtered)',
          value: formatNumber(filteredTotals.totalPromptTokens + filteredTotals.totalCompletionTokens),
          description: `${formatNumber(filteredTotals.totalPromptTokens)} prompt ? ${formatNumber(filteredTotals.totalCompletionTokens)} completion`,
          icon: <SparklesIcon className="size-5" aria-hidden="true" />,
          tone: 'success' as const,
        },
      ]
    : [];

  return (
    <ObservabilityLayout
      title="LLM telemetry"
      description="Provider, model, and stage level performance, spend, and reliability."
      actions={heroActions}
      metrics={heroMetrics}
    >
      <div className="grid gap-6 xl:grid-cols-12">
        <div className="xl:col-span-12" data-testid="observability-llm-filters" data-analytics="observability:llm:filters">
          <Surface variant="soft" className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="space-y-1">
                <h2 className="text-sm font-semibold text-gray-900 dark:text-white">Filter stages</h2>
                <p className="text-xs text-gray-500 dark:text-dark-200/70">Focus on specific providers or search across models and stages.</p>
              </div>
              <Badge color="neutral" variant="soft" className="flex items-center gap-1 text-[11px]">
                <FunnelIcon className="size-3" aria-hidden="true" />
                {filteredMetrics.length} of {stageMetrics.length} stages
              </Badge>
            </div>
            <div className="grid gap-3 md:grid-cols-[minmax(0,220px)_minmax(0,1fr)] md:items-end">
              <Select
                label="Provider"
                value={providerFilter}
                onChange={(event) => setProviderFilter(event.target.value)}
                data-testid="observability-llm-provider-filter"
                data-analytics="observability:llm:filter-provider"
              >
                <option value="ALL">All providers</option>
                {providers.map((provider) => (
                  <option key={provider} value={provider}>
                    {provider}
                  </option>
                ))}
              </Select>
              <Input
                label="Search models and stages"
                placeholder="gpt-4o, moderation, qa"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                data-testid="observability-llm-search"
                data-analytics="observability:llm:filter-search"
              />
            </div>
          </Surface>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:col-span-12 xl:grid-cols-4" data-testid="observability-llm-metrics">
          {hasData
            ? metricCards.map((metric) => (
                <div
                  key={metric.id}
                  data-testid={`observability-llm-metric-${metric.id}`}
                  data-analytics={`observability:llm:${metric.id}`}
                >
                  <MetricCard
                    label={metric.label}
                    value={metric.value}
                    description={metric.description}
                    icon={metric.icon}
                    tone={metric.tone}
                  />
                </div>
              ))
            : Array.from({ length: 4 }).map((_, index) => (
                <Surface key={`llm-metric-skeleton-${index}`} variant="soft" className="rounded-3xl p-5">
                  <Skeleton className="h-3 w-24 rounded" />
                  <Skeleton className="mt-4 h-8 w-32 rounded" />
                  <Skeleton className="mt-3 h-3 w-36 rounded" />
                </Surface>
              ))}
        </div>

        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-llm-calls"
          data-analytics="observability:llm:calls-chart"
        >
          <header className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Calls vs errors by stage</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Stacked bars compare success and failure volume for the busiest stages.</p>
            </div>
            <div className="text-xs text-gray-500 dark:text-dark-200/70">Top {topByVolume.length} stages (filtered)</div>
          </header>

          {isLoading ? (
            <Skeleton className="h-72 w-full rounded-3xl" />
          ) : topByVolume.length === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <ChartBarIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No stages match the current filters</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Adjust filters or wait for additional LLM traffic to populate this view.</p>
            </div>
          ) : (
            <ApexChart
              type="bar"
              series={[
                { name: 'Calls', data: topByVolume.map((row) => row.calls) },
                { name: 'Errors', data: topByVolume.map((row) => row.errors) },
              ]}
              options={{
                xaxis: { categories: stageLabels, labels: { rotate: -45 } },
                legend: { show: true },
                dataLabels: { enabled: false },
                plotOptions: { bar: { columnWidth: '55%', borderRadius: 6 } },
              }}
              height={360}
            />
          )}
        </Surface>

        <div className="grid gap-6 xl:col-span-12 xl:grid-cols-2">
          <Surface
            variant="frosted"
            className="space-y-5"
            data-testid="observability-llm-latency"
            data-analytics="observability:llm:latency-chart"
          >
            <header className="space-y-1">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Average latency by stage</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Track performance regressions per provider/model/stage combination.</p>
            </header>

            {isLoading ? (
              <Skeleton className="h-64 w-full rounded-3xl" />
            ) : topByVolume.length === 0 ? (
              <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
                <ClockIcon className="size-10 text-primary-400" aria-hidden="true" />
                <h3 className="text-base font-semibold">No latency data</h3>
                <p className="text-sm text-gray-600 dark:text-dark-200/80">Latency metrics appear after at least one successful completion per stage.</p>
              </div>
            ) : (
              <ApexChart
                type="bar"
                series={[
                  {
                    name: 'Avg ms',
                    data: topByVolume.map((row) => Math.round(row.avgLatencyMs || 0)),
                  },
                ]}
                options={{
                  xaxis: { categories: stageLabels, labels: { rotate: -45 } },
                  dataLabels: { enabled: false },
                }}
                height={320}
              />
            )}
          </Surface>

          <Surface
            variant="frosted"
            className="space-y-5"
            data-testid="observability-llm-tokens"
            data-analytics="observability:llm:tokens-chart"
          >
            <header className="space-y-1">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Tokens distribution</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Prompt vs completion tokens for the most active stages.</p>
            </header>

            {isLoading ? (
              <Skeleton className="h-64 w-full rounded-3xl" />
            ) : topByVolume.length === 0 ? (
              <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
                <SparklesIcon className="size-10 text-primary-400" aria-hidden="true" />
                <h3 className="text-base font-semibold">No token data yet</h3>
                <p className="text-sm text-gray-600 dark:text-dark-200/80">Tokens will appear once the SDK reports both prompt and completion usage.</p>
              </div>
            ) : (
              <ApexChart
                type="bar"
                series={[
                  { name: 'Prompt tokens', data: topByVolume.map((row) => row.promptTokens) },
                  { name: 'Completion tokens', data: topByVolume.map((row) => row.completionTokens) },
                ]}
                options={{
                  xaxis: { categories: stageLabels, labels: { rotate: -45 } },
                  legend: { show: true },
                  dataLabels: { enabled: false },
                  chart: { stacked: true },
                }}
                height={320}
              />
            )}
          </Surface>
        </div>

        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-llm-table"
          data-analytics="observability:llm:table"
        >
          <header className="flex flex-col gap-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Stage breakdown</h2>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">Detailed metrics per provider, model, and stage with pagination and responsive layout.</p>
          </header>

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={`llm-table-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : totalRows === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <FunnelIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No stages to display</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Reset filters or wait for the observability pipeline to ingest more stages.</p>
            </div>
          ) : (
            <>
              <div className="hidden md:block">
                <div className="overflow-x-auto">
                  <Table.Table preset="analytics" zebra hover>
                    <Table.THead>
                      <Table.TR>
                        <Table.TH>Provider</Table.TH>
                        <Table.TH>Model</Table.TH>
                        <Table.TH>Stage</Table.TH>
                        <Table.TH>Calls</Table.TH>
                        <Table.TH>Errors</Table.TH>
                        <Table.TH>Avg ms</Table.TH>
                        <Table.TH>Prompt tokens</Table.TH>
                        <Table.TH>Completion tokens</Table.TH>
                        <Table.TH>Spend (USD)</Table.TH>
                      </Table.TR>
                    </Table.THead>
                    <Table.TBody>
                      {paginatedRows.map((row, index) => (
                        <Table.TR
                          key={row.key}
                          data-testid={`observability-llm-row-${(page - 1) * pageSize + index}`}
                          data-analytics="observability:llm:table-row"
                          className="cursor-pointer transition hover:-translate-y-[1px]"
                        >
                          <Table.TD>{row.provider}</Table.TD>
                          <Table.TD>{row.model}</Table.TD>
                          <Table.TD>{row.stage}</Table.TD>
                          <Table.TD>{formatNumber(row.calls)}</Table.TD>
                          <Table.TD className={row.errors ? 'text-rose-600 dark:text-rose-400' : ''}>{formatNumber(row.errors)}</Table.TD>
                          <Table.TD>{Math.round(row.avgLatencyMs || 0)}</Table.TD>
                          <Table.TD>{formatNumber(row.promptTokens)}</Table.TD>
                          <Table.TD>{formatNumber(row.completionTokens)}</Table.TD>
                          <Table.TD>{formatCurrency(row.costUsd)}</Table.TD>
                        </Table.TR>
                      ))}
                    </Table.TBody>
                  </Table.Table>
                </div>
              </div>

              <div className="space-y-3 md:hidden">
                {paginatedRows.map((row, index) => (
                  <Surface
                    key={row.key}
                    variant="soft"
                    className="rounded-3xl p-5"
                    data-testid={`observability-llm-card-${(page - 1) * pageSize + index}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <Badge color="primary" variant="soft">{row.provider}</Badge>
                      <span className="text-xs text-gray-500 dark:text-dark-200/70">{formatCurrency(row.costUsd)}</span>
                    </div>
                    <div className="mt-3 text-sm font-semibold text-gray-900 dark:text-white">{row.model}</div>
                    <div className="text-xs text-gray-500 dark:text-dark-200/70">Stage: {row.stage}</div>
                    <dl className="mt-3 grid grid-cols-2 gap-3 text-xs text-gray-600 dark:text-dark-200/80">
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Calls</dt>
                        <dd>{formatNumber(row.calls)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Errors</dt>
                        <dd className={row.errors ? 'text-rose-600 dark:text-rose-400' : ''}>{formatNumber(row.errors)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Avg ms</dt>
                        <dd>{Math.round(row.avgLatencyMs || 0)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Tokens</dt>
                        <dd>
                          {formatNumber(row.promptTokens)} prompt / {formatNumber(row.completionTokens)} completion
                        </dd>
                      </div>
                    </dl>
                  </Surface>
                ))}
              </div>

              <TablePagination
                page={page}
                pageSize={pageSize}
                currentCount={paginatedRows.length}
                totalItems={totalRows}
                hasNext={hasNext}
                onPageChange={setPage}
                onPageSizeChange={(value) => {
                  setPageSize(value);
                  setPage(1);
                }}
                data-testid="observability-llm-pagination"
              />
            </>
          )}
        </Surface>
      </div>
    </ObservabilityLayout>
  );
}







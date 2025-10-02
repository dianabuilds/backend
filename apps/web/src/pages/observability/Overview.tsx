import React from 'react';
import {
  ArrowPathIcon,
  BoltIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  GlobeAltIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { ApexChart, Button, MetricCard, Skeleton, Surface } from '@ui';
import { ObservabilityLayout } from './ObservabilityLayout';
import { fetchTelemetryOverview } from './api';
import { useTelemetryQuery } from './useTelemetryQuery';
import {
  LLMCallMetric,
  LLMLatencyMetric,
  TelemetryOverview,
  TransitionModeSummary,
} from './types';

const numberFormatter = new Intl.NumberFormat('en-US');

function formatNumber(value: number | null | undefined) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '--';
  return numberFormatter.format(value);
}

function formatLatency(value: number | null | undefined) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '--';
  return `${Math.round(value)} ms`;
}

type MetricsSnapshot = {
  llmTotalCalls: number;
  llmTotalErrors: number;
  llmLatencySeries: LLMLatencyMetric[];
  workerCompleted: number;
  workerFailed: number;
  workerPending: number;
  transitionsAvgMs: number;
  transitionsNoRouteRatio: number;
  rumTtfb: number | null | undefined;
  rumLoad: number | null | undefined;
};

function summarizeMetrics(data: TelemetryOverview | null): MetricsSnapshot {
  if (!data) {
    return {
      llmTotalCalls: 0,
      llmTotalErrors: 0,
      llmLatencySeries: [],
      workerCompleted: 0,
      workerFailed: 0,
      workerPending: 0,
      transitionsAvgMs: 0,
      transitionsNoRouteRatio: 0,
      rumTtfb: null,
      rumLoad: null,
    };
  }

  const llmCalls = (data.llm?.calls ?? []) as LLMCallMetric[];
  const llmTotalCalls = llmCalls
    .filter((entry) => entry.type === 'calls')
    .reduce((acc, entry) => acc + (entry.count || 0), 0);
  const llmTotalErrors = llmCalls
    .filter((entry) => entry.type === 'errors')
    .reduce((acc, entry) => acc + (entry.count || 0), 0);

  const llmLatencySeries = (data.llm?.latency_avg_ms ?? []) as LLMLatencyMetric[];

  const workerJobs = data.workers?.jobs || {};
  const workerStarted = workerJobs.started || 0;
  const workerCompleted = workerJobs.completed || 0;
  const workerFailed = workerJobs.failed || 0;
  const workerPending = Math.max(workerStarted - workerCompleted - workerFailed, 0);

  const transitions = (data.transitions || []) as TransitionModeSummary[];
  const transitionsCount = transitions.length || 1;
  const transitionsAvgMs = transitions.reduce((acc, entry) => acc + (entry.avg_latency_ms || 0), 0) / transitionsCount;
  const transitionsNoRouteRatio =
    transitions.reduce((acc, entry) => acc + (entry.no_route_ratio || 0), 0) / transitionsCount;

  const rumNav = data.rum?.navigation_avg || {};

  return {
    llmTotalCalls,
    llmTotalErrors,
    llmLatencySeries,
    workerCompleted,
    workerFailed,
    workerPending,
    transitionsAvgMs,
    transitionsNoRouteRatio,
    rumTtfb: rumNav.ttfb_ms,
    rumLoad: rumNav.load_event_ms,
  };
}

export default function ObservabilityOverview() {
  const { data, loading, error, refresh } = useTelemetryQuery<TelemetryOverview>({
    fetcher: (signal) => fetchTelemetryOverview(signal),
  });

  const metrics = React.useMemo(() => summarizeMetrics(data), [data]);
  const hasData = Boolean(data) && !loading && !error;
  const isLoading = loading || (!data && !error);

  const headerStats = hasData
    ? [
        {
          label: 'LLM calls',
          value: formatNumber(metrics.llmTotalCalls),
          hint: `${formatNumber(metrics.llmTotalErrors)} errors`,
          icon: <BoltIcon className="size-4" aria-hidden="true" />,
        },
        {
          label: 'Worker throughput',
          value: formatNumber(metrics.workerCompleted),
          hint: `${formatNumber(metrics.workerFailed)} failed | ${formatNumber(metrics.workerPending)} pending`,
          icon: <ArrowPathIcon className="size-4" aria-hidden="true" />,
        },
        {
          label: 'Transition latency',
          value: formatLatency(metrics.transitionsAvgMs),
          hint: `No-route ${(metrics.transitionsNoRouteRatio * 100).toFixed(1)}%`,
          icon: <SparklesIcon className="size-4" aria-hidden="true" />,
        },
      ]
    : undefined;

  if (error) {
    return (
      <ObservabilityLayout>
        <Surface
          variant="soft"
          className="border border-rose-200/60 bg-rose-50/60 text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/20 dark:text-rose-200"
          role="alert"
          data-testid="observability-overview-error"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <ExclamationTriangleIcon className="mt-0.5 size-6 shrink-0" aria-hidden="true" />
              <div className="space-y-1">
                <h2 className="text-sm font-semibold">Telemetry overview failed to load</h2>
                <p className="text-sm opacity-80">{error}</p>
              </div>
            </div>
            <Button
              onClick={() => refresh()}
              variant="outlined"
              color="error"
              data-testid="observability-overview-retry"
            >
              Retry request
            </Button>
          </div>
        </Surface>
      </ObservabilityLayout>
    );
  }

  return (
    <ObservabilityLayout stats={headerStats}>
      <div className="grid gap-6 xl:grid-cols-12" data-testid="observability-overview-kpis" data-analytics="observability:overview:kpis">
        <div className="grid gap-4 sm:grid-cols-2 xl:col-span-12 xl:grid-cols-4">
          {hasData
            ? [
                {
                  id: 'llm-calls',
                  label: 'LLM calls (24h)',
                  value: formatNumber(metrics.llmTotalCalls),
                  description: `${formatNumber(metrics.llmTotalErrors)} errors captured`,
                  icon: <BoltIcon className="size-5" aria-hidden="true" />,
                  tone: 'primary' as const,
                },
                {
                  id: 'worker-completed',
                  label: 'Jobs completed',
                  value: formatNumber(metrics.workerCompleted),
                  description: `${formatNumber(metrics.workerFailed)} failed and ${formatNumber(metrics.workerPending)} pending`,
                  icon: <ArrowPathIcon className="size-5" aria-hidden="true" />,
                  tone: 'secondary' as const,
                },
                {
                  id: 'transition-latency',
                  label: 'Avg transition latency',
                  value: formatLatency(metrics.transitionsAvgMs),
                  description: `No-route ${(metrics.transitionsNoRouteRatio * 100).toFixed(1)}%`,
                  icon: <SparklesIcon className="size-5" aria-hidden="true" />,
                  tone: 'warning' as const,
                },
                {
                  id: 'rum-load',
                  label: 'Load experience',
                  value: formatLatency(metrics.rumLoad),
                  description: `TTFB ${formatLatency(metrics.rumTtfb)}`,
                  icon: <GlobeAltIcon className="size-5" aria-hidden="true" />,
                  tone: 'success' as const,
                },
              ].map((metric) => (
                <div
                  key={metric.id}
                  data-testid={`observability-overview-metric-${metric.id}`}
                  data-analytics={`observability:overview:${metric.id}`}
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
                <Surface key={`overview-metric-skeleton-${index}`} variant="soft" className="rounded-3xl p-5">
                  <Skeleton className="h-3 w-24 rounded" />
                  <Skeleton className="mt-4 h-8 w-32 rounded" />
                  <Skeleton className="mt-3 h-3 w-36 rounded" />
                </Surface>
              ))}
        </div>
      </div>

      <Surface
        variant="frosted"
        className="space-y-5"
        data-testid="observability-overview-llm-latency"
        data-analytics="observability:overview:llm-latency"
      >
        <header className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">LLM avg latency by provider</h2>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">Rolling 24h average latency grouped by provider, model, and stage.</p>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200/70">
            <ChartBarIcon className="size-4" aria-hidden="true" /> Latency buckets rendered in milliseconds
          </div>
        </header>

        {isLoading ? (
          <Skeleton className="h-72 w-full rounded-3xl" />
        ) : metrics.llmLatencySeries.length === 0 ? (
          <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
            <SparklesIcon className="size-10 text-primary-400" aria-hidden="true" />
            <h3 className="text-base font-semibold">Waiting for traffic</h3>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">Latency trends appear once the first successful LLM invocation is recorded.</p>
          </div>
        ) : (
          <ApexChart
            type="bar"
            series={[
              {
                name: 'avg_ms',
                data: metrics.llmLatencySeries
                  .map((entry) => ({
                    x: `${entry.provider}:${entry.model}${entry.stage ? `@${entry.stage}` : ''}`,
                    y: Math.round(entry.avg_ms || 0),
                  }))
                  .slice(0, 12),
              },
            ]}
            options={{
              xaxis: { type: 'category', labels: { rotate: -45 } },
              yaxis: { labels: { formatter: (value: number) => `${Math.round(value)} ms` } },
              dataLabels: { enabled: false },
              grid: { borderColor: 'rgba(148, 163, 184, 0.2)' },
            }}
            height={360}
          />
        )}
      </Surface>
    </ObservabilityLayout>
  );
}

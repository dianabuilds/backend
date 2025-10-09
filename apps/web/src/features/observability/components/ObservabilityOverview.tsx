
import React from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowPathIcon,
  ChartBarIcon,
  ClockIcon,
  Cog6ToothIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  GlobeAltIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import { Badge, Button, MetricCard, Skeleton, Surface, Table } from '@ui';
import { ObservabilityLayout } from './ObservabilityLayout';
import { useTelemetryQuery } from '../hooks/useTelemetryQuery';
import { fetchTelemetryOverview } from "@shared/api";
import type { EventHandlerRow, TelemetryOverview } from '@shared/types/observability';

const numberFormatter = new Intl.NumberFormat('en-US');
const percentFormatter = new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 1 });
const timeFormatter = new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

function formatNumber(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '--';
  return numberFormatter.format(value);
}

function formatPercent(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '--';
  return percentFormatter.format(value);
}

function formatUpdated(date: Date | null): string {
  if (!date) return '--';
  return timeFormatter.format(date);
}

function formatMs(value: number | null | undefined): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '--';
  return `${Math.round(value)} ms`;
}

type LlmFlowRow = {
  provider: string;
  model: string;
  stage: string;
  count: number;
  avgLatency: number | null;
};

type WorkerStageRow = {
  stage: string;
  count: number;
  avg: number;
};

type TransitionRow = {
  mode: string;
  count: number;
  latency: number;
  fallback: number;
};
const OVERVIEW_POLL_INTERVAL_MS = 30_000;
export function ObservabilityOverview(): React.ReactElement {
  const { data, loading, error, refresh, lastUpdated } = useTelemetryQuery<TelemetryOverview>({
    fetcher: (signal) => fetchTelemetryOverview({ signal }),
    pollIntervalMs: OVERVIEW_POLL_INTERVAL_MS,
  });

  const showSkeleton = loading && !data;

  const llmFlows = React.useMemo<LlmFlowRow[]>(() => {
    if (!data?.llm) return [];
    const aggregated = new Map<string, LlmFlowRow>();
    data.llm.calls.forEach((metric) => {
      const key = `${metric.provider}:${metric.model}:${metric.stage || 'default'}`;
      const existing = aggregated.get(key);
      if (existing) {
        existing.count += metric.count || 0;
      } else {
        aggregated.set(key, {
          provider: metric.provider,
          model: metric.model,
          stage: metric.stage || '',
          count: metric.count || 0,
          avgLatency: null,
        });
      }
    });
    const latencyLookup = new Map<string, number>();
    data.llm.latency_avg_ms.forEach((metric) => {
      const key = `${metric.provider}:${metric.model}:${metric.stage || 'default'}`;
      latencyLookup.set(key, metric.avg_ms ?? 0);
    });
    aggregated.forEach((row, key) => {
      row.avgLatency = latencyLookup.get(key) ?? null;
    });
    return Array.from(aggregated.values()).sort((a, b) => b.count - a.count).slice(0, 5);
  }, [data?.llm]);

  const workerStages = React.useMemo<WorkerStageRow[]>(() => {
    if (!data?.workers) return [];
    return Object.entries(data.workers.stages ?? {})
      .map(([stage, metrics]) => ({
        stage,
        count: metrics.count ?? 0,
        avg: metrics.avg_ms ?? 0,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }, [data?.workers]);

  const eventHandlers = React.useMemo<EventHandlerRow[]>(() => {
    if (!data?.events) return [];
    return [...(data.events.handlers ?? [])].sort((a, b) => (b.total || 0) - (a.total || 0)).slice(0, 5);
  }, [data?.events]);

  const transitions = React.useMemo<TransitionRow[]>(() => {
    if (!data?.transitions) return [];
    return data.transitions
      .map((item) => ({
        mode: item.mode,
        count: item.count ?? 0,
        latency: item.avg_latency_ms ?? 0,
        fallback: item.fallback_ratio ?? 0,
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }, [data?.transitions]);

  const headerStats = React.useMemo(() => {
    if (!data) return undefined;
    const llmCalls = data.llm?.calls.reduce((acc, metric) => acc + (metric.count || 0), 0) ?? 0;
    const workerJobs = Object.values(data.workers?.jobs ?? {}).reduce((acc, value) => acc + (value || 0), 0);
    const rumTotal = Object.values(data.rum?.counts ?? {}).reduce((acc, value) => acc + (value || 0), 0);
    return [
      {
        label: 'LLM calls',
        value: formatNumber(llmCalls),
        icon: <SparklesIcon className="size-5" aria-hidden="true" />,
      },
      {
        label: 'Worker jobs',
        value: formatNumber(workerJobs),
        icon: <Cog6ToothIcon className="size-5" aria-hidden="true" />,
      },
      {
        label: 'RUM events',
        value: formatNumber(rumTotal),
        icon: <GlobeAltIcon className="size-5" aria-hidden="true" />,
      },
      {
        label: 'Last update',
        value: formatUpdated(lastUpdated),
        hint: `Auto refresh · ${OVERVIEW_POLL_INTERVAL_MS / 1000}s`,
        icon: <ClockIcon className="size-5" aria-hidden="true" />,
      },
    ];
  }, [data, lastUpdated]);
  const errorSurface = error ? (
    <Surface
      variant="frosted"
      className="space-y-4 border border-rose-200/60 bg-rose-50/80 text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/20 dark:text-rose-200"
      data-testid="observability-overview-error"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <ExclamationTriangleIcon className="size-6 shrink-0" aria-hidden="true" />
          <div className="space-y-1">
            <h2 className="text-base font-semibold">Failed to load telemetry overview</h2>
            <p className="text-sm opacity-80">{error}</p>
          </div>
        </div>
        <Button
          type="button"
          variant="outlined"
          color="error"
          size="sm"
          onClick={() => {
            void refresh();
          }}
          disabled={loading}
          data-testid="observability-overview-error-retry"
        >
          Retry
        </Button>
      </div>
    </Surface>
  ) : null;

  const actions = React.useMemo(
    () => (
      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant="outlined"
          size="sm"
          onClick={() => {
            void refresh();
          }}
          disabled={loading}
          data-testid="observability-overview-refresh"
        >
          <ArrowPathIcon className="size-4" aria-hidden="true" />
          Refresh
        </Button>
        <Button
          as={Link}
          to="/observability/rum"
          variant="filled"
          className="shadow-[0_18px_45px_-25px_rgba(79,70,229,0.6)]"
          data-testid="observability-header-cta"
          data-analytics="observability:cta:rum"
        >
          <ChartBarIcon className="size-4" aria-hidden="true" />
          Realtime RUM
        </Button>
      </div>
    ),
    [loading, refresh],
  );

  if (!data && error) {
    return (
      <ObservabilityLayout
        title="Telemetry command centre"
        description="Monitor AI output, worker queues, domain events, transitions, and client-side health from a single pane of glass."
        actions={actions}
      >
        {errorSurface}
      </ObservabilityLayout>
    );
  }

  const workerLatency = data?.workers?.job_avg_ms ?? null;
  const rum = data?.rum;
  const ux = data?.ux;
  return (
    <ObservabilityLayout
      title="Telemetry command centre"
      description="Monitor AI output, worker queues, domain events, transitions, and client-side health from a single pane of glass."
      actions={actions}
      stats={headerStats}
    >
      {errorSurface}
      <div className="grid gap-6 xl:grid-cols-12">
        <Surface variant="frosted" className="space-y-4 xl:col-span-12" data-testid="observability-overview-metrics">
          {showSkeleton ? (
            <div className="space-y-2">
              {[0, 1, 2].map((index) => (
                <Skeleton key={`overview-metric-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : (
            <div className="grid gap-3 md:grid-cols-3">
              <MetricCard
                label="LLM tokens (prompt)"
                value={formatNumber(data?.llm?.tokens_total.find((t) => t.type === 'prompt')?.total ?? 0)}
                description="Aggregated prompt tokens"
                icon={<CpuChipIcon className="size-5" aria-hidden="true" />}
                tone="primary"
              />
              <MetricCard
                label="Worker latency"
                value={formatMs(workerLatency)}
                description="Average job execution time"
                icon={<Cog6ToothIcon className="size-5" aria-hidden="true" />}
                tone="secondary"
              />
              <MetricCard
                label="Login latency"
                value={formatMs(rum?.login_attempt_avg_ms ?? null)}
                description="Real-user auth experience"
                icon={<GlobeAltIcon className="size-5" aria-hidden="true" />}
                tone="neutral"
              />
            </div>
          )}
        </Surface>

        <Surface variant="frosted" className="space-y-4 xl:col-span-6" data-testid="observability-overview-llm">
          <div className="flex items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">LLM flows</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Top providers by call volume.</p>
            </div>
            <Button as={Link} to="/observability/llm" variant="ghost" size="sm" color="neutral">
              View details
            </Button>
          </div>
          {showSkeleton ? (
            <div className="space-y-2">
              {[0, 1, 2].map((index) => (
                <Skeleton key={`overview-llm-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : llmFlows.length ? (
            <div className="overflow-x-auto">
              <Table.Table preset="analytics" zebra>
                <Table.THead>
                  <Table.TR>
                    <Table.TH>Provider</Table.TH>
                    <Table.TH>Model</Table.TH>
                    <Table.TH>Stage</Table.TH>
                    <Table.TH>Calls</Table.TH>
                    <Table.TH>Avg ms</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {llmFlows.map((row, index) => (
                    <Table.TR key={`${row.provider}-${row.model}-${row.stage}-${index}`}>
                      <Table.TD>{row.provider}</Table.TD>
                      <Table.TD>{row.model}</Table.TD>
                      <Table.TD>
                        {row.stage ? <Badge color="info">{row.stage}</Badge> : <span className="text-gray-500">default</span>}
                      </Table.TD>
                      <Table.TD>{formatNumber(row.count)}</Table.TD>
                      <Table.TD>{formatMs(row.avgLatency)}</Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-gray-200/70 bg-white/70 p-6 text-sm text-gray-500 dark:border-dark-600/60 dark:bg-dark-800/40">
              No LLM calls have been recorded for the current window.
            </div>
          )}
        </Surface>

        <Surface variant="frosted" className="space-y-4 xl:col-span-6" data-testid="observability-overview-workers">
          <div className="flex items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Worker stages</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Throughput across background pipelines.</p>
            </div>
            <Button as={Link} to="/observability/workers" variant="ghost" size="sm" color="neutral">
              View details
            </Button>
          </div>
          {showSkeleton ? (
            <div className="space-y-2">
              {[0, 1].map((index) => (
                <Skeleton key={`overview-workers-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : workerStages.length ? (
            <div className="overflow-x-auto">
              <Table.Table preset="analytics" zebra>
                <Table.THead>
                  <Table.TR>
                    <Table.TH>Stage</Table.TH>
                    <Table.TH>Jobs</Table.TH>
                    <Table.TH>Avg ms</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {workerStages.map((row) => (
                    <Table.TR key={row.stage}>
                      <Table.TD>{row.stage}</Table.TD>
                      <Table.TD>{formatNumber(row.count)}</Table.TD>
                      <Table.TD>{formatMs(row.avg)}</Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-gray-200/70 bg-white/70 p-6 text-sm text-gray-500 dark:border-dark-600/60 dark:bg-dark-800/40">
              Worker telemetry has no activity for the current window.
            </div>
          )}
        </Surface>

        <Surface variant="frosted" className="space-y-4 xl:col-span-6" data-testid="observability-overview-events">
          <div className="flex items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Domain events</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Latency and failure ratio per handler.</p>
            </div>
            <Button as={Link} to="/observability/events" variant="ghost" size="sm" color="neutral">
              View details
            </Button>
          </div>
          {showSkeleton ? (
            <div className="space-y-2">
              {[0, 1, 2].map((index) => (
                <Skeleton key={`overview-events-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : eventHandlers.length ? (
            <div className="overflow-x-auto">
              <Table.Table preset="analytics" zebra>
                <Table.THead>
                  <Table.TR>
                    <Table.TH>Event</Table.TH>
                    <Table.TH>Handler</Table.TH>
                    <Table.TH>Success</Table.TH>
                    <Table.TH>Failure</Table.TH>
                    <Table.TH>Avg ms</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {eventHandlers.map((handler) => (
                    <Table.TR key={`${handler.event}-${handler.handler}`}>
                      <Table.TD className="font-mono text-xs">{handler.event}</Table.TD>
                      <Table.TD>{handler.handler}</Table.TD>
                      <Table.TD>{formatNumber(handler.success)}</Table.TD>
                      <Table.TD className={handler.failure ? 'text-rose-600 dark:text-rose-400' : ''}>
                        {formatNumber(handler.failure)}
                      </Table.TD>
                      <Table.TD>{formatMs(handler.avg_ms ?? 0)}</Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-gray-200/70 bg-white/70 p-6 text-sm text-gray-500 dark:border-dark-600/60 dark:bg-dark-800/40">
              Domain events have not been ingested yet.
            </div>
          )}
        </Surface>

        <Surface variant="frosted" className="space-y-4 xl:col-span-6" data-testid="observability-overview-transitions">
          <div className="flex items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">UI transitions</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Routing latency and fallback ratio.</p>
            </div>
            <Button as={Link} to="/observability/transitions" variant="ghost" size="sm" color="neutral">
              View details
            </Button>
          </div>
          {showSkeleton ? (
            <div className="space-y-2">
              {[0, 1].map((index) => (
                <Skeleton key={`overview-transitions-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : transitions.length ? (
            <div className="overflow-x-auto">
              <Table.Table preset="analytics" zebra>
                <Table.THead>
                  <Table.TR>
                    <Table.TH>Mode</Table.TH>
                    <Table.TH>Transitions</Table.TH>
                    <Table.TH>Avg ms</Table.TH>
                    <Table.TH>Fallback</Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {transitions.map((row) => (
                    <Table.TR key={row.mode}>
                      <Table.TD>{row.mode}</Table.TD>
                      <Table.TD>{formatNumber(row.count)}</Table.TD>
                      <Table.TD>{formatMs(row.latency)}</Table.TD>
                      <Table.TD>{formatPercent(row.fallback)}</Table.TD>
                    </Table.TR>
                  ))}
                </Table.TBody>
              </Table.Table>
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-gray-200/70 bg-white/70 p-6 text-sm text-gray-500 dark:border-dark-600/60 dark:bg-dark-800/40">
              Transition telemetry has not been captured yet.
            </div>
          )}
        </Surface>

        <Surface variant="frosted" className="space-y-4 xl:col-span-12" data-testid="observability-overview-rum">
          <div className="flex items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">UX & RUM snapshot</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Client-side performance and editorial cadence.</p>
            </div>
            <Button as={Link} to="/observability/rum" variant="ghost" size="sm" color="neutral">
              View details
            </Button>
          </div>
          {showSkeleton ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full rounded-2xl" />
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-white/60 bg-white/70 p-4 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/60">
                <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/70">
                  DOM content loaded
                </div>
                <div className="mt-1 text-lg font-semibold text-gray-900 dark:text-white">
                  {formatMs(rum?.navigation_avg.dom_content_loaded_ms ?? null)}
                </div>
                <div className="text-xs text-gray-500 dark:text-dark-200/70">Median navigation timing</div>
              </div>
              <div className="rounded-2xl border border-white/60 bg-white/70 p-4 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/60">
                <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/70">
                  Load event
                </div>
                <div className="mt-1 text-lg font-semibold text-gray-900 dark:text-white">
                  {formatMs(rum?.navigation_avg.load_event_ms ?? null)}
                </div>
                <div className="text-xs text-gray-500 dark:text-dark-200/70">Full page load time</div>
              </div>
              <div className="rounded-2xl border border-white/60 bg-white/70 p-4 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/60">
                <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/70">
                  Save &amp; Next cadence
                </div>
                <div className="mt-1 text-lg font-semibold text-gray-900 dark:text-white">
                  {formatNumber(ux?.save_next_total ?? 0)}
                </div>
                <div className="text-xs text-gray-500 dark:text-dark-200/70">Editorial workflow shortcuts</div>
              </div>
            </div>
          )}
        </Surface>
      </div>
    </ObservabilityLayout>
  );
}


import React from 'react';
import {
  ArrowPathIcon,
  ArrowTrendingUpIcon,
  ArrowsRightLeftIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import {
  ApexChart,
  Badge,
  Button,
  Input,
  MetricCard,
  Skeleton,
  Surface,
  Table,
  TablePagination,
} from '@ui';
import { ObservabilityLayout } from './ObservabilityLayout';
import { fetchTransitionsSummary } from '@shared/api/observability';
import { useTelemetryQuery } from '../hooks/useTelemetryQuery';
import { TransitionModeSummary } from '@shared/types/observability';
import type { PageHeroMetric } from '@ui/patterns/PageHero';

const numberFormatter = new Intl.NumberFormat('en-US');
const timeFormatter = new Intl.DateTimeFormat('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

function formatUpdated(date: Date | null): string {
  if (!date) return '—';
  return timeFormatter.format(date);
}

  function formatNumber(value: number | null | undefined) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
    return numberFormatter.format(value);
  }

  function formatLatency(value: number | null | undefined) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
    return `${Math.round(value)} ms`;
  }

const TRANSITIONS_POLL_INTERVAL_MS = 30_000;

  function formatPercent(value: number | null | undefined) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return '—';
    return `${(value * 100).toFixed(2)}%`;
  }

export function ObservabilityTransitions(): React.ReactElement {
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [search, setSearch] = React.useState('');

  const { data, loading, error, refresh, lastUpdated } = useTelemetryQuery<TransitionModeSummary[]>({
    fetcher: (signal) => fetchTransitionsSummary({ signal }),
    pollIntervalMs: TRANSITIONS_POLL_INTERVAL_MS,
  });

  const rows = React.useMemo(() => data ?? [], [data]);
  const trimmedSearch = search.trim().toLowerCase();
  const filteredRows = React.useMemo(() => {
    if (!trimmedSearch) return rows;
    return rows.filter((row) => row.mode.toLowerCase().includes(trimmedSearch));
  }, [rows, trimmedSearch]);

  React.useEffect(() => {
    setPage(1);
  }, [trimmedSearch, rows.length]);

  const totalRows = filteredRows.length;
  const paginatedRows = React.useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, page, pageSize]);
  const hasNext = page * pageSize < totalRows;

  const totals = React.useMemo(() => {
    if (!rows.length) {
      return {
        totalTransitions: 0,
        averageLatency: 0,
        averageNoRoute: 0,
        averageFallback: 0,
      };
    }
    const totalTransitions = rows.reduce((acc, row) => acc + (row.count || 0), 0);
    const averageLatency = rows.reduce((acc, row) => acc + (row.avg_latency_ms || 0), 0) / rows.length;
    const averageNoRoute = rows.reduce((acc, row) => acc + (row.no_route_ratio || 0), 0) / rows.length;
    const averageFallback = rows.reduce((acc, row) => acc + (row.fallback_ratio || 0), 0) / rows.length;
    return { totalTransitions, averageLatency, averageNoRoute, averageFallback };
  }, [rows]);

  const extremes = React.useMemo(() => {
    if (!rows.length) {
      return { slowest: null, highestFallback: null, highestNoRoute: null } as const;
    }
    return rows.reduce(
      (acc, row) => {
        if (!acc.slowest || (row.avg_latency_ms || 0) > (acc.slowest.avg_latency_ms || 0)) acc.slowest = row;
        if (!acc.highestFallback || (row.fallback_ratio || 0) > (acc.highestFallback.fallback_ratio || 0)) acc.highestFallback = row;
        if (!acc.highestNoRoute || (row.no_route_ratio || 0) > (acc.highestNoRoute.no_route_ratio || 0)) acc.highestNoRoute = row;
        return acc;
      },
      { slowest: null as TransitionModeSummary | null, highestFallback: null as TransitionModeSummary | null, highestNoRoute: null as TransitionModeSummary | null },
    );
  }, [rows]);

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
          data-testid="observability-transitions-refresh"
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
            id: 'transitions-total',
            label: 'Transitions processed',
            value: formatNumber(totals.totalTransitions),
          helper: `${formatPercent(totals.averageFallback)} fallback avg`,
          icon: <ArrowsRightLeftIcon className="size-4" aria-hidden="true" />,
          accent: 'positive',
        },
        {
          id: 'transitions-latency',
          label: 'Average latency',
          value: formatLatency(totals.averageLatency),
          helper: extremes.slowest ? `${extremes.slowest.mode} peak` : 'Awaiting data',
          icon: <ArrowTrendingUpIcon className="size-4" aria-hidden="true" />,
          accent: 'warning',
        },
          {
            id: 'transitions-no-route',
            label: 'No-route avg',
            value: formatPercent(totals.averageNoRoute),
            helper: extremes.highestNoRoute ? `${extremes.highestNoRoute.mode} max` : 'Awaiting data',
            icon: <ShieldCheckIcon className="size-4" aria-hidden="true" />,
            accent: 'danger',
          },
        ]
      : undefined;

  if (error) {
    return (
      <ObservabilityLayout title="Routing telemetry" actions={heroActions} metrics={heroMetrics}>
        <Surface
          variant="soft"
          className="border border-rose-200/60 bg-rose-50/60 text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/20 dark:text-rose-200"
          role="alert"
          data-testid="observability-transitions-error"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <ExclamationTriangleIcon className="mt-0.5 size-6 shrink-0" aria-hidden="true" />
              <div className="space-y-1">
                <h2 className="text-sm font-semibold">Routing telemetry failed to load</h2>
                <p className="text-sm opacity-80">{error}</p>
              </div>
            </div>
            <Button onClick={() => refresh()} variant="outlined" color="error" data-testid="observability-transitions-retry">
              Retry request
            </Button>
          </div>
        </Surface>
      </ObservabilityLayout>
    );
  }

  const latencySeries = filteredRows.map((row) => Math.round(row.avg_latency_ms || 0));
  const latencyCategories = filteredRows.map((row) => row.mode);
  const ratioSeries = [
    {
      name: 'No-route %',
      data: filteredRows.map((row) => Math.round((row.no_route_ratio || 0) * 100)),
    },
    {
      name: 'Fallback %',
      data: filteredRows.map((row) => Math.round((row.fallback_ratio || 0) * 100)),
    },
  ];

  const metricCards = hasData
    ? [
        {
          id: 'slowest',
          label: 'Slowest mode',
          value: extremes.slowest ? formatLatency(extremes.slowest.avg_latency_ms) : '—',
          description: extremes.slowest ? extremes.slowest.mode : 'Awaiting data',
          tone: 'warning' as const,
        },
        {
          id: 'fallback',
          label: 'Highest fallback',
          value: extremes.highestFallback ? formatPercent(extremes.highestFallback.fallback_ratio) : '—',
          description: extremes.highestFallback ? extremes.highestFallback.mode : 'Awaiting data',
          tone: 'secondary' as const,
        },
        {
          id: 'no-route',
          label: 'Highest no-route',
          value: extremes.highestNoRoute ? formatPercent(extremes.highestNoRoute.no_route_ratio) : '—',
          description: extremes.highestNoRoute ? extremes.highestNoRoute.mode : 'Awaiting data',
          tone: 'warning' as const,
        },
        {
          id: 'throughput',
          label: 'Filtered transitions',
          value: formatNumber(filteredRows.reduce((acc, row) => acc + (row.count || 0), 0)),
          description: `${filteredRows.length} modes`,
          tone: 'primary' as const,
        },
      ]
    : [];

  return (
    <ObservabilityLayout
      title="Routing telemetry"
      description="Latency, fallback usage, and volume per transition mode."
      actions={heroActions}
      metrics={heroMetrics}
    >
      <div className="grid gap-6 xl:grid-cols-12">
        <div className="xl:col-span-12" data-testid="observability-transitions-filters" data-analytics="observability:transitions:filters">
          <Surface variant="soft" className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="space-y-1">
                <h2 className="text-sm font-semibold text-gray-900 dark:text-white">Filter modes</h2>
                <p className="text-xs text-gray-500 dark:text-dark-200/70">Search by mode key to focus on specific flows.</p>
              </div>
              <Badge color="neutral" variant="soft" className="text-[11px]">
                {filteredRows.length} of {rows.length} modes
              </Badge>
            </div>
            <Input
              label="Search modes"
              placeholder="linked_fallback, no_route, llm_explore"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              data-testid="observability-transitions-search"
              data-analytics="observability:transitions:filter-search"
            />
          </Surface>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:col-span-12 xl:grid-cols-4" data-testid="observability-transitions-metrics">
          {hasData
            ? metricCards.map((metric) => (
                <div
                  key={metric.id}
                  data-testid={`observability-transitions-metric-${metric.id}`}
                  data-analytics={`observability:transitions:${metric.id}`}
                >
                  <MetricCard
                    label={metric.label}
                    value={metric.value}
                    description={metric.description}
                    tone={metric.tone}
                  />
                </div>
              ))
            : Array.from({ length: 4 }).map((_, index) => (
                <Surface key={`transitions-metric-skeleton-${index}`} variant="soft" className="rounded-3xl p-5">
                  <Skeleton className="h-3 w-24 rounded" />
                  <Skeleton className="mt-4 h-8 w-32 rounded" />
                  <Skeleton className="mt-3 h-3 w-36 rounded" />
                </Surface>
              ))}
        </div>

        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-transitions-latency"
          data-analytics="observability:transitions:latency-chart"
        >
          <header className="space-y-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Average latency by mode</h2>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">Identify modes that slow down player journeys.</p>
          </header>

          {isLoading ? (
            <Skeleton className="h-72 w-full rounded-3xl" />
          ) : filteredRows.length === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <ArrowsRightLeftIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No modes match the filter</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Adjust the search or wait for routing events to arrive.</p>
            </div>
          ) : (
            <ApexChart
              type="bar"
              series={[
                {
                  name: 'Avg ms',
                  data: latencySeries,
                },
              ]}
              options={{ xaxis: { categories: latencyCategories, labels: { rotate: -45 } }, dataLabels: { enabled: false } }}
              height={360}
            />
          )}
        </Surface>

        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-transitions-ratios"
          data-analytics="observability:transitions:ratios-chart"
        >
          <header className="space-y-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">No-route and fallback ratios</h2>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">Track safety nets and fallback behaviour by mode.</p>
          </header>

          {isLoading ? (
            <Skeleton className="h-72 w-full rounded-3xl" />
          ) : filteredRows.length === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <ShieldCheckIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No ratio data available</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Fallback metrics will appear once routing decisions are logged.</p>
            </div>
          ) : (
            <ApexChart
              type="bar"
              series={ratioSeries}
              options={{ xaxis: { categories: latencyCategories, labels: { rotate: -45 } }, legend: { show: true }, dataLabels: { enabled: false } }}
              height={360}
            />
          )}
        </Surface>

        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-transitions-table"
          data-analytics="observability:transitions:table"
        >
          <header className="flex flex-col gap-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Modes table</h2>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">Full list of transitions with counts, latency, and safety-net ratios.</p>
          </header>

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={`transitions-table-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : totalRows === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <ArrowsRightLeftIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No modes to display</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Reset filters or wait for additional telemetry.</p>
            </div>
          ) : (
            <>
              <div className="hidden md:block">
                <div className="overflow-x-auto">
                  <Table.Table preset="analytics" zebra hover>
                    <Table.THead>
                      <Table.TR>
                        <Table.TH>Mode</Table.TH>
                        <Table.TH>Avg ms</Table.TH>
                        <Table.TH>No-route %</Table.TH>
                        <Table.TH>Fallback %</Table.TH>
                        <Table.TH>Count</Table.TH>
                      </Table.TR>
                    </Table.THead>
                    <Table.TBody>
                      {paginatedRows.map((row, index) => (
                        <Table.TR
                          key={`${row.mode}-${index}`}
                          data-testid={`observability-transitions-row-${(page - 1) * pageSize + index}`}
                          data-analytics="observability:transitions:table-row"
                          className="cursor-pointer transition hover:-translate-y-[1px]"
                        >
                          <Table.TD className="font-mono text-xs">{row.mode}</Table.TD>
                          <Table.TD>{Math.round(row.avg_latency_ms || 0)}</Table.TD>
                          <Table.TD>{formatPercent(row.no_route_ratio)}</Table.TD>
                          <Table.TD>{formatPercent(row.fallback_ratio)}</Table.TD>
                          <Table.TD>{formatNumber(row.count)}</Table.TD>
                        </Table.TR>
                      ))}
                    </Table.TBody>
                  </Table.Table>
                </div>
              </div>

              <div className="space-y-3 md:hidden">
                {paginatedRows.map((row, index) => (
                  <Surface
                    key={`${row.mode}-${index}`}
                    variant="soft"
                    className="rounded-3xl p-5"
                    data-testid={`observability-transitions-card-${(page - 1) * pageSize + index}`}
                  >
                    <div className="font-mono text-xs text-gray-500 dark:text-dark-200/80">{row.mode}</div>
                    <dl className="mt-3 grid grid-cols-2 gap-3 text-xs text-gray-600 dark:text-dark-200/80">
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Avg ms</dt>
                        <dd>{Math.round(row.avg_latency_ms || 0)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Count</dt>
                        <dd>{formatNumber(row.count)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">No-route %</dt>
                        <dd>{formatPercent(row.no_route_ratio)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Fallback %</dt>
                        <dd>{formatPercent(row.fallback_ratio)}</dd>
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
                data-testid="observability-transitions-pagination"
              />
            </>
          )}
        </Surface>
      </div>
    </ObservabilityLayout>
  );
}






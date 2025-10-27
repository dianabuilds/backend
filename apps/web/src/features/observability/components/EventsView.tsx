import React from 'react';
import {
  ClockIcon,
  ExclamationTriangleIcon,
  InboxIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import {
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
import { ObservabilityHeroActions } from './ObservabilityHeroActions';
import { ObservabilitySummaryMetrics } from './ObservabilitySummaryMetrics';
import { fetchEventsSummary } from '@shared/api/observability';
import { useTelemetryQuery } from '../hooks/useTelemetryQuery';
import { formatNumber, formatPercent } from '../utils/format';
import { EventsSummary } from '@shared/types/observability';
import type { PageHeroMetric } from '@ui/patterns/PageHero';

const EVENTS_POLL_INTERVAL_MS = 30_000;

export function ObservabilityEvents(): React.ReactElement {
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(10);
  const [eventFilter, setEventFilter] = React.useState('');
  const [handlerFilter, setHandlerFilter] = React.useState('');

  const { data, loading, error, refresh, lastUpdated } = useTelemetryQuery<EventsSummary>({
    fetcher: (signal) => fetchEventsSummary({ signal }),
    pollIntervalMs: EVENTS_POLL_INTERVAL_MS,
  });

  const handlers = React.useMemo(() => {
    const list = data?.handlers ?? [];
    return [...list].sort((a, b) => (b.failure || 0) - (a.failure || 0));
  }, [data?.handlers]);

  const totals = React.useMemo(() => {
    const totalSuccess = handlers.reduce((acc, row) => acc + (row.success || 0), 0);
    const totalFailure = handlers.reduce((acc, row) => acc + (row.failure || 0), 0);
    const totalEvents = totalSuccess + totalFailure;
    const failureRatio = totalEvents ? totalFailure / totalEvents : 0;
    const averageLatency = handlers.length
      ? handlers.reduce((acc, row) => acc + (row.avg_ms || 0), 0) / handlers.length
      : 0;
    return { totalHandlers: handlers.length, totalEvents, totalSuccess, totalFailure, failureRatio, averageLatency };
  }, [handlers]);

  const trimmedEvent = eventFilter.trim().toLowerCase();
  const trimmedHandler = handlerFilter.trim().toLowerCase();

  const filteredHandlers = React.useMemo(() => {
    return handlers.filter((row) => {
      const eventMatch = trimmedEvent ? row.event.toLowerCase().includes(trimmedEvent) : true;
      const handlerMatch = trimmedHandler ? row.handler.toLowerCase().includes(trimmedHandler) : true;
      return eventMatch && handlerMatch;
    });
  }, [handlers, trimmedEvent, trimmedHandler]);

  React.useEffect(() => {
    setPage(1);
  }, [handlers.length, eventFilter, handlerFilter]);

  const totalRows = filteredHandlers.length;
  const start = (page - 1) * pageSize;
  const paginatedRows = filteredHandlers.slice(start, start + pageSize);
  const hasNext = page * pageSize < totalRows;

  const hasData = Boolean(data) && !loading && !error;
  const isLoading = loading || (!data && !error);

  const topFailure = handlers.reduce((best, row) => ((row.failure || 0) > (best?.failure || 0) ? row : best), handlers[0] ?? null);
  const topLatency = handlers.reduce((best, row) => ((row.avg_ms || 0) > (best?.avg_ms || 0) ? row : best), handlers[0] ?? null);

  const heroActions = React.useMemo(
    () => (
      <ObservabilityHeroActions
        lastUpdated={lastUpdated}
        onRefresh={() => {
          void refresh();
        }}
        refreshing={loading}
        refreshTestId="observability-events-refresh"
      />
    ),
    [lastUpdated, loading, refresh],
  );

  const heroMetrics: PageHeroMetric[] | undefined = hasData
      ? [
          {
            id: 'events-handlers',
            label: 'Handlers tracked',
            value: formatNumber(totals.totalHandlers),
          helper: `${formatNumber(totals.totalEvents)} executions`,
          icon: <InboxIcon className="size-4" aria-hidden="true" />,
        },
        {
          id: 'events-latency',
          label: 'Average latency',
          value: `${Math.round(totals.averageLatency || 0)} ms`,
          helper: topLatency ? `${topLatency.handler} peak` : 'Awaiting data',
          icon: <ClockIcon className="size-4" aria-hidden="true" />,
          accent: 'warning',
        },
        {
          id: 'events-failure',
          label: 'Failure ratio',
          value: formatPercent(totals.failureRatio, { maximumFractionDigits: 2 }),
            helper: `${formatNumber(totals.totalFailure)} failures`,
            icon: <ExclamationTriangleIcon className="size-4" aria-hidden="true" />,
            accent: 'danger',
          },
        ]
      : undefined;

  if (error) {
    return (
      <ObservabilityLayout title="Domain events" actions={heroActions}>
        <Surface
          variant="soft"
          className="border border-rose-200/60 bg-rose-50/60 text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/20 dark:text-rose-200"
          role="alert"
          data-testid="observability-events-error"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <ExclamationTriangleIcon className="mt-0.5 size-6 shrink-0" aria-hidden="true" />
              <div className="space-y-1">
                <h2 className="text-sm font-semibold">Event telemetry failed to load</h2>
                <p className="text-sm opacity-80">{error}</p>
              </div>
            </div>
            <Button onClick={() => refresh()} variant="outlined" color="error" data-testid="observability-events-retry">
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
          id: 'top-failure',
          label: 'Top failing handler',
          value: topFailure ? formatNumber(topFailure.failure) : '—',
          description: topFailure ? `${topFailure.handler}` : 'Awaiting data',
          tone: 'warning' as const,
        },
        {
          id: 'top-latency',
          label: 'Slowest handler',
          value: topLatency ? `${Math.round(topLatency.avg_ms || 0)} ms` : '—',
          description: topLatency ? `${topLatency.handler}` : 'Awaiting data',
          tone: 'warning' as const,
        },
        {
          id: 'success-rate',
          label: 'Success rate',
          value: totals.totalEvents
            ? formatPercent(totals.totalSuccess / totals.totalEvents, { maximumFractionDigits: 2 })
            : '—',
          description: `${formatNumber(totals.totalSuccess)} successes`,
          tone: 'success' as const,
        },
        {
          id: 'filtered',
          label: 'Filtered handlers',
          value: formatNumber(filteredHandlers.length),
          description: `${formatNumber(totalRows)} entries`,
          tone: 'primary' as const,
        },
      ]
    : [];

  return (
    <ObservabilityLayout
      title="Domain events"
      description="Handler success rates, latencies, and volumes to catch regressions early."
      actions={heroActions}
    >
      <ObservabilitySummaryMetrics metrics={heroMetrics} />
      <div className="grid gap-6 xl:grid-cols-12">
        <div className="xl:col-span-12" data-testid="observability-events-filters" data-analytics="observability:events:filters">
          <Surface variant="soft" className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="space-y-1">
                <h2 className="text-sm font-semibold text-gray-900 dark:text-white">Filter handlers</h2>
                <p className="text-xs text-gray-500 dark:text-dark-200/70">Combine event and handler filters to isolate problematic consumers.</p>
              </div>
              <Badge color="neutral" variant="soft" className="flex items-center gap-1 text-[11px]">
                <MagnifyingGlassIcon className="size-3" aria-hidden="true" />
                {filteredHandlers.length} of {handlers.length} handlers
              </Badge>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              <Input
                label="Filter by event"
                placeholder="user.registered"
                value={eventFilter}
                onChange={(event) => setEventFilter(event.target.value)}
                data-testid="observability-events-filter-event"
                data-analytics="observability:events:filter-event"
              />
              <Input
                label="Filter by handler"
                placeholder="domains.platform.notifications"
                value={handlerFilter}
                onChange={(event) => setHandlerFilter(event.target.value)}
                data-testid="observability-events-filter-handler"
                data-analytics="observability:events:filter-handler"
              />
            </div>
          </Surface>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:col-span-12 xl:grid-cols-4" data-testid="observability-events-metrics">
          {hasData
            ? metricCards.map((metric) => (
                <div
                  key={metric.id}
                  data-testid={`observability-events-metric-${metric.id}`}
                  data-analytics={`observability:events:${metric.id}`}
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
                <Surface key={`events-metric-skeleton-${index}`} variant="soft" className="rounded-3xl p-5">
                  <Skeleton className="h-3 w-24 rounded" />
                  <Skeleton className="mt-4 h-8 w-32 rounded" />
                  <Skeleton className="mt-3 h-3 w-36 rounded" />
                </Surface>
              ))}
        </div>

        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-events-table"
          data-analytics="observability:events:table"
        >
          <header className="flex flex-col gap-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Event handlers</h2>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">Latency and reliability per handler with responsive cards for mobile.</p>
          </header>

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={`events-table-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : totalRows === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <MagnifyingGlassIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No handlers match the filters</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Relax the filters or monitor for upcoming event activity.</p>
            </div>
          ) : (
            <>
              <div className="hidden md:block">
                <div className="overflow-x-auto">
                  <Table.Table preset="analytics" zebra hover>
                    <Table.THead>
                      <Table.TR>
                        <Table.TH>Event</Table.TH>
                        <Table.TH>Handler</Table.TH>
                        <Table.TH>Success</Table.TH>
                        <Table.TH>Failure</Table.TH>
                        <Table.TH>Avg ms</Table.TH>
                        <Table.TH>Total</Table.TH>
                      </Table.TR>
                    </Table.THead>
                    <Table.TBody>
                      {paginatedRows.map((row, index) => (
                        <Table.TR
                          key={`${row.event}-${row.handler}-${index}`}
                          data-testid={`observability-events-row-${(page - 1) * pageSize + index}`}
                          data-analytics="observability:events:table-row"
                          className="cursor-pointer transition hover:-translate-y-[1px]"
                        >
                          <Table.TD className="font-mono text-xs">{row.event}</Table.TD>
                          <Table.TD>{row.handler}</Table.TD>
                          <Table.TD>{formatNumber(row.success)}</Table.TD>
                          <Table.TD className={row.failure ? 'text-rose-600 dark:text-rose-400' : ''}>{formatNumber(row.failure)}</Table.TD>
                          <Table.TD>{Math.round(row.avg_ms || 0)}</Table.TD>
                          <Table.TD>{formatNumber(row.total)}</Table.TD>
                        </Table.TR>
                      ))}
                    </Table.TBody>
                  </Table.Table>
                </div>
              </div>

              <div className="space-y-3 md:hidden">
                {paginatedRows.map((row, index) => (
                  <Surface
                    key={`${row.event}-${row.handler}-${index}`}
                    variant="soft"
                    className="rounded-3xl p-5"
                    data-testid={`observability-events-card-${(page - 1) * pageSize + index}`}
                  >
                    <div className="font-mono text-xs text-gray-500 dark:text-dark-200/80">{row.event}</div>
                    <div className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">{row.handler}</div>
                    <dl className="mt-3 grid grid-cols-2 gap-3 text-xs text-gray-600 dark:text-dark-200/80">
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Success</dt>
                        <dd>{formatNumber(row.success)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Failure</dt>
                        <dd className={row.failure ? 'text-rose-600 dark:text-rose-400' : ''}>{formatNumber(row.failure)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Avg ms</dt>
                        <dd>{Math.round(row.avg_ms || 0)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Total</dt>
                        <dd>{formatNumber(row.total)}</dd>
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
                data-testid="observability-events-pagination"
              />
            </>
          )}
        </Surface>
      </div>
    </ObservabilityLayout>
  );
}










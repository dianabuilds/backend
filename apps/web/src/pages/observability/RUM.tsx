import React from 'react';
import {
  ArrowsUpDownIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  GlobeAltIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import {
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
import { fetchRumEvents, fetchRumSummary } from './api';
import { useTelemetryQuery } from './useTelemetryQuery';
import { RumEventRow, RumSummary } from './types';
import { usePaginatedQuery } from '../../shared/hooks/usePaginatedQuery';

const numberFormatter = new Intl.NumberFormat('en-US');

function formatNumber(value: number | null | undefined) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '--';
  return numberFormatter.format(value);
}

function formatLatency(value: number | null | undefined) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return '--';
  return `${Math.round(value)} ms`;
}

function formatTs(value: string | number) {
  if (!value) return '--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  const dd = String(date.getDate()).padStart(2, '0');
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const yyyy = date.getFullYear();
  const hh = String(date.getHours()).padStart(2, '0');
  const min = String(date.getMinutes()).padStart(2, '0');
  return `${dd}.${mm}.${yyyy} ${hh}:${min}`;
}

export default function ObservabilityRUM() {
  const [windowSize, setWindowSize] = React.useState(500);
  const [eventFilter, setEventFilter] = React.useState('');
  const [urlFilter, setUrlFilter] = React.useState('');

  const [countsPage, setCountsPage] = React.useState(1);
  const [countsPageSize, setCountsPageSize] = React.useState(10);

  const { data: summary, loading, error, refresh } = useTelemetryQuery<RumSummary>({
    fetcher: (signal) => fetchRumSummary(signal, windowSize),
    deps: [windowSize],
  });

  const eventsQuery = usePaginatedQuery<RumEventRow, RumEventRow[]>({
    fetcher: ({ page, pageSize, signal }) =>
      fetchRumEvents(
        {
          event: eventFilter.trim() || undefined,
          url: urlFilter.trim() || undefined,
          offset: (page - 1) * pageSize,
          limit: pageSize,
        },
        signal,
      ),
    mapResponse: (response, { pageSize }) => ({
      items: response,
      hasNext: response.length === pageSize,
    }),
    dependencies: [eventFilter, urlFilter],
    initialPageSize: 20,
  });

  const {
    items: eventRows,
    page: eventPage,
    setPage: setEventPage,
    pageSize: eventPageSize,
    setPageSize: setEventPageSize,
    hasNext: eventsHasNext,
    loading: eventsLoading,
    error: eventsError,
  } = eventsQuery;

  const countsLength = React.useMemo(() => Object.keys(summary?.counts ?? {}).length, [summary]);

  React.useEffect(() => {
    setCountsPage(1);
  }, [countsLength]);

  React.useEffect(() => {
    setEventPage(1);
  }, [eventFilter, urlFilter, setEventPage]);

  const hasData = Boolean(summary) && !loading && !error;
  const isLoading = loading || (!summary && !error);

  const nav = summary?.navigation_avg;
  const counts = React.useMemo(
    () => Object.entries(summary?.counts || {}).map(([event, count]) => ({ event, count: count as number })),
    [summary?.counts],
  );
  const countsTotal = counts.length;
  const countsStart = (countsPage - 1) * countsPageSize;
  const countsRows = counts.slice(countsStart, countsStart + countsPageSize);
  const countsHasNext = countsPage * countsPageSize < countsTotal;

  const totalEvents = summary?.window ? formatNumber(summary.window) : '--';

  const headerStats = hasData
    ? [
        {
          label: 'Window size',
          value: totalEvents,
          hint: 'Events considered in summaries',
          icon: <ChartBarIcon className="size-4" aria-hidden="true" />,
        },
        {
          label: 'Login latency',
          value: formatLatency(summary?.login_attempt_avg_ms ?? null),
          hint: 'Average login attempt duration',
          icon: <ArrowsUpDownIcon className="size-4" aria-hidden="true" />,
        },
        {
          label: 'TTFB average',
          value: formatLatency(nav?.ttfb_ms ?? null),
          hint: `Load ${formatLatency(nav?.load_event_ms ?? null)}`,
          icon: <GlobeAltIcon className="size-4" aria-hidden="true" />,
        },
      ]
    : undefined;

  if (error) {
    return (
      <ObservabilityLayout title="RUM telemetry">
        <Surface
          variant="soft"
          className="border border-rose-200/60 bg-rose-50/60 text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/20 dark:text-rose-200"
          role="alert"
          data-testid="observability-rum-error"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <ExclamationTriangleIcon className="mt-0.5 size-6 shrink-0" aria-hidden="true" />
              <div className="space-y-1">
                <h2 className="text-sm font-semibold">RUM telemetry failed to load</h2>
                <p className="text-sm opacity-80">{error}</p>
              </div>
            </div>
            <Button onClick={() => refresh()} variant="outlined" color="error" data-testid="observability-rum-retry">
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
          id: 'login',
          label: 'Login avg',
          value: formatLatency(summary?.login_attempt_avg_ms ?? null),
          description: 'Authentication flow duration',
          tone: 'primary' as const,
        },
        {
          id: 'ttfb',
          label: 'TTFB avg',
          value: formatLatency(nav?.ttfb_ms ?? null),
          description: 'Time to first byte for navigation',
          tone: 'secondary' as const,
        },
        {
          id: 'load',
          label: 'Load event avg',
          value: formatLatency(nav?.load_event_ms ?? null),
          description: 'Window load completion',
          tone: 'success' as const,
        },
        {
          id: 'dom',
          label: 'DOM content loaded',
          value: formatLatency(nav?.dom_content_loaded_ms ?? null),
          description: 'DOMContentLoaded timing',
          tone: 'warning' as const,
        },
      ]
    : [];

  return (
    <ObservabilityLayout
      title="RUM telemetry"
      description="Experience metrics and raw events collected from the browser SDK."
      stats={headerStats}
    >
      <div className="grid gap-6 xl:grid-cols-12">
        <div className="xl:col-span-12" data-testid="observability-rum-filters" data-analytics="observability:rum:filters">
          <Surface variant="soft" className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="space-y-1">
                <h2 className="text-sm font-semibold text-gray-900 dark:text-white">Filter events</h2>
                <p className="text-xs text-gray-500 dark:text-dark-200/70">Adjust window size and narrow down by event name or URL.</p>
              </div>
              <Badge color="neutral" variant="soft" className="text-[11px]">{eventRows.length} recent events</Badge>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/80">Summary window</label>
                <Select
                  value={String(windowSize)}
                  onChange={(event) => setWindowSize(Number(event.target.value))}
                  data-testid="observability-rum-window"
                  data-analytics="observability:rum:filter-window"
                >
                  {[100, 250, 500, 750, 1000].map((option) => (
                    <option key={option} value={option}>
                      last {option} events
                    </option>
                  ))}
                </Select>
              </div>
              <Input
                label="Filter by event"
                placeholder="login_attempt, navigation"
                value={eventFilter}
                onChange={(event) => setEventFilter(event.target.value)}
                data-testid="observability-rum-filter-event"
                data-analytics="observability:rum:filter-event"
              />
              <Input
                label="Filter by URL"
                placeholder="/nodes, /login"
                value={urlFilter}
                onChange={(event) => setUrlFilter(event.target.value)}
                data-testid="observability-rum-filter-url"
                data-analytics="observability:rum:filter-url"
              />
            </div>
          </Surface>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:col-span-12 xl:grid-cols-4" data-testid="observability-rum-metrics">
          {hasData
            ? metricCards.map((metric) => (
                <div
                  key={metric.id}
                  data-testid={`observability-rum-metric-${metric.id}`}
                  data-analytics={`observability:rum:${metric.id}`}
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
                <Surface key={`rum-metric-skeleton-${index}`} variant="soft" className="rounded-3xl p-5">
                  <Skeleton className="h-3 w-24 rounded" />
                  <Skeleton className="mt-4 h-8 w-32 rounded" />
                  <Skeleton className="mt-3 h-3 w-36 rounded" />
                </Surface>
              ))}
        </div>

        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-rum-counts"
          data-analytics="observability:rum:counts"
        >
          <header className="flex flex-col gap-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Event counts</h2>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">Distribution of browser events within the selected window.</p>
          </header>

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={`rum-counts-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : countsRows.length === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <MagnifyingGlassIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No events recorded</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Generate traffic or expand the window to populate counts.</p>
            </div>
          ) : (
            <>
              <div className="hidden md:block">
                <div className="overflow-x-auto">
                  <Table.Table zebra hover>
                    <Table.THead>
                      <Table.TR>
                        <Table.TH>Event</Table.TH>
                        <Table.TH>Count</Table.TH>
                      </Table.TR>
                    </Table.THead>
                    <Table.TBody>
                      {countsRows.map((row, index) => (
                        <Table.TR
                          key={`${row.event}-${index}`}
                          data-testid={`observability-rum-count-row-${(countsPage - 1) * countsPageSize + index}`}
                          data-analytics="observability:rum:count-row"
                        >
                          <Table.TD>{row.event}</Table.TD>
                          <Table.TD>{formatNumber(row.count)}</Table.TD>
                        </Table.TR>
                      ))}
                    </Table.TBody>
                  </Table.Table>
                </div>
              </div>

              <div className="space-y-3 md:hidden">
                {countsRows.map((row, index) => (
                  <Surface
                    key={`${row.event}-${index}`}
                    variant="soft"
                    className="rounded-3xl p-5"
                    data-testid={`observability-rum-count-card-${(countsPage - 1) * countsPageSize + index}`}
                  >
                    <div className="text-sm font-semibold text-gray-900 dark:text-white">{row.event}</div>
                    <div className="mt-2 text-xs text-gray-600 dark:text-dark-200/80">Count: {formatNumber(row.count)}</div>
                  </Surface>
                ))}
              </div>

              <TablePagination
                page={countsPage}
                pageSize={countsPageSize}
                currentCount={countsRows.length}
                totalItems={countsTotal}
                hasNext={countsHasNext}
                onPageChange={setCountsPage}
                onPageSizeChange={(value) => {
                  setCountsPageSize(value);
                  setCountsPage(1);
                }}
                pageSizeOptions={[10, 20, 50, 100]}
                data-testid="observability-rum-counts-pagination"
              />
            </>
          )}
        </Surface>

        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-rum-events"
          data-analytics="observability:rum:events"
        >
          <header className="flex flex-col gap-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent events</h2>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">Raw RUM payloads for debugging client-side behaviour.</p>
          </header>

          {eventsError ? (
            <div className="rounded-3xl border border-rose-200/70 bg-rose-50/70 p-5 text-sm text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/20 dark:text-rose-200">
              {eventsError}
            </div>
          ) : eventsLoading && eventRows.length === 0 ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={`rum-events-skeleton-${index}`} className="h-16 w-full rounded-2xl" />
              ))}
            </div>
          ) : eventRows.length === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <MagnifyingGlassIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No recent events</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Send browser traffic that satisfies the filters to see live events.</p>
            </div>
          ) : (
            <>
              <div className="hidden md:block">
                <div className="overflow-x-auto">
                  <Table.Table zebra hover>
                    <Table.THead>
                      <Table.TR>
                        <Table.TH>Timestamp</Table.TH>
                        <Table.TH>Event</Table.TH>
                        <Table.TH>URL</Table.TH>
                        <Table.TH>Data</Table.TH>
                      </Table.TR>
                    </Table.THead>
                    <Table.TBody>
                      {eventRows.map((event, index) => (
                        <Table.TR
                          key={`${event.ts}-${index}`}
                          data-testid={`observability-rum-event-row-${(eventPage - 1) * eventPageSize + index}`}
                          data-analytics="observability:rum:event-row"
                        >
                          <Table.TD className="font-mono text-xs">{formatTs(event.ts)}</Table.TD>
                          <Table.TD>{event.event}</Table.TD>
                          <Table.TD className="font-mono text-xs">{event.url}</Table.TD>
                          <Table.TD className="font-mono text-xs break-all">{JSON.stringify(event.data || {})}</Table.TD>
                        </Table.TR>
                      ))}
                    </Table.TBody>
                  </Table.Table>
                </div>
              </div>

              <div className="space-y-3 md:hidden">
                {eventRows.map((event, index) => (
                  <Surface
                    key={`${event.ts}-${index}`}
                    variant="soft"
                    className="rounded-3xl p-5"
                    data-testid={`observability-rum-event-card-${(eventPage - 1) * eventPageSize + index}`}
                  >
                    <div className="font-mono text-xs text-gray-500 dark:text-dark-200/80">{formatTs(event.ts)}</div>
                    <div className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">{event.event}</div>
                    <div className="font-mono text-xs text-gray-500 dark:text-dark-200/80">{event.url}</div>
                    <pre className="mt-2 max-h-32 overflow-auto rounded-2xl bg-gray-100 p-3 text-[11px] text-gray-700 dark:bg-dark-700 dark:text-dark-50">
                      {JSON.stringify(event.data || {}, null, 2)}
                    </pre>
                  </Surface>
                ))}
              </div>

              <TablePagination
                page={eventPage}
                pageSize={eventPageSize}
                currentCount={eventRows.length}
                totalItems={eventRows.length + (eventPage - 1) * eventPageSize + (eventsHasNext ? 1 : 0)}
                hasNext={eventsHasNext}
                onPageChange={setEventPage}
                onPageSizeChange={(value) => {
                  setEventPageSize(value);
                  setEventPage(1);
                }}
                data-testid="observability-rum-events-pagination"
              />
            </>
          )}
        </Surface>
      </div>
    </ObservabilityLayout>
  );
}

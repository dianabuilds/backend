import React from 'react';
import {
  ArrowTrendingUpIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
  SignalIcon,
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
import { ObservabilityHeroActions } from './ObservabilityHeroActions';
import { ObservabilitySummaryMetrics } from './ObservabilitySummaryMetrics';
import { fetchHttpSummary } from '@shared/api/observability';
import { useTelemetryQuery } from '../hooks/useTelemetryQuery';
import { formatLatency, formatNumber, formatPercent } from '../utils/format';
import { HttpPathStats, HttpSummary } from '@shared/types/observability';
import type { PageHeroMetric } from '@ui/patterns/PageHero';

type SummarySnapshot = {
  totalEndpoints: number;
  totalRequests: number;
  averageLatency: number;
  averageErrorRatio: number;
};

type ExtremesSnapshot = {
  slowest: HttpPathStats | null;
  highestError: HttpPathStats | null;
  mostRequested: HttpPathStats | null;
};

const API_POLL_INTERVAL_MS = 30_000;

function computeSummary(rows: HttpPathStats[]): SummarySnapshot {
  if (!rows.length) {
    return { totalEndpoints: 0, totalRequests: 0, averageLatency: 0, averageErrorRatio: 0 };
  }
  const totalRequests = rows.reduce((acc, row) => acc + (row.requests_total || 0), 0);
  const averageLatency = rows.reduce((acc, row) => acc + (row.avg_duration_ms || 0), 0) / rows.length;
  const averageErrorRatio = rows.reduce((acc, row) => acc + (row.error5xx_ratio || 0), 0) / rows.length;
  return { totalEndpoints: rows.length, totalRequests, averageLatency, averageErrorRatio };
}

function computeExtremes(rows: HttpPathStats[]): ExtremesSnapshot {
  if (!rows.length) {
    return { slowest: null, highestError: null, mostRequested: null };
  }
  return rows.reduce<ExtremesSnapshot>(
    (acc, row) => {
      if (!acc.slowest || (row.avg_duration_ms || 0) > (acc.slowest.avg_duration_ms || 0)) {
        acc.slowest = row;
      }
      if (!acc.highestError || (row.error5xx_ratio || 0) > (acc.highestError.error5xx_ratio || 0)) {
        acc.highestError = row;
      }
      if (!acc.mostRequested || (row.requests_total || 0) > (acc.mostRequested.requests_total || 0)) {
        acc.mostRequested = row;
      }
      return acc;
    },
    { slowest: null, highestError: null, mostRequested: null },
  );
}

export function ObservabilityAPI(): React.ReactElement {
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(10);
  const [search, setSearch] = React.useState('');
  const [methodFilter, setMethodFilter] = React.useState('ALL');

  const { data, loading, error, refresh, lastUpdated } = useTelemetryQuery<HttpSummary>({
    fetcher: (signal) => fetchHttpSummary({ signal }),
    pollIntervalMs: API_POLL_INTERVAL_MS,
  });

  const rows = React.useMemo(() => data?.paths ?? [], [data]);
  const summary = React.useMemo(() => computeSummary(rows), [rows]);
  const extremes = React.useMemo(() => computeExtremes(rows), [rows]);
  const availableMethods = React.useMemo(() => {
    const set = new Set(rows.map((row) => row.method));
    return Array.from(set.values()).sort();
  }, [rows]);

  const trimmedSearch = search.trim().toLowerCase();

  const filteredRows = React.useMemo(() => {
    if (!rows.length) return [];
    return rows.filter((row) => {
      const matchesSearch = trimmedSearch
        ? `${row.method} ${row.path}`.toLowerCase().includes(trimmedSearch)
        : true;
      const matchesMethod = methodFilter === 'ALL' || row.method === methodFilter;
      return matchesSearch && matchesMethod;
    });
  }, [rows, trimmedSearch, methodFilter]);

  React.useEffect(() => {
    setPage(1);
  }, [trimmedSearch, methodFilter, rows.length]);

  const totalRows = filteredRows.length;
  const paginatedRows = React.useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, page, pageSize]);
  const hasNext = page * pageSize < totalRows;

  const slowestByLatency = React.useMemo(
    () =>
      filteredRows
        .slice()
        .sort((a, b) => (b.avg_duration_ms || 0) - (a.avg_duration_ms || 0))
        .slice(0, 12),
    [filteredRows],
  );

  const hasData = Boolean(data) && !loading && !error;
  const isLoading = loading || (!data && !error);

  const heroActions = React.useMemo(
    () => (
      <ObservabilityHeroActions
        lastUpdated={lastUpdated}
        onRefresh={() => {
          void refresh();
        }}
        refreshing={loading}
        refreshTestId="observability-api-refresh"
        cta={{
          to: '/observability/rum',
          label: 'Realtime RUM',
          icon: <ChartBarIcon className="size-4" aria-hidden="true" />,
          analyticsId: 'observability:cta:rum',
          testId: 'observability-header-cta',
        }}
      />
    ),
    [lastUpdated, loading, refresh],
  );

  const heroMetrics: PageHeroMetric[] | undefined = hasData
    ? [
        {
          id: 'api-endpoints',
          label: 'Tracked endpoints',
          value: formatNumber(summary.totalEndpoints),
          helper: `${formatNumber(summary.totalRequests)} requests`,
          icon: <ChartBarIcon className="size-4" aria-hidden="true" />,
        },
        {
          id: 'api-latency',
          label: 'Average latency',
          value: formatLatency(summary.averageLatency),
          helper: extremes.slowest ? `Peak ${formatLatency(extremes.slowest.avg_duration_ms)}` : 'Awaiting data',
          icon: <ArrowTrendingUpIcon className="size-4" aria-hidden="true" />,
          accent: 'warning',
        },
        {
          id: 'api-errors',
          label: 'Average 5xx ratio',
          value: formatPercent(summary.averageErrorRatio, { maximumFractionDigits: 2 }),
          helper: extremes.highestError
            ? `Max ${formatPercent(extremes.highestError.error5xx_ratio, { maximumFractionDigits: 2 })}`
            : 'Awaiting data',
          icon: <ShieldExclamationIcon className="size-4" aria-hidden="true" />,
          accent: 'danger',
        },]
    : undefined;

  if (error) {
    return (
      <ObservabilityLayout title="HTTP API telemetry" actions={heroActions}>
        <Surface
          variant="soft"
          className="border border-rose-200/60 bg-rose-50/60 text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/20 dark:text-rose-200"
          role="alert"
          data-testid="observability-api-error"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <ExclamationTriangleIcon className="mt-0.5 size-6 shrink-0" aria-hidden="true" />
              <div className="space-y-1">
                <h2 className="text-sm font-semibold">HTTP telemetry failed to load</h2>
                <p className="text-sm opacity-80">{error}</p>
              </div>
            </div>
            <Button onClick={() => refresh()} variant="outlined" color="error" data-testid="observability-api-retry">
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
          id: 'slowest',
          label: 'Slowest endpoint',
          value: extremes.slowest ? formatLatency(extremes.slowest.avg_duration_ms) : '—',
          description: extremes.slowest ? `${extremes.slowest.method} ${extremes.slowest.path}` : 'Awaiting traffic',
          tone: 'warning' as const,
        },
        {
          id: 'highest-error',
          label: 'Highest 5xx ratio',
          value: extremes.highestError
            ? formatPercent(extremes.highestError.error5xx_ratio, { maximumFractionDigits: 2 })
            : '—',
          description: extremes.highestError
            ? `${extremes.highestError.method} ${extremes.highestError.path}`
            : 'Awaiting traffic',
          tone: 'warning' as const,
        },
        {
          id: 'most-requests',
          label: 'Most requested',
          value: extremes.mostRequested ? formatNumber(extremes.mostRequested.requests_total) : '—',
          description: extremes.mostRequested
            ? `${extremes.mostRequested.method} ${extremes.mostRequested.path}`
            : 'Awaiting traffic',
          tone: 'secondary' as const,
        },
      ]
    : [];

  return (
    <ObservabilityLayout
      title="HTTP API telemetry"
      description="Latency, error ratio, and request volume for critical endpoints."
      actions={heroActions}
    >
      <ObservabilitySummaryMetrics metrics={heroMetrics} />
      <div className="grid gap-6 xl:grid-cols-12">
        <div className="xl:col-span-12" data-testid="observability-api-filters" data-analytics="observability:api:filters">
          <Surface variant="soft" className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="space-y-1">
                <h2 className="text-sm font-semibold text-gray-900 dark:text-white">Filter requests</h2>
                <p className="text-xs text-gray-500 dark:text-dark-200/70">Narrow the dataset before comparing latency and reliability.</p>
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-[minmax(0,220px)_minmax(0,1fr)] md:items-end">
              <Select
                label="HTTP method"
                value={methodFilter}
                onChange={(event) => setMethodFilter(event.target.value)}
                data-testid="observability-api-method-filter"
                data-analytics="observability:api:filter-method"
              >
                <option value="ALL">All methods</option>
                {availableMethods.map((method) => (
                  <option key={method} value={method}>
                    {method}
                  </option>
                ))}
              </Select>
              <Input
                label="Search endpoints"
                placeholder="GET /v1/users"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                data-testid="observability-api-search"
                data-analytics="observability:api:filter-search"
              />
            </div>
          </Surface>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:col-span-12 xl:grid-cols-4" data-testid="observability-api-metrics">
          {hasData
            ? metricCards.map((metric) => (
                <div
                  key={metric.id}
                  data-testid={`observability-api-metric-${metric.id}`}
                  data-analytics={`observability:api:${metric.id}`}
                >
                  <MetricCard
                    label={metric.label}
                    value={metric.value}
                    description={metric.description}
                    tone={metric.tone}
                    icon={<SignalIcon className="size-5" aria-hidden="true" />}
                  />
                </div>
              ))
            : Array.from({ length: 4 }).map((_, index) => (
                <Surface key={`api-metric-skeleton-${index}`} variant="soft" className="rounded-3xl p-5">
                  <Skeleton className="h-3 w-24 rounded" />
                  <Skeleton className="mt-4 h-8 w-32 rounded" />
                  <Skeleton className="mt-3 h-3 w-36 rounded" />
                </Surface>
              ))}
        </div>

        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-api-latency-chart"
          data-analytics="observability:api:latency-chart"
        >
          <header className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-1">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Slowest endpoints by average latency</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Focus on the top offenders to triage timeouts and client regressions.</p>
            </div>
            <div className="text-xs text-gray-500 dark:text-dark-200/70">Top {slowestByLatency.length} endpoints from current filters</div>
          </header>

          {isLoading ? (
            <Skeleton className="h-72 w-full rounded-3xl" />
          ) : slowestByLatency.length === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <ChartBarIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No endpoints match the current filters</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Adjust filters or wait for fresh traffic to populate the histogram.</p>
            </div>
          ) : (
            <ApexChart
              type="bar"
              series={[
                {
                  name: 'Avg ms',
                  data: slowestByLatency.map((row) => ({
                    x: `${row.method} ${row.path}`,
                    y: Math.round(row.avg_duration_ms || 0),
                  })),
                },
              ]}
              options={{
                xaxis: { type: 'category', labels: { rotate: -45 } },
                dataLabels: { enabled: false },
              }}
              height={360}
            />
          )}
        </Surface>

        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-api-table"
          data-analytics="observability:api:table"
        >
          <header className="flex flex-col gap-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Endpoint snapshot</h2>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">
              Sorted by the current filters with pagination for deeper exploration. Click a row to inspect details.
            </p>
          </header>

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={`api-table-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : totalRows === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <ShieldExclamationIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No data available</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Try resetting filters or check back after more requests are processed.</p>
            </div>
          ) : (
            <>
              <div className="hidden md:block">
                <div className="overflow-x-auto">
                  <Table.Table preset="analytics" zebra hover>
                    <Table.THead>
                      <Table.TR>
                        <Table.TH>Method</Table.TH>
                        <Table.TH>Path</Table.TH>
                        <Table.TH>Avg ms</Table.TH>
                        <Table.TH>5xx %</Table.TH>
                        <Table.TH>Requests</Table.TH>
                      </Table.TR>
                    </Table.THead>
                    <Table.TBody>
                      {paginatedRows.map((row, index) => (
                        <Table.TR
                          key={`${row.method}-${row.path}-${index}`}
                          data-testid={`observability-api-row-${(page - 1) * pageSize + index}`}
                          data-analytics="observability:api:table-row"
                          className="cursor-pointer transition hover:-translate-y-[1px]"
                        >
                          <Table.TD>{row.method}</Table.TD>
                          <Table.TD className="font-mono text-xs">{row.path}</Table.TD>
                          <Table.TD>{Math.round(row.avg_duration_ms || 0)}</Table.TD>
                          <Table.TD>{formatPercent(row.error5xx_ratio, { maximumFractionDigits: 2 })}</Table.TD>
                          <Table.TD>{formatNumber(row.requests_total)}</Table.TD>
                        </Table.TR>
                      ))}
                    </Table.TBody>
                  </Table.Table>
                </div>
              </div>

              <div className="space-y-3 md:hidden">
                {paginatedRows.map((row, index) => (
                  <Surface
                    key={`${row.method}-${row.path}-${index}`}
                    variant="soft"
                    className="rounded-3xl p-5"
                    data-testid={`observability-api-card-${(page - 1) * pageSize + index}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <Badge color="primary" variant="soft">{row.method}</Badge>
                      <span className="text-xs text-gray-500 dark:text-dark-200/70">
                        {formatPercent(row.error5xx_ratio, { maximumFractionDigits: 2 })} 5xx
                      </span>
                    </div>
                    <div className="mt-3 font-mono text-xs text-gray-800 dark:text-dark-50">{row.path}</div>
                    <dl className="mt-3 grid grid-cols-2 gap-3 text-xs text-gray-600 dark:text-dark-200/80">
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Avg ms</dt>
                        <dd>{Math.round(row.avg_duration_ms || 0)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Requests</dt>
                        <dd>{formatNumber(row.requests_total)}</dd>
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
                data-testid="observability-api-pagination"
              />
            </>
          )}
        </Surface>
      </div>
    </ObservabilityLayout>
  );
}

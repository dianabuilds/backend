import React from 'react';
import {
  BanknotesIcon,
  BoltIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ListBulletIcon,
  SparklesIcon,
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
import { ObservabilityHeroActions } from './ObservabilityHeroActions';
import { ObservabilitySummaryMetrics } from './ObservabilitySummaryMetrics';
import { fetchWorkerSummary } from '@shared/api/observability';
import { useTelemetryQuery } from '../hooks/useTelemetryQuery';
import { formatCurrency, formatLatency, formatNumber } from '../utils/format';
import { WorkersSummary } from '@shared/types/observability';
import type { PageHeroMetric } from '@ui/patterns/PageHero';

const WORKERS_POLL_INTERVAL_MS = 30_000;
export function ObservabilityWorkers(): React.ReactElement {
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(10);
  const [stageSearch, setStageSearch] = React.useState('');
  const { data, loading, error, refresh, lastUpdated } = useTelemetryQuery<WorkersSummary>({
    fetcher: (signal) => fetchWorkerSummary({ signal }),
    pollIntervalMs: WORKERS_POLL_INTERVAL_MS,
  });
  const stages = React.useMemo(() => data?.stages ?? {}, [data]);
  const stageRows = React.useMemo(
    () =>
      Object.entries(stages).map(([stage, value]) => ({
        stage,
        count: (value as any)?.count || 0,
        avg_ms: (value as any)?.avg_ms || 0,
      })),
    [stages],
  );
  const trimmedSearch = stageSearch.trim().toLowerCase();
  const filteredStageRows = React.useMemo(() => {
    if (!trimmedSearch) return stageRows;
    return stageRows.filter((row) => row.stage.toLowerCase().includes(trimmedSearch));
  }, [stageRows, trimmedSearch]);
  React.useEffect(() => {
    setPage(1);
  }, [trimmedSearch, stageRows.length]);
  const totalRows = filteredStageRows.length;
  const paginatedRows = React.useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredStageRows.slice(start, start + pageSize);
  }, [filteredStageRows, page, pageSize]);
  const hasNext = page * pageSize < totalRows;
  const jobs = data?.jobs ?? {};
  const started = jobs.started || 0;
  const completed = jobs.completed || 0;
  const failed = jobs.failed || 0;
  const pending = Math.max(started - completed - failed, 0);
  const promptTokens = data?.tokens?.prompt || 0;
  const completionTokens = data?.tokens?.completion || 0;
  const totalTokens = promptTokens + completionTokens;
  const costUsd = data?.cost_usd_total || 0;
  const avgJobDuration = data?.job_avg_ms || 0;
  const jobStatusSeries = [completed, failed, pending];
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
        refreshTestId="observability-workers-refresh"
      />
    ),
    [lastUpdated, loading, refresh],
  );

  const heroMetrics: PageHeroMetric[] | undefined = hasData
    ? [
        {
          id: 'workers-started',
          label: 'Jobs started',
          value: formatNumber(started),
          helper: `${formatNumber(completed)} completed`,
          icon: <BoltIcon className="size-4" aria-hidden="true" />,
          accent: 'positive',
        },
        {
          id: 'workers-failed',
          label: 'Failures recorded',
          value: formatNumber(failed),
          helper: `${formatNumber(pending)} pending`,
          icon: <ExclamationTriangleIcon className="size-4" aria-hidden="true" />,
          accent: 'danger',
        },
        {
          id: 'workers-duration',
          label: 'Average duration',
          value: formatLatency(avgJobDuration),
        helper: `${formatCurrency(costUsd, 'USD')} spend`,
          icon: <ClockIcon className="size-4" aria-hidden="true" />,
          accent: 'warning',
        },
      ]
    : undefined;
  if (error) {
    return (
      <ObservabilityLayout title="Worker telemetry" actions={heroActions}>
        <Surface
          variant="soft"
          className="border border-rose-200/60 bg-rose-50/60 text-rose-700 dark:border-rose-900/40 dark:bg-rose-900/20 dark:text-rose-200"
          role="alert"
          data-testid="observability-workers-error"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3">
              <ExclamationTriangleIcon className="mt-0.5 size-6 shrink-0" aria-hidden="true" />
              <div className="space-y-1">
                <h2 className="text-sm font-semibold">Worker telemetry failed to load</h2>
                <p className="text-sm opacity-80">{error}</p>
              </div>
            </div>
            <Button onClick={() => refresh()} variant="outlined" color="error" data-testid="observability-workers-retry">
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
          id: 'tokens',
          label: 'Tokens consumed',
          value: formatNumber(totalTokens),
          description: `${formatNumber(promptTokens)} prompt ? ${formatNumber(completionTokens)} completion`,
          icon: <SparklesIcon className="size-5" aria-hidden="true" />,
          tone: 'success' as const,
        },
        {
          id: 'spend',
          label: 'Spend (USD)',
          value: formatCurrency(costUsd, 'USD'),
          description: 'Cumulative worker cost',
          icon: <BanknotesIcon className="size-5" aria-hidden="true" />,
          tone: 'secondary' as const,
        },
        {
          id: 'throughput',
          label: 'Throughput',
          value: `${formatNumber(completed)} completed`,
          description: `${formatNumber(started)} started total`,
          icon: <BoltIcon className="size-5" aria-hidden="true" />,
          tone: 'primary' as const,
        },
        {
          id: 'queue',
          label: 'Queue backlog',
          value: formatNumber(pending),
          description: `${formatNumber(failed)} failures observed`,
          icon: <ListBulletIcon className="size-5" aria-hidden="true" />,
          tone: 'warning' as const,
        },
      ]
    : [];
  return (
    <ObservabilityLayout
      title="Worker telemetry"
      description="Queue throughput, failure ratio, and stage timings for async jobs."
      actions={heroActions}
    >
      <ObservabilitySummaryMetrics metrics={heroMetrics} />
      <div className="grid gap-6 xl:grid-cols-12">
        <div className="xl:col-span-12" data-testid="observability-workers-filters" data-analytics="observability:workers:filters">
          <Surface variant="soft" className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="space-y-1">
                <h2 className="text-sm font-semibold text-gray-900 dark:text-white">Filter stages</h2>
                <p className="text-xs text-gray-500 dark:text-dark-200/70">Search by stage name to focus on specific pipelines.</p>
              </div>
              <Badge color="neutral" variant="soft" className="flex items-center gap-1 text-[11px]">
                <ListBulletIcon className="size-3" aria-hidden="true" />
                {filteredStageRows.length} of {stageRows.length} stages
              </Badge>
            </div>
            <Input
              label="Search stage"
              placeholder="ingest, moderation, publish"
              value={stageSearch}
              onChange={(event) => setStageSearch(event.target.value)}
              data-testid="observability-workers-stage-search"
              data-analytics="observability:workers:filter-stage"
            />
          </Surface>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:col-span-12 xl:grid-cols-4" data-testid="observability-workers-metrics">
          {hasData
            ? metricCards.map((metric) => (
                <div
                  key={metric.id}
                  data-testid={`observability-workers-metric-${metric.id}`}
                  data-analytics={`observability:workers:${metric.id}`}
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
                <Surface key={`workers-metric-skeleton-${index}`} variant="soft" className="rounded-3xl p-5">
                  <Skeleton className="h-3 w-24 rounded" />
                  <Skeleton className="mt-4 h-8 w-32 rounded" />
                  <Skeleton className="mt-3 h-3 w-36 rounded" />
                </Surface>
              ))}
        </div>
        <div className="grid gap-6 xl:col-span-12 xl:grid-cols-[1.2fr_1fr]">
          <Surface
            variant="frosted"
            className="space-y-5"
            data-testid="observability-workers-status"
            data-analytics="observability:workers:status-chart"
          >
            <header className="space-y-1">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Job status mix</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Completed vs failed vs pending jobs for the current window.</p>
            </header>
            {isLoading ? (
              <Skeleton className="h-64 w-full rounded-3xl" />
            ) : jobStatusSeries.every((value) => value === 0) ? (
              <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
                <SparklesIcon className="size-10 text-primary-400" aria-hidden="true" />
                <h3 className="text-base font-semibold">No job executions yet</h3>
                <p className="text-sm text-gray-600 dark:text-dark-200/80">Workers have not processed jobs in the selected window.</p>
              </div>
            ) : (
              <ApexChart
                type="donut"
                series={jobStatusSeries}
                options={{ labels: ['Completed', 'Failed', 'Pending'], legend: { position: 'bottom' } }}
                height={320}
              />
            )}
          </Surface>
          <Surface
            variant="frosted"
            className="space-y-5"
            data-testid="observability-workers-duration"
            data-analytics="observability:workers:duration-chart"
          >
            <header className="space-y-1">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Stage average duration</h2>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Compare stage execution time to identify bottlenecks.</p>
            </header>
            {isLoading ? (
              <Skeleton className="h-64 w-full rounded-3xl" />
            ) : filteredStageRows.length === 0 ? (
              <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
                <ClockIcon className="size-10 text-primary-400" aria-hidden="true" />
                <h3 className="text-base font-semibold">No stage data</h3>
                <p className="text-sm text-gray-600 dark:text-dark-200/80">Check back when workers log stage timings for this window.</p>
              </div>
            ) : (
              <ApexChart
                type="bar"
                series={[
                  {
                    name: 'Avg ms',
                    data: filteredStageRows.map((row) => ({ x: row.stage, y: Math.round(row.avg_ms || 0) })),
                  },
                ]}
                options={{ xaxis: { type: 'category', labels: { rotate: -45 } }, dataLabels: { enabled: false } }}
                height={320}
              />
            )}
          </Surface>
        </div>
        <Surface
          variant="frosted"
          className="space-y-5 xl:col-span-12"
          data-testid="observability-workers-table"
          data-analytics="observability:workers:table"
        >
          <header className="flex flex-col gap-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Stages table</h2>
            <p className="text-sm text-gray-600 dark:text-dark-200/80">View stage execution counts and average duration with responsive cards on mobile.</p>
          </header>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 6 }).map((_, index) => (
                <Skeleton key={`workers-table-skeleton-${index}`} className="h-12 w-full rounded-2xl" />
              ))}
            </div>
          ) : totalRows === 0 ? (
            <div className="flex flex-col items-center gap-3 rounded-3xl border border-dashed border-gray-200/80 bg-white/70 p-10 text-center dark:border-dark-600/60 dark:bg-dark-800/40">
              <ListBulletIcon className="size-10 text-primary-400" aria-hidden="true" />
              <h3 className="text-base font-semibold">No stages match the search</h3>
              <p className="text-sm text-gray-600 dark:text-dark-200/80">Reset the filter or wait for workers to emit more telemetry.</p>
            </div>
          ) : (
            <>
              <div className="hidden md:block">
                <div className="overflow-x-auto">
                  <Table.Table preset="analytics" zebra hover>
                    <Table.THead>
                      <Table.TR>
                        <Table.TH>Stage</Table.TH>
                        <Table.TH>Executions</Table.TH>
                        <Table.TH>Avg ms</Table.TH>
                      </Table.TR>
                    </Table.THead>
                    <Table.TBody>
                      {paginatedRows.map((row, index) => (
                        <Table.TR
                          key={`${row.stage}-${index}`}
                          data-testid={`observability-workers-row-${(page - 1) * pageSize + index}`}
                          data-analytics="observability:workers:table-row"
                          className="cursor-pointer transition hover:-translate-y-[1px]"
                        >
                          <Table.TD>{row.stage}</Table.TD>
                          <Table.TD>{formatNumber(row.count)}</Table.TD>
                          <Table.TD>{Math.round(row.avg_ms || 0)}</Table.TD>
                        </Table.TR>
                      ))}
                    </Table.TBody>
                  </Table.Table>
                </div>
              </div>
              <div className="space-y-3 md:hidden">
                {paginatedRows.map((row, index) => (
                  <Surface
                    key={`${row.stage}-${index}`}
                    variant="soft"
                    className="rounded-3xl p-5"
                    data-testid={`observability-workers-card-${(page - 1) * pageSize + index}`}
                  >
                    <div className="text-sm font-semibold text-gray-900 dark:text-white">{row.stage}</div>
                    <dl className="mt-3 grid grid-cols-2 gap-3 text-xs text-gray-600 dark:text-dark-200/80">
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Executions</dt>
                        <dd>{formatNumber(row.count)}</dd>
                      </div>
                      <div>
                        <dt className="font-semibold text-gray-500 dark:text-dark-200/80">Avg ms</dt>
                        <dd>{Math.round(row.avg_ms || 0)}</dd>
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
                data-testid="observability-workers-pagination"
              />
            </>
          )}
        </Surface>
      </div>
    </ObservabilityLayout>
  );
}




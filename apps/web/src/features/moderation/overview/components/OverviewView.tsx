import React from 'react';
import { Link } from 'react-router-dom';
import { Card, Spinner, Button, LineChart, BarChart, PieChart, PageHero, Skeleton } from '@ui';
import { fetchModerationOverview } from '@shared/api/moderation';
import type { ModerationOverview, ModerationOverviewCard, ModerationOverviewChart } from '@shared/types/moderation';

function toTitleCase(value: string): string {
  return value
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(' ');
}

function formatNumber(value: unknown): string {
  if (value == null) return '0';
  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) {
    return String(value);
  }
  return numberValue.toLocaleString();
}

function formatRelativeTime(value?: string | null): string {
  if (!value) return '-';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  const diffMs = Date.now() - dt.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return dt.toLocaleDateString();
}

const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
const REFRESH_INTERVAL_MINUTES = Math.round(REFRESH_INTERVAL_MS / 60000);

function getFirstSeriesValue(series: unknown): number | null {
  if (!Array.isArray(series) || series.length === 0) {
    return null;
  }
  const first = series[0] as unknown;
  if (typeof first === 'number') {
    return Number.isFinite(first) ? first : null;
  }
  if (typeof first === 'object' && first !== null) {
    const candidate = (first as { value?: unknown }).value;
    if (candidate != null) {
      const numeric = Number(candidate);
      return Number.isFinite(numeric) ? numeric : null;
    }
    const data = (first as { data?: unknown }).data;
    if (Array.isArray(data) && data.length > 0) {
      const numeric = Number(data[0]);
      return Number.isFinite(numeric) ? numeric : null;
    }
  }
  return null;
}

function formatHours(value: number): string {
  if (!Number.isFinite(value)) {
    return '—';
  }
  if (value >= 10) {
    return `${Math.round(value)}h`;
  }
  if (value >= 1) {
    return `${value.toFixed(1)}h`;
  }
  if (value > 0) {
    return `${value.toFixed(2)}h`;
  }
  return '0h';
}

type HeroMetric = {
  id?: string;
  label: string;
  value: React.ReactNode;
  trend?: React.ReactNode;
  helper?: React.ReactNode;
  icon?: React.ReactNode;
  accent?: 'neutral' | 'positive' | 'warning' | 'danger';
};

function ChartRenderer({ chart }: { chart: ModerationOverviewChart }) {
  const { type = 'line', series, options, height } = chart;

  if (!Array.isArray(series) || series.length === 0) {
    return <div className="text-sm text-gray-500">No data available.</div>;
  }

  if (type === 'bar') {
    return <BarChart series={series} options={options} height={height} />;
  }

  if (type === 'pie') {
    return <PieChart series={series} options={options} height={height} />;
  }

  return <LineChart series={series} options={options} height={height} />;
}

function ActionCard({ card }: { card: ModerationOverviewCard }) {
  const actions = card.actions ?? [];
  return (
    <Card skin="shadow" className="flex h-full flex-col justify-between p-4">
      <div className="space-y-2">
        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">{card.title}</div>
        <div className="text-2xl font-semibold text-gray-900 dark:text-white">{card.value}</div>
        {card.description ? (
          <p className="text-sm text-gray-600 dark:text-dark-100/80">{card.description}</p>
        ) : null}
        {card.delta ? (
          <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">{card.delta}</div>
        ) : null}
      </div>
      {actions.length > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {actions.map((action, index) => {
            const key = `${card.id}-action-${index}`;
            if (action.to) {
              return (
                <Button key={key} as={Link} to={action.to} size="sm" variant="outlined">
                  {action.label}
                </Button>
              );
            }
            if (action.href) {
              return (
                <Button
                  key={key}
                  as="a"
                  href={action.href}
                  target="_blank"
                  rel="noreferrer"
                  size="sm"
                  variant="outlined"
                >
                  {action.label}
                </Button>
              );
            }
            return (
              <span key={key} className="text-xs text-gray-500">
                {action.label}
              </span>
            );
          })}
        </div>
      ) : null}
    </Card>
  );
}

export default function ModerationOverview() {
  const [data, setData] = React.useState<ModerationOverview | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchModerationOverview();
      setData(response);
      setLastUpdated(new Date().toISOString());
    } catch (err: any) {
      setError(String(err?.message || err || 'Failed to load moderation overview'));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void load();
  }, [load]);

  React.useEffect(() => {
    const intervalId = window.setInterval(() => {
      void load();
    }, REFRESH_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [load]);

  const queueEntries = React.useMemo(
    () => {
      const entries = Object.entries(data?.contentQueues ?? {}).map(
        ([key, value]) => [key, Number(value ?? 0)] as [string, number],
      );
      entries.sort((a, b) => b[1] - a[1]);
      return entries;
    },
    [data?.contentQueues],
  );

  const queueTotal = React.useMemo(
    () => queueEntries.reduce((acc, [, value]) => acc + value, 0),
    [queueEntries],
  );

  const chartConfigs = React.useMemo<ModerationOverviewChart[]>(
    () => (Array.isArray(data?.charts) ? data.charts : []),
    [data?.charts],
  );

  const avgResponseHours = React.useMemo(() => {
    const avgChart = chartConfigs.find((chart) => chart.id === 'avg-response-time');
    return avgChart ? getFirstSeriesValue(avgChart.series) : null;
  }, [chartConfigs]);

  const hasData = Boolean(data);
  const initialLoading = loading && !hasData;

  const escalatedComplaints =
    typeof data?.complaints?.escalated === 'number' ? data.complaints.escalated : null;

  const totalComplaints = React.useMemo(() => {
    if (!data?.complaints) {
      return null;
    }
    if (typeof data.complaints.total === 'number') {
      return data.complaints.total;
    }
    const entries = Object.entries(data.complaints);
    if (!entries.length) {
      return null;
    }
    return entries.reduce((acc, [, value]) => acc + Number(value ?? 0), 0);
  }, [data?.complaints]);

  const heroMetrics = React.useMemo<HeroMetric[]>(() => {
    const placeholder = <Skeleton aria-hidden className="h-6 w-16 rounded" />;
    const metrics: HeroMetric[] = [];

    const queueValue =
      initialLoading
        ? placeholder
        : hasData && queueEntries.length
        ? formatNumber(queueTotal)
        : hasData
        ? '0'
        : '—';

    const queueHelper = initialLoading
      ? 'Preparing data...'
      : queueEntries.length
      ? `Top queue: ${toTitleCase(queueEntries[0][0])}`
      : hasData
      ? 'All queues clear'
      : 'No data available';

    metrics.push({
      id: 'queues',
      label: 'Queues backlog',
      value: queueValue,
      helper: queueHelper,
    });

    const incidentsSource = escalatedComplaints ?? totalComplaints;
    const incidentsValue =
      initialLoading
        ? placeholder
        : incidentsSource != null
        ? formatNumber(incidentsSource)
        : hasData
        ? '0'
        : '—';

    const incidentsHelper = initialLoading
      ? 'Preparing data...'
      : escalatedComplaints != null
      ? 'Escalated cases in review'
      : totalComplaints != null
      ? 'New reports (24h)'
      : hasData
      ? 'No new incidents'
      : 'No data available';

    metrics.push({
      id: 'incidents',
      label: 'Incidents',
      value: incidentsValue,
      helper: incidentsHelper,
    });

    const slaMetric: HeroMetric = {
      id: 'sla',
      label: 'SLA',
      value: initialLoading
        ? placeholder
        : avgResponseHours != null
        ? formatHours(avgResponseHours)
        : '—',
      helper: initialLoading
        ? 'Preparing data...'
        : avgResponseHours != null
        ? 'Average response time (24h)'
        : hasData
        ? 'Awaiting SLA signal'
        : 'No data available',
    };

    if (!initialLoading && avgResponseHours != null) {
      if (avgResponseHours <= 4) {
        slaMetric.accent = 'positive';
      } else if (avgResponseHours <= 6) {
        slaMetric.accent = 'warning';
      } else {
        slaMetric.accent = 'danger';
      }
    }

    metrics.push(slaMetric);

    return metrics;
  }, [
    avgResponseHours,
    escalatedComplaints,
    hasData,
    initialLoading,
    queueEntries,
    queueTotal,
    totalComplaints,
  ]);
  const actionCards = React.useMemo<ModerationOverviewCard[]>(() => {
    const cards = Array.isArray(data?.cards) ? data.cards : [];
    const normalized = cards.map((card) => ({
      ...card,
      value: card.value ?? 'вЂ”',
      actions: card.actions ?? [],
    }));

    if (queueEntries.length > 0) {
      const [queueName, queueValue] = queueEntries[0];
      normalized.unshift({
        id: 'queue-priority',
        title: `${toTitleCase(queueName)} queue`,
        value: formatNumber(queueValue),
        description: 'Highest workload queue right now',
        actions: [
          {
            label: 'Review queue',
            to: `/nodes/library?moderation_status=${encodeURIComponent(queueName)}`,
          },
        ],
      });
    }

    return normalized;
  }, [data?.cards, queueEntries]);

  const refreshStatus = React.useMemo(() => {
    if (initialLoading) {
      return 'Loading moderation stats...';
    }
    if (loading) {
      return 'Refreshing...';
    }
    if (error) {
      return lastUpdated
        ? `Last refresh failed | Showing data from ${formatRelativeTime(lastUpdated)}`
        : 'Last refresh failed';
    }
    if (lastUpdated) {
      return `Auto refresh | Updated ${formatRelativeTime(lastUpdated)}`;
    }
    return `Auto refresh every ${REFRESH_INTERVAL_MINUTES} min`;
  }, [error, initialLoading, lastUpdated, loading]);

  const statusToneClass = error ? 'text-rose-200' : 'text-slate-200';
  const statusDotClass = error ? 'bg-rose-300' : 'bg-emerald-300';
  const statusPulseClass = loading ? 'animate-pulse' : '';
  const statusDotClasses = ['inline-flex h-2 w-2 rounded-full', statusDotClass, statusPulseClass]
    .filter((cls): cls is string => Boolean(cls))
    .join(' ');
  const lastUpdatedTitle = lastUpdated ? new Date(lastUpdated).toLocaleString() : undefined;

  const complaintEntries = React.useMemo(
    () => Object.entries(data?.complaints ?? {}).sort((a, b) => Number(b[1] ?? 0) - Number(a[1] ?? 0)),
    [data?.complaints],
  );

  const ticketEntries = React.useMemo(
    () => Object.entries(data?.tickets ?? {}).sort((a, b) => Number(b[1] ?? 0) - Number(a[1] ?? 0)),
    [data?.tickets],
  );

  const lastSanctions = Array.isArray(data?.lastSanctions) ? data?.lastSanctions ?? [] : [];

  const heroActions = React.useMemo(
    () => (
      <div className="flex flex-wrap items-center gap-3">
        <Button
          onClick={load}
          variant="ghost"
          color="neutral"
          size="sm"
          disabled={loading}
          type="button"
          data-analytics="moderation:hero"
        >
          {loading ? <Spinner size="sm" className="mr-2" /> : null}
          Refresh
        </Button>
        <div className={`flex items-center gap-2 text-xs ${statusToneClass}`} aria-live="polite">
          <span className={statusDotClasses} aria-hidden="true" />
          <span title={lastUpdatedTitle}>{refreshStatus}</span>
        </div>
      </div>
    ),
    [lastUpdatedTitle, load, loading, refreshStatus, statusDotClasses, statusToneClass],
  );

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="Trust & Safety"
        title="Moderation Overview"
        description="Monitor queues, incidents, and action items to keep the platform safe."
        metrics={heroMetrics}
        actions={heroActions}
        align="start"
        tone="light"
        variant="compact"
        className="bg-white/95 shadow-sm ring-1 ring-gray-200/80 dark:bg-dark-850/85 dark:ring-dark-600/60"
      />

      {error ? (
        <Card skin="shadow" className="border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {error}
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {actionCards.map((card) => (
          <ActionCard key={card.id} card={card} />
        ))}
        {actionCards.length === 0 && !loading ? (
          <Card skin="shadow" className="p-4 text-sm text-gray-500">
            No action items right now.
          </Card>
        ) : null}
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card skin="shadow" className="p-4">
          <h3 className="text-sm font-semibold text-gray-700">Content queues</h3>
          <div className="mt-3 space-y-3">
            {queueEntries.length > 0 ? (
              queueEntries.map(([key, value]) => (
                <div key={key} className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">{toTitleCase(key)}</span>
                  <span className="font-semibold text-gray-900 dark:text-white">{formatNumber(value)}</span>
                </div>
              ))
            ) : (
              <div className="text-sm text-gray-500">No queued content.</div>
            )}
          </div>
        </Card>

        <Card skin="shadow" className="p-4">
          <h3 className="text-sm font-semibold text-gray-700">New complaints</h3>
          <div className="mt-3 space-y-3">
            {complaintEntries.length > 0 ? (
              complaintEntries.map(([key, value]) => (
                <div key={key} className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">{toTitleCase(key)}</span>
                  <span className="font-medium text-gray-900 dark:text-white">{formatNumber(value)}</span>
                </div>
              ))
            ) : (
              <div className="text-sm text-gray-500">No new complaints.</div>
            )}
          </div>
        </Card>

        <Card skin="shadow" className="p-4">
          <h3 className="text-sm font-semibold text-gray-700">Tickets health</h3>
          <div className="mt-3 space-y-3">
            {ticketEntries.length > 0 ? (
              ticketEntries.map(([key, value]) => (
                <div key={key} className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">{toTitleCase(key)}</span>
                  <span className="font-medium text-gray-900 dark:text-white">{formatNumber(value)}</span>
                </div>
              ))
            ) : (
              <div className="text-sm text-gray-500">No active tickets.</div>
            )}
          </div>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card skin="shadow" className="xl:col-span-2 p-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-semibold text-gray-700">Operational trends</h3>
              <p className="mt-1 text-sm text-gray-500">
                Queue volume, escalations, and SLA performance from analytics feed.
              </p>
            </div>
            {loading ? <Spinner size="sm" /> : null}
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {chartConfigs.length > 0 ? (
              chartConfigs.map((chart) => (
                <div key={chart.id} className="space-y-2">
                  <div className="text-sm font-medium text-gray-700">{chart.title}</div>
                  {chart.description ? (
                    <div className="text-xs text-gray-500">{chart.description}</div>
                  ) : null}
                  <ChartRenderer chart={chart} />
                </div>
              ))
            ) : (
              <div className="rounded border border-dashed border-gray-200 p-4 text-sm text-gray-500">
                Analytics feed does not provide charts yet.
              </div>
            )}
          </div>
        </Card>

        <Card skin="shadow" className="p-4">
          <h3 className="text-sm font-semibold text-gray-700">Recent sanctions</h3>
          <div className="mt-3 space-y-3">
            {lastSanctions.length > 0 ? (
              lastSanctions.map((sanction) => (
                <div
                  key={sanction.id}
                  className="rounded-lg border border-gray-200 p-3 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-200"
                >
                  <div className="flex items-center justify-between text-sm font-semibold text-gray-800 dark:text-white">
                    <span className="uppercase tracking-wide">{toTitleCase(sanction.type)}</span>
                    <span className="text-xs font-medium text-gray-400">{formatRelativeTime(sanction.issued_at)}</span>
                  </div>
                  <div className="mt-1">
                    Status: <span className="font-medium text-gray-700 dark:text-dark-100">{toTitleCase(sanction.status)}</span>
                  </div>
                  {sanction.target_type ? (
                    <div className="mt-1 text-xs text-gray-500">
                      Target: {toTitleCase(sanction.target_type)}{sanction.target_id ? ` #${sanction.target_id}` : ''}
                    </div>
                  ) : null}
                  {sanction.reason ? (
                    <div className="mt-2 text-xs text-gray-500 line-clamp-3">{sanction.reason}</div>
                  ) : null}
                  {sanction.moderator ? (
                    <div className="mt-2 text-xs text-gray-400">by {sanction.moderator}</div>
                  ) : null}
                </div>
              ))
            ) : (
              <div className="text-sm text-gray-500">No recent sanctions.</div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}




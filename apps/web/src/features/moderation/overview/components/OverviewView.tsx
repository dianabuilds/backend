import React from 'react';
import clsx from 'clsx';
import { Link } from 'react-router-dom';
import { Badge, Button, Card, PageHero, Skeleton, Spinner, LineChart, BarChart, PieChart } from '@ui';
import { fetchModerationOverview } from '@shared/api/moderation';
import type { PageHeroMetric } from '@ui/patterns/PageHero';
import type {
  ModerationOverview,
  ModerationOverviewCard,
  ModerationOverviewChart,
  ModerationSanctionRecord,
} from '@shared/types/moderation';

type QueueEntry = [string, number];

const REFRESH_INTERVAL_MS = 5 * 60 * 1000;
const REFRESH_INTERVAL_MINUTES = Math.round(REFRESH_INTERVAL_MS / 60000);

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

function formatPercent(value: number): string {
  if (!Number.isFinite(value)) return '—';
  const clamped = Math.max(0, Math.min(1, value));
  return `${Math.round(clamped * 100)}%`;
}

type HighlightCard = {
  id: string;
  label: string;
  value: React.ReactNode;
  helper?: React.ReactNode;
  accent?: 'neutral' | 'positive' | 'warning' | 'danger';
  action?: { label: string; to?: string };
  loading?: boolean;
};

const HIGHLIGHT_ACCENT_CLASS: Record<Exclude<HighlightCard['accent'], undefined>, string> = {
  neutral: 'border-gray-200',
  positive: 'border-emerald-200',
  warning: 'border-amber-200',
  danger: 'border-rose-200',
};

function HighlightCardView({ card }: { card: HighlightCard }): React.ReactElement {
  const accentClass = card.accent ? HIGHLIGHT_ACCENT_CLASS[card.accent] : 'border-gray-200';
  return (
    <Card
      skin="shadow"
      className={clsx(
        'flex h-full flex-col justify-between rounded-2xl border bg-white/95 p-4 dark:border-dark-700/70 dark:bg-dark-900/90',
        accentClass
      )}
    >
      <div className="space-y-2">
        <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/80">
          {card.label}
        </div>
        <div className="text-2xl font-semibold text-gray-900 dark:text-white">
          {card.loading ? <Skeleton aria-hidden className="h-6 w-16 rounded" /> : card.value}
        </div>
        {card.helper ? (
          <p className="text-sm text-gray-600 dark:text-dark-200/80">{card.helper}</p>
        ) : null}
      </div>
      {card.action?.to ? (
        <Button as={Link} to={card.action.to} size="sm" variant="outlined" className="self-start">
          {card.action.label}
        </Button>
      ) : null}
    </Card>
  );
}

function ChartRenderer({ chart }: { chart: ModerationOverviewChart }): React.ReactElement {
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

function QueueHealthList({
  entries,
  loading,
}: {
  entries: QueueEntry[];
  loading: boolean;
}): React.ReactElement {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="flex items-center justify-between">
            <Skeleton aria-hidden className="h-4 w-32 rounded" />
            <Skeleton aria-hidden className="h-4 w-12 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (!entries.length) {
    return (
      <div className="rounded border border-dashed border-gray-200/80 p-4 text-sm text-gray-500 dark:border-dark-700/70 dark:text-dark-200/80">
        All queues are clear. Connect additional feeds to track backlog trends.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {entries.map(([key, value], index) => {
        const isPrimary = index === 0;
        return (
          <div key={key} className="flex items-center justify-between gap-3 rounded-lg border border-gray-100/70 p-3 dark:border-dark-700/70">
            <div className="flex items-center gap-2 text-sm font-medium text-gray-800 dark:text-dark-50">
              {isPrimary ? <Badge color="warning" variant="soft">Top queue</Badge> : null}
              <span>{toTitleCase(key)}</span>
            </div>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">{formatNumber(value)}</span>
          </div>
        );
      })}
    </div>
  );
}

function IncidentsList({
  complaints,
  tickets,
  loading,
}: {
  complaints: Array<[string, unknown]>;
  tickets: Array<[string, unknown]>;
  loading: boolean;
}): React.ReactElement {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="flex items-center justify-between">
            <Skeleton aria-hidden className="h-4 w-40 rounded" />
            <Skeleton aria-hidden className="h-4 w-10 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (!complaints.length && !tickets.length) {
    return (
      <div className="rounded border border-dashed border-gray-200/80 p-4 text-sm text-gray-500 dark:border-dark-700/70 dark:text-dark-200/80">
        No new complaints or tickets in the last 24 hours.
      </div>
    );
  }

  const renderEntries = (entries: Array<[string, unknown]>, title: string) => (
    <div className="space-y-2">
      <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/80">{title}</div>
      {entries.map(([key, value]) => (
        <div key={key} className="flex items-center justify-between rounded-lg border border-gray-100/70 bg-white/80 p-3 text-sm text-gray-600 dark:border-dark-700/70 dark:bg-dark-900/60 dark:text-dark-200/80">
          <span>{toTitleCase(key)}</span>
          <span className="font-semibold text-gray-900 dark:text-white">{formatNumber(value)}</span>
        </div>
      ))}
    </div>
  );

  return (
    <div className="space-y-4">
      {complaints.length ? renderEntries(complaints, 'Complaints (24h)') : null}
      {tickets.length ? renderEntries(tickets, 'Tickets') : null}
    </div>
  );
}

function SanctionsList({
  sanctions,
  loading,
}: {
  sanctions: ModerationSanctionRecord[];
  loading: boolean;
}): React.ReactElement {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <Card key={index} skin="bordered" className="space-y-2 p-3">
            <Skeleton aria-hidden className="h-4 w-32 rounded" />
            <Skeleton aria-hidden className="h-3 w-48 rounded" />
            <Skeleton aria-hidden className="h-3 w-24 rounded" />
          </Card>
        ))}
      </div>
    );
  }

  if (!sanctions.length) {
    return (
      <div className="rounded border border-dashed border-gray-200/80 p-4 text-sm text-gray-500 dark:border-dark-700/70 dark:text-dark-200/80">
        No recent sanctions. All clear.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {sanctions.map((sanction) => (
        <Card
          key={sanction.id}
          skin="bordered"
          className="space-y-2 rounded-2xl border-gray-200/80 p-3 dark:border-dark-700/70"
        >
          <div className="flex items-center justify-between text-sm font-semibold text-gray-800 dark:text-white">
            <span>{toTitleCase(sanction.type)}</span>
            <span className="text-xs font-medium text-gray-400">{formatRelativeTime(sanction.issued_at)}</span>
          </div>
          {sanction.reason ? (
            <div className="text-xs text-gray-500 dark:text-dark-200/80 line-clamp-3">{sanction.reason}</div>
          ) : null}
          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-dark-200/80">
            {sanction.status ? <Badge color="neutral" variant="soft">{toTitleCase(sanction.status)}</Badge> : null}
            {sanction.target_type ? (
              <span>
                Target: {toTitleCase(sanction.target_type)}
                {sanction.target_id ? ` #${sanction.target_id}` : ''}
              </span>
            ) : null}
            {sanction.moderator ? <span>By {sanction.moderator}</span> : null}
          </div>
        </Card>
      ))}
    </div>
  );
}

export default function ModerationOverview(): React.ReactElement {
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

  const queueEntries = React.useMemo<QueueEntry[]>(
    () => {
      const entries = Object.entries(data?.contentQueues ?? {}).map(
        ([key, value]) => [key, Number(value ?? 0)] as QueueEntry,
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

  const aiAutoShare = React.useMemo(() => {
    const aiChart = chartConfigs.find((chart) => chart.id === 'ai-decisions-share');
    const firstValue = aiChart ? getFirstSeriesValue(aiChart.series) : null;
    if (firstValue == null) {
      return null;
    }
    return Math.max(0, Math.min(1, firstValue));
  }, [chartConfigs]);

  const initialLoading = loading && !data;
  const hasData = Boolean(data);

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

  const heroMetrics = React.useMemo<PageHeroMetric[]>(() => {
    const placeholder = <Skeleton aria-hidden className="h-6 w-16 rounded" />;

    const queueHelper = initialLoading
      ? 'Preparing data...'
      : queueEntries.length
      ? `Top queue: ${toTitleCase(queueEntries[0][0])}`
      : hasData
      ? 'All queues clear'
      : 'No data available';

    const slaHelper = initialLoading
      ? 'Preparing data...'
      : avgResponseHours != null
      ? 'Average response time (24h)'
      : hasData
      ? 'Awaiting SLA signal'
      : 'No data available';

    const slaAccent: PageHeroMetric['accent'] =
      !initialLoading && avgResponseHours != null
        ? avgResponseHours <= 4
          ? 'positive'
          : avgResponseHours <= 6
          ? 'warning'
          : 'danger'
        : undefined;

    return [
      {
        id: 'queues',
        label: 'Queues backlog',
        value: initialLoading
          ? placeholder
          : hasData
          ? formatNumber(queueTotal)
          : '—',
        helper: queueHelper,
      },
      {
        id: 'sla',
        label: 'SLA avg response',
        value: initialLoading
          ? placeholder
          : avgResponseHours != null
          ? formatHours(avgResponseHours)
          : '—',
        helper: slaHelper,
        accent: slaAccent,
      },
    ];
  }, [avgResponseHours, hasData, initialLoading, queueEntries, queueTotal]);

  const secondaryHighlights = React.useMemo<HighlightCard[]>(() => {
    const placeholderValue = <Skeleton aria-hidden className="h-6 w-16 rounded" />;
    const incidentsSource = escalatedComplaints ?? totalComplaints;
    const incidentsHelper = initialLoading
      ? 'Preparing data...'
      : escalatedComplaints != null
      ? 'Escalated cases in review'
      : totalComplaints != null
      ? 'New reports (24h)'
      : hasData
      ? 'No new incidents'
      : 'No data available';

    const incidentsCard: HighlightCard = {
      id: 'incidents',
      label: 'Incidents (24h)',
      value: initialLoading
        ? placeholderValue
        : incidentsSource != null
        ? formatNumber(incidentsSource)
        : hasData
        ? '0'
        : '—',
      helper: incidentsHelper,
      accent: incidentsSource != null && incidentsSource > 0 ? 'warning' : 'neutral',
      action: { label: 'Review incidents', to: '/moderation/cases?statuses=open' },
      loading: initialLoading,
    };

    const aiAccent =
      !initialLoading && aiAutoShare != null
        ? aiAutoShare <= 0.35
          ? 'positive'
          : aiAutoShare <= 0.65
          ? 'warning'
          : 'danger'
        : 'neutral';

    const aiCard: HighlightCard = {
      id: 'ai-share',
      label: 'AI automation share',
      value: initialLoading ? placeholderValue : aiAutoShare != null ? formatPercent(aiAutoShare) : hasData ? '0%' : '—',
      helper: initialLoading
        ? 'Preparing data...'
        : aiAutoShare != null
        ? 'Share of automated moderation (24h)'
        : hasData
        ? 'No AI decisions logged'
        : 'No data available',
      accent: aiAccent,
      action: { label: 'Configure AI rules', to: '/moderation/ai-rules' },
      loading: initialLoading,
    };

    return [incidentsCard, aiCard];
  }, [aiAutoShare, escalatedComplaints, hasData, initialLoading, totalComplaints]);

  const complaintEntries = React.useMemo(
    () => Object.entries(data?.complaints ?? {}).sort((a, b) => Number(b[1] ?? 0) - Number(a[1] ?? 0)),
    [data?.complaints],
  );

  const ticketEntries = React.useMemo(
    () => Object.entries(data?.tickets ?? {}).sort((a, b) => Number(b[1] ?? 0) - Number(a[1] ?? 0)),
    [data?.tickets],
  );

  const lastSanctions = Array.isArray(data?.lastSanctions) ? data?.lastSanctions ?? [] : [];

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

  const heroActions = React.useMemo(
    () => (
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <Button
            onClick={() => void load()}
            variant="ghost"
            color="neutral"
            size="sm"
            disabled={loading}
            type="button"
            data-analytics="moderation:overview:refresh"
            className="flex items-center gap-2"
          >
            {loading ? <Spinner size="sm" /> : null}
            Refresh
          </Button>
          <Button as={Link} to="/operations/integrations?tab=moderation" size="sm" variant="outlined">
            Manage sources
          </Button>
        </div>
        <div className={clsx('flex items-center gap-2 text-xs', statusToneClass)} aria-live="polite">
          <span className={statusDotClasses} aria-hidden="true" />
          <span title={lastUpdatedTitle}>{refreshStatus}</span>
        </div>
      </div>
    ),
    [lastUpdatedTitle, load, loading, refreshStatus, statusDotClasses, statusToneClass],
  );

  const actionCards = React.useMemo<ModerationOverviewCard[]>(() => {
    const cards = Array.isArray(data?.cards) ? data.cards : [];
    return cards.map((card) => ({
      ...card,
      value: card.value ?? '—',
      actions: card.actions ?? [],
    }));
  }, [data?.cards]);

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="Trust & Safety"
        title="Moderation overview"
        description="Track queues, incidents, and automation health to keep the network safe."
        metrics={heroMetrics}
        actions={heroActions}
        align="start"
        variant="metrics"
        tone="light"
        className="ring-1 ring-primary-500/10 dark:ring-primary-400/15"
      />

      {error ? (
        <Card skin="shadow" className="border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200">
          {error}
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {secondaryHighlights.map((card) => (
          <HighlightCardView key={card.id} card={card} />
        ))}
        {actionCards.map((card) => (
          <Card key={card.id} skin="shadow" className="flex h-full flex-col justify-between rounded-2xl border border-gray-200 bg-white/95 p-4 dark:border-dark-700/70 dark:bg-dark-900/90">
            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/80">
                {card.title}
              </div>
              <div className="text-2xl font-semibold text-gray-900 dark:text-white">{card.value}</div>
              {card.description ? (
                <p className="text-sm text-gray-600 dark:text-dark-200/80">{card.description}</p>
              ) : null}
              {card.delta ? (
                <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">{card.delta}</div>
              ) : null}
            </div>
            {card.actions?.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {card.actions.map((action, index) => {
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
                    <span key={key} className="text-xs text-gray-500 dark:text-dark-200/80">
                      {action.label}
                    </span>
                  );
                })}
              </div>
            ) : null}
          </Card>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <Card skin="shadow" className="space-y-4 rounded-2xl border border-gray-200 bg-white/95 p-4 dark:border-dark-700/70 dark:bg-dark-900/90">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-100">Queues health</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-dark-200/80">
                Backlog by queue with the most loaded queue highlighted.
              </p>
            </div>
            <Button as={Link} to="/moderation/cases" size="sm" variant="ghost" color="neutral">
              View cases
            </Button>
          </div>
          <QueueHealthList entries={queueEntries} loading={initialLoading} />
        </Card>

        <Card skin="shadow" className="space-y-4 rounded-2xl border border-gray-200 bg-white/95 p-4 dark:border-dark-700/70 dark:bg-dark-900/90">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-100">Incidents</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-dark-200/80">
                New complaints and ticket activity over the last 24 hours.
              </p>
            </div>
            <Button as={Link} to="/moderation/cases?statuses=open" size="sm" variant="ghost" color="neutral">
              Open queue
            </Button>
          </div>
          <IncidentsList complaints={complaintEntries} tickets={ticketEntries} loading={initialLoading} />
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <Card skin="shadow" className="rounded-2xl border border-gray-200 bg-white/95 p-4 dark:border-dark-700/70 dark:bg-dark-900/90">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-100">Operational trends</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-dark-200/80">
                Queue volume, escalations, and SLA performance from analytics feed.
              </p>
            </div>
            {loading ? <Spinner size="sm" /> : null}
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            {initialLoading ? (
              Array.from({ length: 2 }).map((_, index) => (
                <Card key={index} skin="bordered" className="space-y-3 rounded-2xl border-gray-100/80 p-4 dark:border-dark-700/70">
                  <Skeleton aria-hidden className="h-4 w-24 rounded" />
                  <Skeleton aria-hidden className="h-3 w-40 rounded" />
                  <Skeleton aria-hidden className="h-32 w-full rounded" />
                </Card>
              ))
            ) : chartConfigs.length > 0 ? (
              chartConfigs.map((chart) => (
                <div key={chart.id} className="space-y-2 rounded-2xl border border-gray-100/80 bg-white/90 p-4 dark:border-dark-700/70 dark:bg-dark-900/70">
                  <div className="text-sm font-medium text-gray-700 dark:text-gray-100">{chart.title}</div>
                  {chart.description ? (
                    <div className="text-xs text-gray-500 dark:text-dark-200/80">{chart.description}</div>
                  ) : null}
                  <ChartRenderer chart={chart} />
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-gray-200/80 p-6 text-sm text-gray-500 dark:border-dark-700/70 dark:text-dark-200/80">
                Analytics feed does not provide charts yet. Connect telemetry or import historical data to populate this
                section.
              </div>
            )}
          </div>
        </Card>

        <Card skin="shadow" className="rounded-2xl border border-gray-200 bg-white/95 p-4 dark:border-dark-700/70 dark:bg-dark-900/90">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-100">Recent sanctions</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-dark-200/80">
                Latest enforcement actions with responsible moderator.
              </p>
            </div>
          </div>
          <SanctionsList sanctions={lastSanctions} loading={initialLoading} />
        </Card>
      </div>
    </div>
  );
}

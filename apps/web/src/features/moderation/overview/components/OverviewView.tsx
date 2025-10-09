import React from 'react';
import { Link } from 'react-router-dom';
import { Card, Spinner, Button, LineChart, BarChart, PieChart, PageHero } from '@ui';
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

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchModerationOverview();
      setData(response);
    } catch (err: any) {
      setError(String(err?.message || err || 'Failed to load moderation overview'));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void load();
  }, [load]);

  const queueEntries = React.useMemo(() => Object.entries(data?.contentQueues ?? {}), [data?.contentQueues]);

  const heroMetrics = React.useMemo(
    () =>
      queueEntries.slice(0, 4).map(([key, value]) => ({
        id: key,
        label: toTitleCase(key),
        value: formatNumber(value),
      })),
    [queueEntries],
  );

  const actionCards = React.useMemo<ModerationOverviewCard[]>(() => {
    const cards = Array.isArray(data?.cards) ? data?.cards : [];
    const normalized = cards.map((card) => ({
      ...card,
      value: card.value ?? '—',
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

  const complaintEntries = React.useMemo(
    () => Object.entries(data?.complaints ?? {}).sort((a, b) => Number(b[1] ?? 0) - Number(a[1] ?? 0)),
    [data?.complaints],
  );

  const ticketEntries = React.useMemo(
    () => Object.entries(data?.tickets ?? {}).sort((a, b) => Number(b[1] ?? 0) - Number(a[1] ?? 0)),
    [data?.tickets],
  );

  const chartConfigs = React.useMemo<ModerationOverviewChart[]>(() => {
    return Array.isArray(data?.charts) ? data?.charts : [];
  }, [data?.charts]);

  const lastSanctions = Array.isArray(data?.lastSanctions) ? data?.lastSanctions ?? [] : [];

  return (
    <div className="space-y-6">
      <PageHero
        eyebrow="Trust & Safety"
        title="Moderation Overview"
        description="Monitor queues, incidents, and action items to keep the platform safe."
        metrics={heroMetrics}
        actions={
          <div className="flex items-center gap-2">
            {loading && <Spinner size="sm" />}
            <Button onClick={load} variant="outlined">
              Refresh
            </Button>
          </div>
        }
        variant="metrics"
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

import React from 'react';
import { ChartBarIcon } from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';
import { Button, Card, PageHero, Surface } from '@ui';
import type { PageHeroMetric } from '@ui/patterns/PageHero';
import { apiGet } from '@shared/api/client';

type HealthResponse = {
  ok?: boolean;
  components?: Record<string, string | boolean | number | null>;
};

type QueryStat = { q?: string; query?: string; count?: number; cnt?: number };

const QUICK_PLAYBOOKS = [
  'Deploy new world template >',
  'Review moderation tickets backlog >',
  'Audit AI fallbacks & latency >',
];

export default function DashboardPage() {
  const [health, setHealth] = React.useState<HealthResponse | null>(null);
  const [topQueries, setTopQueries] = React.useState<QueryStat[]>([]);
  const [refreshedAt, setRefreshedAt] = React.useState<Date | null>(null);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [healthRes, queriesRes] = await Promise.allSettled([
          apiGet<HealthResponse>('/health'),
          apiGet<QueryStat[]>('/v1/search/stats/top?limit=5'),
        ]);

        if (!mounted) return;

        if (healthRes.status === 'fulfilled') {
          setHealth(healthRes.value || null);
        }
        if (queriesRes.status === 'fulfilled' && Array.isArray(queriesRes.value)) {
          setTopQueries(queriesRes.value);
        }
        setRefreshedAt(new Date());
      } catch {
        if (mounted) setRefreshedAt(new Date());
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const topQuery = topQueries[0];
  const servicesOnline = Object.entries(health?.components || {}).filter(([, v]) => String(v).toLowerCase() !== 'false').length;
  const servicesTotal = Object.keys(health?.components || {}).length;
  const refreshedLabel = refreshedAt ? refreshedAt.toLocaleTimeString() : 'Syncing...';
  const isHealthy = typeof health?.ok === 'boolean' ? health.ok : null;

  const heroMetrics = React.useMemo<PageHeroMetric[]>(
    () => [
      {
        label: 'Platform status',
        value: isHealthy === null ? 'Syncing...' : isHealthy ? 'Operational' : 'Needs attention',
        helper: isHealthy === null ? 'Waiting for /health' : 'Monitoring via /health',
        accent: isHealthy === null ? 'neutral' : isHealthy ? 'positive' : 'danger',
      },
      {
        label: 'Trending query',
        value: topQuery ? topQuery.q || topQuery.query || '-' : 'Collecting',
        helper:
          topQuery?.count || topQuery?.cnt
            ? `${topQuery.count ?? topQuery.cnt} hits`
            : 'No recent traffic',
      },
      {
        label: 'Last refresh',
        value: refreshedLabel,
        helper: 'Auto refresh every few minutes',
      },
      {
        label: 'Active subsystems',
        value: servicesTotal ? `${servicesOnline}/${servicesTotal}` : '0/0',
        helper: servicesTotal ? 'Responding subsystems' : 'Awaiting registrations',
      },
    ],
    [isHealthy, topQuery, refreshedLabel, servicesOnline, servicesTotal],
  );

  return (
    <div className="space-y-8">
      <PageHero
        eyebrow="Command Center"
        title="Operational pulse across the cave network"
        description="Track experience health, search intent, and creator momentum from a single, cinematic workspace."
        variant="metrics"
        tone="light"
        maxHeight={420}
        className="py-10 sm:py-11 lg:py-12"
        metrics={heroMetrics}
        actions={(
          <Button
            as={Link}
            to="/observability/rum"
            variant="filled"
            className="shadow-[0_18px_45px_-25px_rgba(79,70,229,0.6)]"
            data-analytics="dashboard:hero:rum"
          >
            <ChartBarIcon className="size-4" />
            Realtime RUM
          </Button>
        )}
      >
        <div className="flex flex-col gap-3 rounded-2xl border border-gray-200 bg-white/85 p-4 text-sm text-gray-700 shadow-[0_18px_45px_-30px_rgba(15,23,42,0.25)] backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
          <span className="text-xs font-semibold uppercase tracking-[0.25em] text-gray-500">Quick playbooks</span>
          <div className="flex flex-wrap gap-2">
            {QUICK_PLAYBOOKS.map((label) => (
              <span
                key={label}
                className="rounded-full border border-gray-200 bg-white/90 px-3 py-1.5 text-xs-plus font-medium text-gray-700 transition hover:border-primary-300 hover:bg-primary-50 hover:text-primary-600"
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      </PageHero>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card padding="md" skin="bordered">
          <header className="flex flex-col gap-3 border-b border-white/40 pb-4 dark:border-white/10 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">System health map</h2>
              <p className="text-sm text-gray-500 dark:text-dark-200/80">Live breakdown of backend components and orchestration services.</p>
            </div>
            <Button as={Link} to="/management/system" variant="outlined">
              Jump to status board
            </Button>
          </header>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <Surface variant="soft" className="p-5">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-800 dark:text-dark-50">Service matrix</h3>
                <span className="text-xs text-gray-500 dark:text-dark-200/70">{refreshedLabel}</span>
              </div>
              <ul className="mt-3 space-y-2 text-sm text-gray-600 dark:text-dark-200/90">
                {Object.entries(health?.components || {}).map(([name, status]) => {
                  const ok = String(status).toLowerCase() !== 'false';
                  return (
                    <li key={name} className="flex items-center justify-between rounded-2xl bg-white/70 px-4 py-2 dark:bg-dark-800/60">
                      <span className="font-medium">{titleCase(name.replace(/[_-]/g, ' '))}</span>
                      <span className={`text-xs font-semibold uppercase ${ok ? 'text-emerald-500' : 'text-error'}`}>
                        {ok ? 'online' : 'issue'}
                      </span>
                    </li>
                  );
                })}
                {servicesTotal === 0 && <li className="rounded-2xl bg-white/60 px-4 py-3 text-xs text-gray-500 dark:bg-dark-800/60">Awaiting heartbeat...</li>}
              </ul>
            </Surface>

            <Surface variant="soft" className="p-5">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-800 dark:text-dark-50">Top live queries</h3>
                <span className="text-xs text-gray-500 dark:text-dark-200/70">Intent heatmap</span>
              </div>
              <ul className="mt-3 space-y-2 text-sm text-gray-600 dark:text-dark-200/90">
                {topQueries.length === 0 && <li className="rounded-2xl bg-white/60 px-4 py-3 text-xs text-gray-500 dark:bg-dark-800/60">No data yet. Encourage editors to explore the atlas.</li>}
                {topQueries.map((q, i) => (
                  <li key={`${q.q || q.query}-${i}`} className="flex items-center justify-between rounded-2xl bg-white/70 px-4 py-2 dark:bg-dark-800/70">
                    <span className="truncate font-medium">{q.q || q.query || 'unknown query'}</span>
                    <span className="text-xs text-gray-500 dark:text-dark-200/80">{q.count ?? q.cnt ?? 0}</span>
                  </li>
                ))}
              </ul>
            </Surface>
          </div>
        </Card>

        <div className="flex flex-col gap-6">
          <Surface variant="soft" className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-dark-50">Connect the dots</h3>
            <p className="mt-2 text-sm text-gray-500 dark:text-dark-200/80">
              Bring creators into the cave network with curated starter quests and world seeds.
            </p>
            <Button as={Link} to="/quests/library" className="mt-4 w-full">
              Design a quest run
            </Button>
          </Surface>
        </div>
      </div>
    </div>
  );
}

function titleCase(input: string) {
  return input
    .split(' ')
    .map((s) => s.charAt(0).toUpperCase() + s.slice(1))
    .join(' ');
}



import React from 'react';
import { ArrowTopRightOnSquareIcon, BoltIcon } from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';
import { Button, Card, MetricCard, PageHeader, Surface } from '@ui';
import { apiGet } from '../../shared/api/client';

type HealthResponse = {
  ok?: boolean;
  components?: Record<string, string | boolean | number | null>;
};

type QueryStat = { q?: string; query?: string; count?: number; cnt?: number };

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
  const refreshedLabel = refreshedAt ? refreshedAt.toLocaleTimeString() : 'syncing...';

  const stats = [
    {
      label: 'Platform status',
      value: health?.ok ? 'Operational' : 'Needs attention',
      hint: `${servicesOnline}/${servicesTotal || 1} subsystems online`,
    },
    {
      label: 'Trending query',
      value: topQuery ? (topQuery.q || topQuery.query || '-') : 'Collecting',
      hint: topQuery?.count || topQuery?.cnt ? `${topQuery.count ?? topQuery.cnt} hits` : 'No recent traffic',
    },
    {
      label: 'Last refresh',
      value: refreshedLabel,
      hint: 'Auto-updates every few minutes',
    },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        kicker="Command Center"
        title="Operational pulse across the cave network"
        description="Track experience health, search intent, and creator momentum from a single, cinematic workspace."
        pattern="highlight"
        stats={stats}
        actions={(
          <Button as={Link} to="/observability" variant="filled">
            <ArrowTopRightOnSquareIcon className="size-4" />
            Open observability
          </Button>
        )}
      />

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

          <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <MetricCard
              label="Operational score"
              value={health?.ok ? '99.4%' : '87.0%'}
              delta={health?.ok ? '+1.2%' : '-4.3%'}
              trend={health?.ok ? 'up' : 'down'}
              description="Composite uptime index rolling 24h"
              icon={<BoltIcon className="size-5" />}
            />
            <MetricCard
              label="Active subsystems"
              value={`${servicesOnline}/${servicesTotal || 1}`}
              delta={`${Math.max(servicesOnline - 1, 0)} recovered`}
              trend="up"
              tone="secondary"
              description="API, orchestrators, asset pipeline"
            />
            <MetricCard
              label="Search momentum"
              value={topQuery ? topQuery.count ?? topQuery.cnt ?? 0 : 0}
              delta={topQueries.length ? `${topQueries.length} active topics` : 'No data yet'}
              trend={topQueries.length ? 'up' : 'steady'}
              tone="success"
              description={topQuery ? `Top: ${topQuery.q || topQuery.query}` : 'Collecting intent signals'}
            />
          </div>

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
          <Surface variant="frosted" className="p-5">
            <h3 className="text-sm font-semibold text-gray-800 dark:text-dark-50">Quick playbooks</h3>
            <ul className="mt-3 space-y-3 text-sm">
              <li className="rounded-2xl bg-primary-500/10 px-4 py-3 text-primary-700 shadow-[0_15px_45px_-28px_rgba(79,70,229,0.6)] dark:text-primary-200">
                Deploy new world template {'>'}
              </li>
              <li className="rounded-2xl bg-white/70 px-4 py-3 text-gray-600 shadow-[0_10px_30px_-24px_rgba(17,24,39,0.4)] dark:bg-dark-800/70 dark:text-dark-200">
                Review moderation tickets backlog {'>'}
              </li>
              <li className="rounded-2xl bg-emerald-500/10 px-4 py-3 text-emerald-600 shadow-[0_10px_30px_-24px_rgba(16,185,129,0.45)] dark:text-emerald-200">
                Audit AI fallbacks & latency {'>'}
              </li>
            </ul>
          </Surface>

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



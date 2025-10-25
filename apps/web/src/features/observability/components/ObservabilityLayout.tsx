import React from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Button, PageHero, Surface } from '@ui';
import { ChartBarIcon } from '@heroicons/react/24/outline';
import type { PageHeroMetric } from '@ui/patterns/PageHero';

type NavItem = {
  to: string;
  label: string;
  exact?: boolean;
  analytics: string;
};

const NAV_LINKS: NavItem[] = [
  { to: '/observability', label: 'Overview', exact: true, analytics: 'overview' },
  { to: '/observability/api', label: 'API', analytics: 'api' },
  { to: '/observability/llm', label: 'LLM', analytics: 'llm' },
  { to: '/observability/workers', label: 'Workers', analytics: 'workers' },
  { to: '/observability/transitions', label: 'Transitions', analytics: 'transitions' },
  { to: '/observability/events', label: 'Events', analytics: 'events' },
  { to: '/observability/rum', label: 'RUM', analytics: 'rum' },
];

const DEFAULT_TITLE = 'Telemetry and experience lab';
const DEFAULT_DESCRIPTION =
  'Telemetry snapshots across API, LLM, workers, events, transitions, and real-user signals.';

const BREADCRUMB_ROOT: Array<{ label: string; to?: string }> = [
  { label: 'Operations', to: '/dashboard' },
  { label: 'Observability', to: '/observability' },
];

type Props = {
  title?: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  metrics?: PageHeroMetric[];
  children: React.ReactNode;
};

export function ObservabilityLayout({
  title = DEFAULT_TITLE,
  description = DEFAULT_DESCRIPTION,
  actions,
  metrics,
  children,
}: Props) {
  const location = useLocation();
  const activePath = React.useMemo(() => {
    const cleaned = location.pathname.replace(/\/$/, '') || '/observability';
    return cleaned.startsWith('/observability') ? cleaned : '/observability';
  }, [location.pathname]);

  const activeNav = React.useMemo(
    () =>
      NAV_LINKS.find((link) => {
        const normalized = link.to.replace(/\/$/, '');
        if (link.exact) return activePath === normalized;
        return activePath.startsWith(normalized);
      }),
    [activePath],
  );

  const resolvedBreadcrumbs = React.useMemo(() => {
    const breadcrumbs = [...BREADCRUMB_ROOT];
    if (activeNav && activeNav.to !== '/observability') {
      breadcrumbs[breadcrumbs.length - 1] = { ...breadcrumbs[breadcrumbs.length - 1], to: '/observability' };
      breadcrumbs.push({ label: activeNav.label });
    } else {
      breadcrumbs[breadcrumbs.length - 1] = { label: 'Observability' };
    }
    return breadcrumbs;
  }, [activeNav]);

  const resolvedActions =
    actions ?? (
      <Button
        as={Link}
        to="/observability/rum"
        variant="filled"
        size="sm"
        className="rounded-full shadow-[0_16px_36px_-22px_rgba(79,70,229,0.55)]"
        data-testid="observability-header-cta"
        data-analytics="observability:cta:rum"
      >
        <ChartBarIcon className="size-4" aria-hidden="true" /> Realtime RUM
      </Button>
    );

  const resolvedMetrics = React.useMemo(() => (metrics ? metrics.slice(0, 3) : undefined), [metrics]);

  return (
    <div className="space-y-6 lg:space-y-8">
      <PageHero
        title={title}
        description={description}
        actions={resolvedActions}
        breadcrumbs={resolvedBreadcrumbs}
        eyebrow={activeNav?.label ?? 'Observability'}
        metrics={resolvedMetrics}
        variant="compact"
        align="start"
        tone="light"
        className="bg-white/95 shadow-sm ring-1 ring-gray-200/80 dark:bg-dark-850/85 dark:ring-dark-600/60"
      />

      <Surface variant="soft" inset className="px-4 py-3">
        <div className="custom-scrollbar -mx-1 overflow-x-auto px-1">
          <nav
            className="flex h-11 items-center gap-2"
            data-testid="observability-nav"
            data-analytics="observability:nav"
          >
            {NAV_LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.exact as any}
                data-testid={`observability-nav-${link.analytics}`}
                data-analytics={`observability:nav:${link.analytics}`}
                className={({ isActive }) =>
                  `rounded-full border px-4 py-2 text-xs-plus font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/60 ${
                    isActive
                      ? 'border-primary-500/60 bg-primary-600 text-white shadow-[0_14px_30px_-20px_rgba(79,70,229,0.7)]'
                      : 'border-white/70 bg-white/70 text-gray-600 shadow-[0_8px_24px_-20px_rgba(17,24,39,0.55)] hover:text-primary-600 dark:border-dark-600/60 dark:bg-dark-700/70 dark:text-dark-100'
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </Surface>

      <main className="space-y-6 lg:space-y-8">{children}</main>
    </div>
  );
}




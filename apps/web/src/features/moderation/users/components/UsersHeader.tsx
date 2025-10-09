import * as React from 'react';

import { Button, MetricCard, PageHeader, Surface } from '@ui';
import {
  ArrowPathIcon,
  ClipboardDocumentListIcon,
  ClockIcon,
  ShieldCheckIcon,
  ShieldExclamationIcon,
  UserPlusIcon,
  UsersIcon,
} from '@heroicons/react/24/outline';

type UsersHeaderMetrics = {
  total: number;
  active: number;
  sanctioned: number;
  highRisk: number;
  complaints: number;
};

type UsersHeaderProps = {
  metrics: UsersHeaderMetrics;
  lastRefreshLabel: string;
  onRefresh: () => void;
  onCreateCase?: () => void;
};

export function UsersHeader({ metrics, lastRefreshLabel, onRefresh, onCreateCase }: UsersHeaderProps): JSX.Element {
  const metricCards = React.useMemo(
    () => [
      {
        key: 'total',
        label: 'Users on page',
        value: metrics.total.toLocaleString('ru-RU'),
        description: 'Current filtered selection',
        icon: <UsersIcon className="size-5" aria-hidden="true" />,
        tone: 'primary' as const,
      },
      {
        key: 'active',
        label: 'Active users',
        value: metrics.active.toLocaleString('ru-RU'),
        description: 'Status: active',
        icon: <ShieldCheckIcon className="size-5" aria-hidden="true" />,
        tone: 'success' as const,
      },
      {
        key: 'sanctioned',
        label: 'Under sanctions',
        value: metrics.sanctioned.toLocaleString('ru-RU'),
        description: `${metrics.highRisk.toLocaleString('ru-RU')} high risk`,
        icon: <ShieldExclamationIcon className="size-5" aria-hidden="true" />,
        tone: 'warning' as const,
      },
      {
        key: 'complaints',
        label: 'Complaints',
        value: metrics.complaints.toLocaleString('ru-RU'),
        description: 'Across current page',
        icon: <ClipboardDocumentListIcon className="size-5" aria-hidden="true" />,
        tone: 'neutral' as const,
      },
    ],
    [metrics],
  );

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Moderation"
        title="Moderation - Users"
        description="Investigate member profiles, escalate sanctions, and keep the network healthy."
        breadcrumbs={[
          { label: 'Moderation', to: '/moderation' },
          { label: 'Users' },
        ]}
        actions={(
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outlined"
              size="sm"
              onClick={onRefresh}
              data-testid="moderation-users-refresh"
              data-analytics="moderation:users:refresh"
            >
              <ArrowPathIcon className="size-4" aria-hidden="true" />
              Refresh
            </Button>
            <Button
              size="sm"
              onClick={() => onCreateCase?.()}
              data-testid="moderation-users-create-case"
              data-analytics="moderation:users:create-case"
            >
              <UserPlusIcon className="size-4" aria-hidden="true" />
              Create case
            </Button>
          </div>
        )}
        pattern="subtle"
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-[repeat(4,minmax(0,1fr))_220px]" data-testid="moderation-users-hero-metrics">
        {metricCards.map((metric) => (
          <MetricCard
            key={metric.key}
            label={metric.label}
            value={metric.value}
            description={metric.description}
            icon={metric.icon}
            tone={metric.tone}
          />
        ))}
        <Surface
          variant="soft"
          className="flex flex-col justify-center rounded-3xl border border-white/40 bg-white/70 p-5 text-sm text-gray-600 shadow-[0_25px_45px_-30px_rgba(15,23,42,0.35)] dark:border-dark-600/40 dark:bg-dark-800/60 dark:text-dark-200"
        >
          <span className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Last refresh</span>
          <div className="mt-1 flex items-center gap-2 text-base font-semibold text-gray-900 dark:text-white">
            <ClockIcon className="size-5 text-primary-500" aria-hidden="true" />
            {lastRefreshLabel}
          </div>
          <span className="mt-1 text-xs text-gray-400 dark:text-dark-400">Auto refresh when filters change</span>
        </Surface>
      </div>
    </div>
  );
}

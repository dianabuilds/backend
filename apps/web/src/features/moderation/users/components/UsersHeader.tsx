import clsx from 'clsx';
import * as React from 'react';

import { Button, PageHero, Spinner } from '@ui';
import type { PageHeroMetric } from '@ui/patterns/PageHero';
import {
  ArrowPathIcon,
  ClipboardDocumentListIcon,
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
  loading?: boolean;
  hasError?: boolean;
  onRefresh: () => void;
  onCreateCase?: () => void;
};

export function UsersHeader({
  metrics,
  lastRefreshLabel,
  loading,
  hasError,
  onRefresh,
  onCreateCase,
}: UsersHeaderProps): JSX.Element {
  const heroMetrics = React.useMemo<PageHeroMetric[]>(
    () => [
      {
        id: 'high-risk-users',
        label: 'High risk',
        value: metrics.highRisk.toLocaleString(),
        helper: `${metrics.total.toLocaleString()} total`,
        icon: <ShieldExclamationIcon className="size-5" aria-hidden="true" />,
        accent: metrics.highRisk > 0 ? 'warning' : 'neutral',
      },
      {
        id: 'sanctioned-users',
        label: 'Under sanctions',
        value: metrics.sanctioned.toLocaleString(),
        helper: `${metrics.active.toLocaleString()} active`,
        icon: <ShieldCheckIcon className="size-5" aria-hidden="true" />,
        accent: metrics.sanctioned > 0 ? 'danger' : 'neutral',
      },
      {
        id: 'complaints',
        label: 'Complaints (page)',
        value: metrics.complaints.toLocaleString(),
        helper: 'Across current filters',
        icon: <ClipboardDocumentListIcon className="size-5" aria-hidden="true" />,
        accent: metrics.complaints > 0 ? 'warning' : 'neutral',
      },
      {
        id: 'active-users',
        label: 'Active',
        value: metrics.active.toLocaleString(),
        helper: 'Users on page',
        icon: <UsersIcon className="size-5" aria-hidden="true" />,
        accent: metrics.active > 0 ? 'positive' : 'neutral',
      },
    ],
    [metrics],
  );

  const statusToneClass = hasError ? 'text-rose-500 dark:text-rose-300' : 'text-gray-500 dark:text-dark-200/80';
  const statusDotClass = clsx(
    'inline-flex h-2 w-2 rounded-full',
    loading ? 'animate-pulse' : '',
    hasError ? 'bg-rose-400 dark:bg-rose-300' : 'bg-emerald-400 dark:bg-emerald-300',
  );
  const refreshLabel = loading ? 'Refreshing…' : hasError ? 'Last refresh failed' : lastRefreshLabel || 'Waiting for data';

  return (
    <PageHero
      variant="metrics"
      tone="light"
      eyebrow="Moderation"
      title="Moderation · Users"
      description="Investigate member profiles, escalate sanctions, and keep the network healthy."
      align="start"
      className="bg-white/95 shadow-sm ring-1 ring-primary-500/10 dark:bg-dark-850/85 dark:ring-primary-400/20"
      breadcrumbs={[
        { label: 'Moderation', to: '/moderation' },
        { label: 'Users' },
      ]}
      metrics={heroMetrics}
      actions={(
        <div className="flex flex-wrap items-center gap-3">
          <div className={clsx('flex items-center gap-2 text-xs', statusToneClass)}>
            <span className={statusDotClass} aria-hidden="true" />
            <span>{refreshLabel}</span>
          </div>
          <Button
            variant="ghost"
            color="neutral"
            size="sm"
            onClick={onRefresh}
            disabled={loading}
            data-testid="moderation-users-refresh"
            data-analytics="moderation:users:refresh"
          >
            {loading ? <Spinner size="sm" className="mr-1" /> : <ArrowPathIcon className="size-4" aria-hidden="true" />}
            Refresh
          </Button>
          <Button
            size="sm"
            className="rounded-full"
            onClick={() => onCreateCase?.()}
            data-testid="moderation-users-create-case"
            data-analytics="moderation:users:create-case"
          >
            <UserPlusIcon className="size-4" aria-hidden="true" />
            Create case
          </Button>
        </div>
      )}
    />
  );
}

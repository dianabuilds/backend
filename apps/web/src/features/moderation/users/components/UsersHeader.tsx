import * as React from 'react';

import { Button, PageHero } from '@ui';
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
  onRefresh: () => void;
  onCreateCase?: () => void;
};

export function UsersHeader({ metrics, lastRefreshLabel, onRefresh, onCreateCase }: UsersHeaderProps): JSX.Element {
  const heroMetrics = React.useMemo<PageHeroMetric[]>(
    () => [
      {
        id: 'total-users',
        label: 'Users on page',
        value: metrics.total.toLocaleString('ru-RU'),
        helper: 'Current filtered selection',
        trend: (
          <>
            <ShieldCheckIcon className="size-4" aria-hidden="true" />
            {`${metrics.active.toLocaleString('ru-RU')} active`}
          </>
        ),
        accent: 'positive',
        icon: <UsersIcon className="size-5" aria-hidden="true" />,
      },
      {
        id: 'sanctioned-users',
        label: 'Under sanctions',
        value: metrics.sanctioned.toLocaleString('ru-RU'),
        helper: `${metrics.highRisk.toLocaleString('ru-RU')} high risk`,
        icon: <ShieldExclamationIcon className="size-5" aria-hidden="true" />,
        accent: 'warning',
      },
      {
        id: 'complaints',
        label: 'Complaints',
        value: metrics.complaints.toLocaleString('ru-RU'),
        helper: 'Across current page',
        icon: <ClipboardDocumentListIcon className="size-5" aria-hidden="true" />,
        accent: 'neutral',
      },
    ],
    [metrics],
  );

  return (
    <PageHero
      variant="compact"
      tone="light"
      eyebrow="Moderation"
      title="Moderation - Users"
      description="Investigate member profiles, escalate sanctions, and keep the network healthy."
      align="start"
      className="bg-white/95 shadow-sm ring-1 ring-gray-200/80 dark:bg-dark-850/85 dark:ring-dark-600/60"
      breadcrumbs={[
        { label: 'Moderation', to: '/moderation' },
        { label: 'Users' },
      ]}
      actions={(
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs font-medium text-gray-500 dark:text-dark-200/80">{lastRefreshLabel}</span>
          <Button
            variant="ghost"
            color="neutral"
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
      metrics={heroMetrics}
      metricsTestId="moderation-users-hero-metrics"
    />
  );
}


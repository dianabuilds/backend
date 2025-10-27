import React from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { ArrowPathIcon } from '@heroicons/react/24/outline';
import { Button } from '@ui';
import { formatUpdated } from '../utils/format';

type CtaConfig = {
  to: string;
  label: React.ReactNode;
  icon?: React.ReactNode;
  analyticsId?: string;
  testId?: string;
  variant?: 'filled' | 'outlined' | 'ghost';
  size?: 'sm' | 'md';
  className?: string;
};

type ObservabilityHeroActionsProps = {
  lastUpdated: Date | null;
  onRefresh: () => void;
  refreshing?: boolean;
  cta?: CtaConfig | null;
  children?: React.ReactNode;
  refreshTestId?: string;
  refreshAnalyticsId?: string;
};

export function ObservabilityHeroActions({
  lastUpdated,
  onRefresh,
  refreshing = false,
  cta,
  children,
  refreshTestId,
  refreshAnalyticsId,
}: ObservabilityHeroActionsProps): React.ReactElement {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs font-medium text-gray-500 dark:text-dark-200/80">
        Updated {formatUpdated(lastUpdated)}
      </span>

      <Button
        type="button"
        size="sm"
        variant="ghost"
        color="neutral"
        onClick={() => {
          onRefresh();
        }}
        disabled={refreshing}
        data-testid={refreshTestId ?? 'observability-hero-refresh'}
        data-analytics={refreshAnalyticsId}
      >
        <ArrowPathIcon className="size-4" aria-hidden="true" />
        Refresh
      </Button>

      {cta ? (
        <Button
          as={Link}
          to={cta.to}
          variant={cta.variant ?? 'filled'}
          size={cta.size ?? 'sm'}
          className={clsx(
            'flex items-center gap-1 rounded-full shadow-[0_16px_36px_-22px_rgba(79,70,229,0.55)]',
            cta.className,
          )}
          data-testid={cta.testId}
          data-analytics={cta.analyticsId}
        >
          {cta.icon}
          <span>{cta.label}</span>
        </Button>
      ) : null}

      {children}
    </div>
  );
}

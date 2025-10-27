import React from 'react';
import { Surface } from '@ui';
import clsx from 'clsx';
import type { PageHeroMetric } from '@ui/patterns/PageHero';

type ObservabilitySummaryMetricsProps = {
  metrics?: PageHeroMetric[] | null;
  testId?: string;
};

export function ObservabilitySummaryMetrics({ metrics, testId }: ObservabilitySummaryMetricsProps) {
  if (!metrics || metrics.length === 0) return null;

  return (
    <div
      className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3"
      data-testid={testId ?? 'observability-summary-metrics'}
    >
      {metrics.map((metric, index) => {
        const key = metric.id ?? `${metric.label}-${index}`;
        return (
          <Surface
            key={key}
            variant="soft"
            className="flex items-start gap-3 rounded-2xl border border-gray-200/70 bg-white/90 px-4 py-3 shadow-sm dark:border-dark-700/60 dark:bg-dark-800/90"
          >
            {metric.icon ? (
              <span className="mt-1 text-primary-500 dark:text-primary-300">{metric.icon}</span>
            ) : null}
            <div className="flex-1 space-y-1">
              <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/80">
                {metric.label}
              </div>
              <div className="text-xl font-semibold text-gray-900 dark:text-white">{metric.value}</div>
              {metric.helper ? (
                <div className="text-xs text-gray-500 dark:text-dark-200/80">{metric.helper}</div>
              ) : null}
              {metric.trend ? (
                <div
                  className={clsx(
                    'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide',
                    metric.accent === 'positive' && 'bg-emerald-100/70 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200',
                    metric.accent === 'warning' && 'bg-amber-100/70 text-amber-700 dark:bg-amber-500/20 dark:text-amber-200',
                    metric.accent === 'danger' && 'bg-rose-100/70 text-rose-700 dark:bg-rose-500/20 dark:text-rose-200',
                    (!metric.accent || metric.accent === 'neutral') && 'bg-slate-100/70 text-slate-600 dark:bg-slate-600/30 dark:text-slate-200',
                  )}
                >
                  {metric.trend}
                </div>
              ) : null}
            </div>
          </Surface>
        );
      })}
    </div>
  );
}

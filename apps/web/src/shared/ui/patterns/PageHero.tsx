import React from 'react';
import clsx from 'clsx';
import { Link } from 'react-router-dom';

export type PageHeroVariant = 'default' | 'metrics' | 'compact';
export type PageHeroTone = 'light' | 'dark';

export type PageHeroMetric = {
  id?: string;
  label: string;
  value: React.ReactNode;
  trend?: React.ReactNode;
  helper?: React.ReactNode;
  icon?: React.ReactNode;
  accent?: 'neutral' | 'positive' | 'warning' | 'danger';
};

export type PageHeroBreadcrumb = {
  label: string;
  to?: string;
};

type Align = 'start' | 'center';

export type PageHeroProps = {
  title: React.ReactNode;
  description?: React.ReactNode;
  eyebrow?: React.ReactNode;
  breadcrumbs?: PageHeroBreadcrumb[];
  actions?: React.ReactNode;
  filters?: React.ReactNode;
  metrics?: PageHeroMetric[] | React.ReactNode;
  metricsTestId?: string;
  children?: React.ReactNode;
  variant?: PageHeroVariant;
  tone?: PageHeroTone;
  align?: Align;
  maxHeight?: number;
  className?: string;
};

const VARIANT_CLASSNAMES: Record<PageHeroVariant, Record<PageHeroTone, string>> = {
  default: {
    light:
      'border-gray-200/80 bg-gradient-to-br from-slate-50/90 via-white to-indigo-50/70 text-gray-900 shadow-[0_20px_45px_-32px_rgba(79,70,229,0.45)] dark:border-dark-600/60 dark:from-dark-800/92 dark:via-dark-850 dark:to-dark-900/90 dark:text-white dark:shadow-[0_25px_60px_-45px_rgba(14,165,233,0.45)]',
    dark:
      'border-transparent bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 text-white shadow-[0_28px_50px_-35px_rgba(15,23,42,0.85)]',
  },
  metrics: {
    light:
      'border border-gray-200/70 bg-gradient-to-br from-white via-indigo-50/40 to-slate-100 text-gray-900 shadow-[0_24px_60px_-36px_rgba(79,70,229,0.45)] dark:border-dark-600/60 dark:from-dark-800/92 dark:via-dark-850 dark:to-dark-900/90 dark:text-white dark:shadow-[0_25px_60px_-45px_rgba(14,165,233,0.45)]',
    dark:
      'border-transparent bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 text-white shadow-[0_28px_50px_-35px_rgba(15,23,42,0.85)]',
  },
  compact: {
    light:
      'rounded-2xl border border-gray-200 bg-white/95 text-gray-900 shadow-sm dark:border-dark-700/70 dark:bg-dark-900/94 dark:text-white',
    dark:
      'rounded-2xl border border-white/10 bg-white/5 text-white shadow-[0_18px_40px_-30px_rgba(15,23,42,0.85)]',
  },
};

const VARIANT_PADDINGS: Record<PageHeroVariant, string> = {
  default: 'px-8 py-10 sm:px-10 lg:px-12 lg:py-12',
  metrics: 'px-8 py-12 sm:px-10 lg:px-14 lg:py-14',
  compact: 'px-6 py-6 sm:px-8 sm:py-7',
};

const DEFAULT_MAX_HEIGHT: Record<PageHeroVariant, number> = {
  default: 420,
  metrics: 460,
  compact: 320,
};

const METRIC_ACCENT: Record<NonNullable<PageHeroMetric['accent']>, string> = {
  neutral: 'bg-slate-100/60 text-slate-700 dark:bg-slate-600/30 dark:text-slate-200',
  positive: 'bg-emerald-100/60 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200',
  warning: 'bg-amber-100/60 text-amber-700 dark:bg-amber-500/20 dark:text-amber-200',
  danger: 'bg-rose-100/60 text-rose-700 dark:bg-rose-500/20 dark:text-rose-200',
};

function isMetricList(metrics?: PageHeroMetric[] | React.ReactNode): metrics is PageHeroMetric[] {
  return Array.isArray(metrics);
}

function Breadcrumbs({ items }: { items?: PageHeroBreadcrumb[] }) {
  if (!items || items.length === 0) return null;
  return (
    <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-gray-300/80">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        const key = `${item.label}-${index}`;
        return (
          <React.Fragment key={key}>
            {item.to && !isLast ? (
              <Link to={item.to} className="transition-colors hover:text-primary-600 dark:hover:text-primary-300">
                {item.label}
              </Link>
            ) : (
              <span className={clsx(isLast && 'font-medium text-gray-900 dark:text-white')}>{item.label}</span>
            )}
            {!isLast && <span className="opacity-40">/</span>}
          </React.Fragment>
        );
      })}
    </nav>
  );
}

function MetricsGrid({
  metrics,
  variant,
  tone,
  dataTestId,
}: {
  metrics: PageHeroMetric[];
  variant: PageHeroVariant;
  tone: PageHeroTone;
  dataTestId?: string;
}) {
  if (!metrics.length) return null;
  const gridCols = variant === 'compact' ? 'sm:grid-cols-2 lg:grid-cols-3' : 'sm:grid-cols-2 lg:grid-cols-4';
  const isLightTone = tone === 'light';
  return (
    <div
      className={clsx(
        'grid gap-3 sm:gap-4',
        gridCols,
        variant === 'metrics' && 'lg:grid-cols-4 xl:grid-cols-5'
      )}
      data-testid={dataTestId}
    >
      {metrics.map((metric, index) => {
        const key = metric.id || `${metric.label}-${index}`;
        return (
          <article
            key={key}
            className={clsx(
              'group relative overflow-hidden rounded-2xl border p-5 transition-transform hover:-translate-y-1',
              variant === 'metrics' &&
                (isLightTone
                  ? 'border-gray-200 bg-white/90 shadow-[0_18px_40px_-30px_rgba(15,23,42,0.25)] dark:border-white/10 dark:bg-white/10'
                  : 'border-white/10 bg-white/10 backdrop-blur-md dark:border-white/5'),
              variant === 'compact' &&
                'border-gray-200 bg-white/90 text-gray-900 shadow-sm dark:border-dark-700/60 dark:bg-dark-800/90 dark:text-gray-100',
              variant === 'default' &&
                'border-white/60 bg-white/80 shadow-[0_12px_40px_-32px_rgba(79,70,229,0.5)] dark:border-dark-700/40 dark:bg-dark-800/80'
            )}
          >
            <div className="flex items-start gap-3">
              {metric.icon ? (
                <span
                  className={clsx(
                    'mt-0.5',
                    isLightTone ? 'text-primary-500' : 'text-primary-300'
                  )}
                >
                  {metric.icon}
                </span>
              ) : null}
              <div className="flex-1 space-y-2">
                <div
                  className={clsx(
                    'text-xs font-semibold uppercase tracking-wide',
                    isLightTone ? 'text-gray-500 dark:text-dark-200/80' : 'text-slate-200/80'
                  )}
                >
                  {metric.label}
                </div>
                <div
                  className={clsx(
                    'text-2xl font-semibold lg:text-3xl',
                    isLightTone ? 'text-gray-900 dark:text-white' : 'text-white'
                  )}
                >
                  {metric.value}
                </div>
                {metric.trend ? (
                  <div
                    className={clsx(
                      'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
                      metric.accent ? METRIC_ACCENT[metric.accent] : 'bg-slate-100/70 text-slate-600 dark:bg-slate-600/30 dark:text-slate-200'
                    )}
                  >
                    {metric.trend}
                  </div>
                ) : null}
                {metric.helper ? (
                  <div
                    className={clsx(
                      'text-xs',
                      isLightTone ? 'text-gray-500 dark:text-dark-200/80' : 'text-slate-200/70'
                    )}
                  >
                    {metric.helper}
                  </div>
                ) : null}
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}

export function PageHero({
  title,
  description,
  eyebrow,
  breadcrumbs,
  actions,
  filters,
  metrics,
  metricsTestId,
  children,
  variant = 'default',
  tone,
  align = 'start',
  maxHeight,
  className = '',
}: PageHeroProps) {
  const resolvedMaxHeight = maxHeight ?? DEFAULT_MAX_HEIGHT[variant];
  const resolvedTone: PageHeroTone = tone ?? 'light';
  const isLightTone = resolvedTone === 'light';

  const containerClass = clsx(
    'relative isolate overflow-hidden rounded-3xl border transition-colors duration-500',
    VARIANT_CLASSNAMES[variant][resolvedTone],
    VARIANT_PADDINGS[variant],
    className
  );

  const headerAlignment = align === 'center' ? 'items-center text-center' : 'items-start text-left';
  const actionAlignment = align === 'center' ? 'justify-center' : 'justify-end';

  return (
    <section className={containerClass} style={{ maxHeight: resolvedMaxHeight }}>
      <div className="relative z-[1] flex flex-col gap-6 lg:gap-8">
        {(eyebrow || (breadcrumbs && breadcrumbs.length > 0)) && (
          <div className={clsx('flex flex-wrap items-center gap-3 text-sm', align === 'center' ? 'justify-center' : 'justify-start')}>
            {eyebrow ? (
              <span
                className={clsx(
                  'rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.25em] shadow-sm',
                  isLightTone
                    ? 'border border-primary-500/15 bg-white/90 text-primary-600 dark:border-white/10 dark:bg-white/10 dark:text-primary-200'
                    : 'border border-white/20 bg-white/10 text-primary-200'
                )}
              >
                {eyebrow}
              </span>
            ) : null}
            <Breadcrumbs items={breadcrumbs} />
          </div>
        )}

        <div className={clsx('flex flex-col gap-6 lg:flex-row lg:items-end', align === 'center' ? 'lg:justify-center' : 'lg:justify-between')}>
          <div className={clsx('flex-1 space-y-4', headerAlignment)}>
            <h1 className={clsx('text-balance font-semibold tracking-tight', variant === 'compact' ? 'text-2xl sm:text-3xl' : 'text-3xl sm:text-4xl lg:text-[2.75rem]')}>
              {title}
            </h1>
            {description ? (
              <div
                className={clsx(
                  'max-w-3xl text-base sm:text-lg',
                  variant === 'metrics'
                    ? isLightTone
                      ? 'text-gray-600 dark:text-gray-200/85'
                      : 'text-slate-200'
                    : 'text-gray-600 dark:text-gray-200/85',
                  align === 'center' && 'mx-auto'
                )}
              >
                {description}
              </div>
            ) : null}
          </div>
          {actions ? (
            <div className={clsx('flex flex-wrap items-center gap-3 lg:min-w-[220px]', actionAlignment)}>{actions}</div>
          ) : null}
        </div>

        {filters ? (
          <div
            className={clsx(
              'flex flex-wrap gap-3 rounded-2xl border p-5 text-sm shadow-sm',
              isLightTone ? 'border-gray-200 bg-white/90 dark:border-white/10 dark:bg-white/10' : 'border-white/40 bg-white/10 dark:border-white/10 dark:bg-white/5',
              align === 'center' ? 'justify-center' : 'justify-start'
            )}
          >
            {filters}
          </div>
        ) : null}

        {metrics ? (
          <div className="space-y-4">
            {isMetricList(metrics) ? (
              <MetricsGrid metrics={metrics} variant={variant} tone={resolvedTone} dataTestId={metricsTestId} />
            ) : (
              metrics
            )}
          </div>
        ) : null}

        {children ? <div className="space-y-4">{children}</div> : null}
      </div>

      <div
        className={clsx(
          'pointer-events-none absolute -left-24 top-10 h-60 w-60 rounded-full blur-3xl',
          isLightTone ? 'bg-primary-400/20 dark:bg-primary-400/20' : 'bg-primary-400/15 dark:bg-primary-400/20'
        )}
      />
      <div
        className={clsx(
          'pointer-events-none absolute -right-24 bottom-10 h-64 w-64 rounded-full blur-3xl',
          isLightTone ? 'bg-secondary/20 dark:bg-secondary/15' : 'bg-secondary/10 dark:bg-secondary/15'
        )}
      />
    </section>
  );
}

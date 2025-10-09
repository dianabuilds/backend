import React from 'react';
import { Link } from 'react-router-dom';

export type PageHeaderStat = {
  label: string;
  value: React.ReactNode;
  hint?: string;
  icon?: React.ReactNode;
};

type PageHeaderProps = {
  title: string;
  description?: React.ReactNode;
  kicker?: React.ReactNode;
  breadcrumbs?: Array<{ label: string; to?: string }>;
  actions?: React.ReactNode;
  stats?: PageHeaderStat[];
  pattern?: 'highlight' | 'radiant' | 'subtle';
  className?: string;
};

const patternMap: Record<Required<PageHeaderProps>['pattern'], string> = {
  highlight:
    'border-white/60 bg-gradient-to-br from-primary-600/12 via-primary-500/5 to-primary-950/10 dark:border-white/5 dark:from-primary-400/15 dark:via-primary-500/10 dark:to-dark-900/40',
  radiant:
    'border-transparent bg-white/70 shadow-[0_10px_40px_-25px_rgba(79,70,229,0.8)] dark:bg-dark-700/80 dark:shadow-[0_18px_50px_-30px_rgba(79,70,229,0.7)]',
  subtle:
    'border-gray-100 bg-gradient-to-br from-white/96 via-primary-50/24 to-indigo-50/30 shadow-[0_20px_45px_-30px_rgba(79,70,229,0.35)] dark:border-dark-600/60 dark:bg-dark-850/70',
};

export function PageHeader({
  title,
  description,
  kicker,
  breadcrumbs,
  actions,
  stats,
  pattern = 'highlight',
  className = '',
}: PageHeaderProps) {
  return (
    <section
      className={`relative isolate overflow-hidden rounded-[28px] border px-5 py-6 sm:px-7 sm:py-7 lg:px-10 lg:py-8 ${patternMap[pattern]} ${className}`}
    >
      <div className="relative z-[1] flex flex-col gap-8">
        {(breadcrumbs?.length || kicker) && (
          <div className="flex flex-wrap items-center gap-3 text-xs-plus text-gray-500 dark:text-dark-200/80">
            {kicker && <span className="rounded-full bg-white/80 px-3 py-1 font-semibold uppercase tracking-[0.3em] text-primary-600 shadow-sm dark:bg-dark-700/60 dark:text-primary-300">{kicker}</span>}
            {breadcrumbs?.length ? (
              <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1 text-xs text-gray-600 dark:text-dark-200/70">
                {breadcrumbs.map((crumb, index) => {
                  const isLast = index === (breadcrumbs?.length || 0) - 1;
                  return (
                    <React.Fragment key={`${crumb.label}-${index}`}>
                      {crumb.to && !isLast ? (
                        <Link to={crumb.to} className="transition-colors hover:text-primary-600 dark:hover:text-primary-300">
                          {crumb.label}
                        </Link>
                      ) : (
                        <span className={isLast ? 'font-medium text-gray-900 dark:text-white' : ''}>{crumb.label}</span>
                      )}
                      {!isLast && <span className="opacity-40">/</span>}
                    </React.Fragment>
                  );
                })}
              </nav>
            ) : null}
          </div>
        )}

        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-3xl space-y-4">
            <h1 className="text-balance text-xl font-semibold tracking-tight text-gray-900 dark:text-white sm:text-2xl">
              {title}
            </h1>
            {description ? (
              <div className="text-xs-plus text-gray-600 dark:text-dark-100/80 sm:text-sm">{description}</div>
            ) : null}
          </div>
          {actions ? <div className="flex flex-wrap items-center justify-end gap-3">{actions}</div> : null}
        </div>

        {stats?.length ? (
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 xl:max-w-lg xl:self-end">
            {stats.map((stat, index) => (
              <div
                key={index}
                className="rounded-xl border border-white/40 bg-white/85 px-3.5 py-2.5 shadow-sm backdrop-blur dark:border-white/10 dark:bg-dark-800/80"
              >
                <div className="flex items-center gap-3">
                  {stat.icon && <div className="mt-0.5 text-primary-500 dark:text-primary-300">{stat.icon}</div>}
                  <div className="space-y-1">
                    <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/70">{stat.label}</div>
                    <div className="text-lg font-semibold text-gray-900 dark:text-white">{stat.value}</div>
                    {stat.hint ? <div className="text-2xs text-gray-500 dark:text-dark-200/60">{stat.hint}</div> : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}

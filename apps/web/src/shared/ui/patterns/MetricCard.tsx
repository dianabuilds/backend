import React from 'react';

export type MetricTrend = 'up' | 'down' | 'steady';

export type MetricCardProps = {
  label: string;
  value: React.ReactNode;
  delta?: string;
  trend?: MetricTrend;
  trendLabel?: string;
  icon?: React.ReactNode;
  description?: React.ReactNode;
  tone?: 'primary' | 'secondary' | 'warning' | 'success' | 'neutral';
  className?: string;
};

const toneMap: Record<Required<MetricCardProps>['tone'], string> = {
  primary: 'from-primary-500/15 to-primary-600/5 text-primary-900 dark:text-primary-100',
  secondary: 'from-secondary/20 to-secondary/5 text-gray-900 dark:text-secondary-light',
  warning: 'from-amber-400/20 to-amber-500/5 text-amber-900 dark:text-amber-200',
  success: 'from-emerald-500/20 to-emerald-500/5 text-emerald-900 dark:text-emerald-200',
  neutral: 'from-slate-400/15 to-slate-200/5 text-gray-900 dark:text-gray-100',
};

const trendCopy: Record<MetricTrend, string> = {
  up: '^',
  down: 'Ў',
  steady: '-',
};

export function MetricCard({
  label,
  value,
  delta,
  trend,
  trendLabel,
  icon,
  description,
  tone = 'primary',
  className = '',
}: MetricCardProps) {
  return (
    <article
      className={`relative overflow-hidden rounded-2xl border border-white/40 bg-gradient-to-br ${toneMap[tone]} p-5 shadow-[0_10px_30px_-20px_rgba(79,70,229,0.7)] transition duration-300 hover:-translate-y-[2px] hover:shadow-[0_18px_40px_-24px_rgba(79,70,229,0.65)] dark:border-white/10 ${className}`}
    >
      <div className="flex items-start gap-4">
        {icon ? <div className="mt-1 text-lg">{icon}</div> : null}
        <div className="flex-1 space-y-1">
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-700/80 dark:text-dark-200/80">{label}</div>
          <div className="text-2xl font-semibold leading-tight text-gray-900 drop-shadow-sm dark:text-white">{value}</div>
          {description ? <p className="text-sm text-gray-600 dark:text-dark-100/70">{description}</p> : null}
          {!delta && trendLabel ? (
            <p className="text-xs font-medium uppercase tracking-wide text-gray-600/80 dark:text-dark-200/70">{trendLabel}</p>
          ) : null}
        </div>
        {delta ? (
          <div
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              trend === 'down'
                ? 'bg-error/15 text-error'
                : trend === 'steady'
                ? 'bg-gray-200/60 text-gray-700 dark:bg-dark-700/40 dark:text-gray-200'
                : 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300'
            }`}
          >
            <span>{trend ? `${trendCopy[trend]} ` : ''}{delta}</span>
            {trendLabel ? (
              <span className="mt-1 block text-[10px] font-medium uppercase tracking-wide opacity-80">{trendLabel}</span>
            ) : null}
          </div>
        ) : null}
      </div>
    </article>
  );
}

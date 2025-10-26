import React from 'react';
import { Card, Button, Select, Spinner, Badge } from '@ui';
import { AlertTriangle } from '@icons';
import { MetricCard, type MetricTrend } from '@ui/patterns/MetricCard';
import { formatNumber, formatPercent, formatDateTime } from '@shared/utils/format';
import type { SiteMetricsPeriod, SitePageMetricsResponse, SiteMetricValue, SiteMetricAlert } from '@shared/types/management';

const PERIOD_OPTIONS: Array<{ value: SiteMetricsPeriod; label: string }> = [
  { value: '1d', label: '24 часа' },
  { value: '7d', label: '7 дней' },
  { value: '30d', label: '30 дней' },
];

type MetricConfig = {
  label: string;
  tone: 'primary' | 'secondary' | 'warning' | 'success' | 'neutral';
  format: (metric: SiteMetricValue) => string;
  formatDelta?: (delta: number | null | undefined) => string | null;
};

const METRIC_CONFIG: Record<string, MetricConfig> = {
  views: {
    label: 'Просмотры',
    tone: 'primary',
    format: (metric) => formatNumber(metric.value, { defaultValue: '—', compact: true, maximumFractionDigits: 0 }),
  },
  unique_users: {
    label: 'Уникальные пользователи',
    tone: 'secondary',
    format: (metric) => formatNumber(metric.value, { defaultValue: '—', compact: true, maximumFractionDigits: 0 }),
  },
  cta_clicks: {
    label: 'Клики по CTA',
    tone: 'secondary',
    format: (metric) => formatNumber(metric.value, { defaultValue: '—', compact: true, maximumFractionDigits: 0 }),
  },
  ctr: {
    label: 'CTR',
    tone: 'primary',
    format: (metric) => formatPercent(metric.value, { defaultValue: '—', maximumFractionDigits: 2, isFraction: true }),
  },
  conversions: {
    label: 'Конверсии',
    tone: 'success',
    format: (metric) => formatNumber(metric.value, { defaultValue: '—', compact: true, maximumFractionDigits: 0 }),
  },
  conversion_rate: {
    label: 'Конверсия',
    tone: 'success',
    format: (metric) => formatPercent(metric.value, { defaultValue: '—', maximumFractionDigits: 2, isFraction: true }),
  },
  bounce_rate: {
    label: 'Bounce rate',
    tone: 'warning',
    format: (metric) => formatPercent(metric.value, { defaultValue: '—', maximumFractionDigits: 2, isFraction: true }),
  },
  mobile_share: {
    label: 'Мобильный трафик',
    tone: 'secondary',
    format: (metric) => formatPercent(metric.value, { defaultValue: '—', maximumFractionDigits: 1, isFraction: true }),
  },
  avg_time_on_page: {
    label: 'Среднее время, с',
    tone: 'neutral',
    format: (metric) => formatNumber(metric.value, { defaultValue: '—', maximumFractionDigits: 1 }),
  },
};

type SitePageMetricsPanelProps = {
  metrics: SitePageMetricsResponse | null;
  loading: boolean;
  error: string | null;
  period: SiteMetricsPeriod;
  onChangePeriod: (period: SiteMetricsPeriod) => void;
  onRefresh: () => void;
};

function pickTrend(delta?: number | null): MetricTrend | undefined {
  if (delta == null || Number.isNaN(delta)) {
    return undefined;
  }
  if (delta > 0.01) return 'up';
  if (delta < -0.01) return 'down';
  return 'steady';
}

function formatDelta(delta?: number | null): string | null {
  if (delta == null || Number.isNaN(delta)) {
    return null;
  }
  return formatPercent(delta, { defaultValue: '', maximumFractionDigits: 1, signDisplay: 'always', isFraction: true }) || null;
}

const ALERT_COLORS: Record<SiteMetricAlert['severity'], string> = {
  info: 'border-slate-200 bg-slate-50 text-slate-700 dark:border-dark-600 dark:bg-dark-800 dark:text-dark-100',
  warning: 'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-400/40 dark:bg-amber-900/20 dark:text-amber-200',
  critical: 'border-rose-300 bg-rose-50 text-rose-800 dark:border-rose-400/40 dark:bg-rose-950/40 dark:text-rose-200',
};

const STATUS_BADGE: Record<string, { label: string; color: 'success' | 'warning' | 'neutral' | 'error' }> = {
  ok: { label: 'Актуально', color: 'success' },
  stale: { label: 'Задержка', color: 'warning' },
  no_data: { label: 'Нет данных', color: 'neutral' },
  unknown: { label: 'Неизвестно', color: 'neutral' },
};

function renderMetricCard(key: string, metric: SiteMetricValue) {
  const config = METRIC_CONFIG[key];
  if (!config) {
    return null;
  }
  const deltaLabel = formatDelta(metric.delta ?? null);
  return (
    <MetricCard
      key={key}
      label={config.label}
      value={config.format(metric)}
      delta={deltaLabel ?? undefined}
      trend={deltaLabel ? pickTrend(metric.delta ?? null) : undefined}
      trendLabel={deltaLabel ? 'к прошлому периоду' : undefined}
      tone={config.tone}
    />
  );
}

function formatLag(value?: number | null): string | null {
  if (!value || Number.isNaN(value) || value <= 0) {
    return null;
  }
  const minutes = Math.round(value / 60000);
  if (minutes <= 0) {
    return null;
  }
  return `${minutes} мин`;
}

export function SitePageMetricsPanel({
  metrics,
  loading,
  error,
  period,
  onChangePeriod,
  onRefresh,
}: SitePageMetricsPanelProps): React.ReactElement {
  const statusInfo = metrics ? STATUS_BADGE[metrics.status] ?? STATUS_BADGE.unknown : undefined;
  const lagLabel = metrics ? formatLag(metrics.source_lag_ms ?? null) : null;

  return (
    <Card className="space-y-4 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="text-sm font-semibold text-gray-900 dark:text-white">Метрики страницы</div>
          {metrics?.range ? (
            <div className="text-xs text-gray-500 dark:text-dark-300">
              Период: {formatDateTime(metrics.range.start, { mode: 'date', fallback: '—' })} —{' '}
              {formatDateTime(metrics.range.end, { mode: 'date', fallback: '—' })}
              {lagLabel ? ` · задержка ${lagLabel}` : ''}
            </div>
          ) : (
            <div className="text-xs text-gray-500 dark:text-dark-300">Данные обновляются по выбранному периоду</div>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {statusInfo ? <Badge color={statusInfo.color}>{statusInfo.label}</Badge> : null}
          <Select value={period} onChange={(event) => onChangePeriod(event.target.value as SiteMetricsPeriod)}>
            {PERIOD_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <Button size="sm" variant="ghost" onClick={onRefresh} disabled={loading}>
            {loading ? 'Обновление…' : 'Обновить'}
          </Button>
        </div>
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/40 dark:text-rose-200">
          <AlertTriangle className="mt-0.5 h-4 w-4" />
          <span>{error}</span>
        </div>
      ) : null}

      {loading && !metrics ? (
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-dark-200">
          <Spinner className="h-4 w-4" />
          Загрузка метрик…
        </div>
      ) : null}

      {!loading && metrics && Object.keys(metrics.metrics).length === 0 && metrics.alerts.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-300">
          Для выбранного периода пока нет данных.
        </div>
      ) : null}

      {metrics && Object.keys(metrics.metrics).length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {Object.entries(metrics.metrics)
            .map(([key, metric]) => renderMetricCard(key, metric))
            .filter((node): node is React.ReactElement => node != null)}
        </div>
      ) : null}

      {metrics?.alerts?.length ? (
        <div className="space-y-2">
          {metrics.alerts.map((alert) => (
            <div
              key={`${alert.code}-${alert.message}`}
              className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-xs ${ALERT_COLORS[alert.severity]}`}
            >
              <AlertTriangle className="mt-0.5 h-4 w-4" />
              <div className="space-y-1">
                <div className="font-semibold">{alert.message}</div>
                <div className="text-[11px] uppercase tracking-wide opacity-80">{alert.code}</div>
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </Card>
  );
}

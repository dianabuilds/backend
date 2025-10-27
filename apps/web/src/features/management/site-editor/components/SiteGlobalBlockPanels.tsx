import React from 'react';
import { AlertTriangle } from '@icons';
import { Badge, Button, Card, Select, Spinner } from '@ui';
import { MetricCard, type MetricTrend } from '@ui/patterns/MetricCard';
import { formatDateTime, formatNumber, formatPercent } from '@shared/utils/format';
import { statusAppearance } from '../utils/pageHelpers';
import type {
  SiteDiffChange,
  SiteGlobalBlockHistoryItem,
  SiteGlobalBlockMetricsResponse,
  SiteGlobalBlockUsage,
  SiteGlobalBlockWarning,
  SiteMetricsPeriod,
  SiteMetricAlert,
  SiteMetricValue,
  SitePageDiffEntry,
} from '@shared/types/management';

const PERIOD_OPTIONS: Array<{ value: SiteMetricsPeriod; label: string }> = [
  { value: '1d', label: '24 часа' },
  { value: '7d', label: '7 дней' },
  { value: '30d', label: '30 дней' },
];

type MetaItemProps = {
  label: string;
  value: React.ReactNode;
};

export function MetaItem({ label, value }: MetaItemProps): React.ReactElement {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-dark-300">{label}</span>
      <span className="text-xs font-medium text-gray-700 dark:text-dark-50">{value}</span>
    </div>
  );
}

export function GlobalBlockWarnings({ warnings }: { warnings: SiteGlobalBlockWarning[] }): React.ReactElement | null {
  if (!warnings.length) {
    return null;
  }
  return (
    <div className="space-y-2">
      {warnings.map((warning) => (
        <div
          key={`${warning.code}-${warning.page_id ?? ''}`}
          className="flex items-start gap-2 rounded-xl border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-400/40 dark:bg-amber-900/20 dark:text-amber-200"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4" />
          <div>
            <div className="font-medium">{warning.message}</div>
            {warning.page_id ? (
              <div className="text-[11px] uppercase tracking-wide text-amber-600 dark:text-amber-300">
                Страница: {warning.page_id}
              </div>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}

type GlobalBlockUsageListProps = {
  usage: SiteGlobalBlockUsage[];
  loading: boolean;
};

export function GlobalBlockUsageList({ usage, loading }: GlobalBlockUsageListProps): React.ReactElement {
  if (loading && !usage.length) {
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
        <Spinner className="h-4 w-4" />
        Загружаем использование блока...
      </div>
    );
  }
  if (!usage.length) {
    return (
      <div className="rounded-2xl border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-300">
        Блок пока не используется на страницах.
      </div>
    );
  }
  return (
    <div className="space-y-3">
      <div className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-300">Использование</div>
      <ul className="space-y-2">
        {usage.map((item) => {
          const pageStatus = statusAppearance(item.status);
          return (
            <li
              key={`${item.page_id}-${item.section}`}
              className="rounded-2xl border border-gray-200 p-4 text-xs text-gray-600 dark:border-dark-600 dark:text-dark-200"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">{item.title}</div>
                  <div className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-dark-300">
                    {item.slug}
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge color={pageStatus.color} variant="soft">
                    {pageStatus.label}
                  </Badge>
                  {item.has_draft ? (
                    <Badge color="warning" variant="soft">
                      Черновик
                    </Badge>
                  ) : null}
                </div>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2">
                <MetaItem label="Зона" value={item.section || '—'} />
                <MetaItem label="Локаль" value={item.locale || '—'} />
                <MetaItem
                  label="Последняя публикация"
                  value={formatDateTime(item.last_published_at, { fallback: '—' })}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

type GlobalBlockHistoryPanelProps = {
  entries: SiteGlobalBlockHistoryItem[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
};

export function GlobalBlockHistoryPanel({
  entries,
  loading,
  error,
  onRefresh,
}: GlobalBlockHistoryPanelProps): React.ReactElement {
  const latestVersion = entries.length ? entries[0].version : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-gray-900 dark:text-white">История публикаций</div>
          <div className="text-xs text-gray-500 dark:text-dark-300">
            Версии и комментарии к публикациям
          </div>
        </div>
        <Button size="sm" variant="ghost" onClick={onRefresh} disabled={loading}>
          {loading ? 'Обновление…' : 'Обновить'}
        </Button>
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/40 dark:text-rose-200">
          <AlertTriangle className="mt-0.5 h-4 w-4" />
          <span>{error}</span>
        </div>
      ) : null}

      {loading && !entries.length ? (
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
          <Spinner className="h-4 w-4" />
          Загрузка истории…
        </div>
      ) : null}

      {entries.length ? (
        <ul className="space-y-3">
          {entries.map((entry) => {
            const isLatest = latestVersion != null && entry.version === latestVersion;
            return (
              <li key={entry.id} className="space-y-3 rounded-xl border border-gray-200 p-4 dark:border-dark-600">
                <div className="flex flex-wrap items-start justify-between gap-3 text-xs text-gray-500 dark:text-dark-300">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
                      Версия v{entry.version}
                      {isLatest ? <Badge color="primary">Актуальная</Badge> : null}
                    </div>
                    <div>
                      Опубликована:{' '}
                      {formatDateTime(entry.published_at, { fallback: '—', withSeconds: true })}
                    </div>
                    <div>Автор: {entry.published_by || '—'}</div>
                  </div>
                </div>
                <div className="text-sm text-gray-700 dark:text-dark-100">
                  {entry.comment ? (
                    <>«{entry.comment}»</>
                  ) : (
                    <span className="italic text-gray-500 dark:text-dark-300">
                      Комментарий не указан
                    </span>
                  )}
                </div>
                <HistoryDiffList diff={entry.diff} />
              </li>
            );
          })}
        </ul>
      ) : (
        !loading &&
        !error && (
          <div className="rounded-lg border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-300">
            История появится после первой публикации блока.
          </div>
        )
      )}
    </div>
  );
}

function HistoryDiffList({ diff }: { diff: SitePageDiffEntry[] | null | undefined }): React.ReactElement {
  if (!diff || !diff.length) {
    return (
      <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-500 dark:bg-dark-700 dark:text-dark-300">
        Изменений не зафиксировано.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {diff.map((entry, index) => {
        const key =
          `${entry.type}-${('blockId' in entry ? entry.blockId : entry.field) ?? 'n/a'}-${entry.change}-${index}`;
        return (
          <div
            key={key}
            className="rounded-lg bg-gray-50 p-3 text-xs text-gray-700 dark:bg-dark-700 dark:text-dark-100"
          >
            <div className="font-semibold text-gray-900 dark:text-white">
              {describeDiffEntry(entry)}
            </div>
            {renderDiffDetails(entry)}
          </div>
        );
      })}
    </div>
  );
}

function describeDiffEntry(entry: SitePageDiffEntry): string {
  const verbs: Record<SiteDiffChange, string> = {
    added: 'добавлен',
    removed: 'удален',
    updated: 'обновлен',
    moved: 'перемещен',
  };

  if (entry.type === 'block') {
    const prefix = `Блок ${entry.blockId}`;
    if (entry.change === 'moved') {
      if (entry.from != null && entry.to != null) {
        return `${prefix} перемещен (${entry.from} → ${entry.to})`;
      }
      return `${prefix} перемещен`;
    }
    return `${prefix} ${verbs[entry.change] ?? entry.change}`;
  }

  const scope = entry.type === 'meta' ? 'Мета-свойство' : 'Поле данных';
  const change =
    entry.change === 'removed'
      ? 'удалено'
      : entry.change === 'added'
      ? 'добавлено'
      : 'обновлено';
  return `${scope} ${entry.field} ${change}`;
}

function renderDiffDetails(entry: SitePageDiffEntry): React.ReactElement | null {
  if (entry.type === 'block' && entry.change === 'moved') {
    const from = entry.from != null ? entry.from : '—';
    const to = entry.to != null ? entry.to : '—';
    return (
      <div className="mt-2 text-xs text-gray-600 dark:text-dark-300">
        Позиция: {from} {'→'} {to}
      </div>
    );
  }

  const before = 'before' in entry ? entry.before : undefined;
  const after = 'after' in entry ? entry.after : undefined;
  if (before === undefined && after === undefined) {
    return null;
  }

  return (
    <div className="mt-2 space-y-1 text-xs text-gray-600 dark:text-dark-300">
      {before !== undefined ? (
        <div>
          <span className="font-semibold text-gray-700 dark:text-dark-100">До:</span>{' '}
          <span className="break-all">{formatDiffValue(before)}</span>
        </div>
      ) : null}
      {after !== undefined ? (
        <div>
          <span className="font-semibold text-gray-700 dark:text-dark-100">После:</span>{' '}
          <span className="break-all">{formatDiffValue(after)}</span>
        </div>
      ) : null}
    </div>
  );
}

function formatDiffValue(value: unknown): string {
  if (value == null) {
    return '—';
  }
  if (typeof value === 'string') {
    return value;
  }
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

type GlobalBlockMetricsPanelProps = {
  metrics: SiteGlobalBlockMetricsResponse | null;
  loading: boolean;
  error: string | null;
  period: SiteMetricsPeriod;
  onChangePeriod: (period: SiteMetricsPeriod) => void;
  onRefresh: () => void;
};

const BLOCK_METRIC_CONFIG: Record<
  string,
  {
    label: string;
    tone: 'primary' | 'secondary' | 'warning' | 'success' | 'neutral';
    format: (metric: SiteMetricValue) => string;
  }
> = {
  impressions: {
    label: 'Показы',
    tone: 'primary',
    format: (metric) =>
      formatNumber(metric.value, { defaultValue: '—', compact: true, maximumFractionDigits: 0 }),
  },
  clicks: {
    label: 'Клики',
    tone: 'secondary',
    format: (metric) =>
      formatNumber(metric.value, { defaultValue: '—', compact: true, maximumFractionDigits: 0 }),
  },
  ctr: {
    label: 'CTR',
    tone: 'primary',
    format: (metric) =>
      formatPercent(metric.value, { defaultValue: '—', maximumFractionDigits: 2, isFraction: true }),
  },
  conversions: {
    label: 'Конверсии',
    tone: 'success',
    format: (metric) =>
      formatNumber(metric.value, { defaultValue: '—', compact: true, maximumFractionDigits: 0 }),
  },
  revenue: {
    label: 'Выручка',
    tone: 'success',
    format: (metric) =>
      formatNumber(metric.value, { defaultValue: '—', compact: true, maximumFractionDigits: 0 }),
  },
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
  return (
    formatPercent(delta, {
      defaultValue: '',
      maximumFractionDigits: 1,
      signDisplay: 'always',
      isFraction: true,
    }) || null
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

const ALERT_COLORS: Record<SiteMetricAlert['severity'], string> = {
  info: 'border-slate-200 bg-slate-50 text-slate-700 dark:border-dark-600 dark:bg-dark-800 dark:text-dark-100',
  warning:
    'border-amber-300 bg-amber-50 text-amber-800 dark:border-amber-400/40 dark:bg-amber-900/20 dark:text-amber-200',
  critical:
    'border-rose-300 bg-rose-50 text-rose-800 dark:border-rose-400/40 dark:bg-rose-950/40 dark:text-rose-200',
};

const STATUS_BADGE: Record<string, { label: string; color: 'success' | 'warning' | 'neutral' | 'error' }> = {
  ok: { label: 'Актуально', color: 'success' },
  stale: { label: 'Задержка', color: 'warning' },
  no_data: { label: 'Нет данных', color: 'neutral' },
  unknown: { label: 'Неизвестно', color: 'neutral' },
};

export function GlobalBlockMetricsPanel({
  metrics,
  loading,
  error,
  period,
  onChangePeriod,
  onRefresh,
}: GlobalBlockMetricsPanelProps): React.ReactElement {
  const statusInfo = metrics ? STATUS_BADGE[metrics.status] ?? STATUS_BADGE.unknown : undefined;
  const lagLabel = metrics ? formatLag(metrics.source_lag_ms ?? null) : null;
  const metricEntries = metrics ? Object.entries(metrics.metrics) : [];

  return (
    <Card className="space-y-4 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="text-sm font-semibold text-gray-900 dark:text-white">Метрики блока</div>
          {metrics?.range ? (
            <div className="text-xs text-gray-500 dark:text-dark-300">
              Период: {formatDateTime(metrics.range.start, { mode: 'date', fallback: '—' })} —{' '}
              {formatDateTime(metrics.range.end, { mode: 'date', fallback: '—' })}
              {lagLabel ? ` · задержка ${lagLabel}` : ''}
            </div>
          ) : (
            <div className="text-xs text-gray-500 dark:text-dark-300">Выберите период для анализа показателей.</div>
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

      {!loading && metrics && metricEntries.length === 0 && metrics.alerts.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-300">
          Для выбранного периода пока нет данных.
        </div>
      ) : null}

      {metrics && metricEntries.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {metricEntries.map(([key, metric]) => {
            const config = BLOCK_METRIC_CONFIG[key];
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
          })}
        </div>
      ) : null}

      {metrics?.alerts?.length ? (
        <div className="space-y-2">
          {metrics.alerts.map((alert, index) => (
            <div
              key={`${alert.code}-${index}`}
              className={`rounded-lg border p-3 text-xs ${ALERT_COLORS[alert.severity]}`}
            >
              {alert.message}
            </div>
          ))}
        </div>
      ) : null}

      {metrics?.top_pages?.length ? (
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-300">
            Топ-страницы
          </div>
          <ul className="space-y-2">
            {metrics.top_pages.map((page) => (
              <li
                key={page.page_id}
                className="flex flex-col gap-1 rounded-xl border border-gray-200 p-3 text-xs text-gray-600 dark:border-dark-600 dark:text-dark-200 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">
                    {page.title}
                  </div>
                  <div className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-dark-300">
                    {page.slug}
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <MetaItem
                    label="Показы"
                    value={formatNumber(page.impressions ?? 0, { defaultValue: '—', maximumFractionDigits: 0 })}
                  />
                  <MetaItem
                    label="Клики"
                    value={formatNumber(page.clicks ?? 0, { defaultValue: '—', maximumFractionDigits: 0 })}
                  />
                  <MetaItem
                    label="CTR"
                    value={formatPercent(page.ctr, {
                      defaultValue: '—',
                      maximumFractionDigits: 2,
                      isFraction: true,
                    })}
                  />
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Card>
  );
}

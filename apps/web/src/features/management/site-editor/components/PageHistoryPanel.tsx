import React from 'react';
import { AlertTriangle } from '@icons';
import { Badge, Button, Spinner } from '@ui';
import { formatDateTime } from '@shared/utils/format';
import type { SiteDiffChange, SitePageDiffEntry, SitePageVersion } from '@shared/types/management';

export type SitePageHistoryPanelProps = {
  entries: SitePageVersion[];
  loading: boolean;
  error: string | null;
  restoringVersion: number | null;
  onRestore: (version: number) => void;
  onRefresh: () => void;
};

export function SitePageHistoryPanel({
  entries,
  loading,
  error,
  restoringVersion,
  onRestore,
  onRefresh,
}: SitePageHistoryPanelProps): React.ReactElement {
  const [showAll, setShowAll] = React.useState(false);
  const DEFAULT_VISIBLE = 3;

  React.useEffect(() => {
    setShowAll(false);
  }, [entries]);

  const visibleEntries = showAll ? entries : entries.slice(0, DEFAULT_VISIBLE);
  const hasMore = entries.length > DEFAULT_VISIBLE;
  const latestVersion = entries.length ? entries[0].version : null;

  return (
    <details className="group rounded-2xl border border-gray-200/70 bg-white/95 text-gray-900 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/80 dark:text-dark-50 [&_summary::-webkit-details-marker]:hidden">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold">
        <span>История публикаций</span>
        <span className="text-xs text-primary-500 group-open:hidden">Развернуть</span>
        <span className="hidden text-xs text-primary-500 group-open:block">Свернуть</span>
      </summary>
      <div className="space-y-3 border-t border-gray-100 px-4 py-4 dark:border-dark-700/60">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-gray-500 dark:text-dark-300">
            Последние публикации и комментарии к релизам.
          </p>
          <Button size="xs" variant="ghost" onClick={onRefresh} disabled={loading}>
            {loading ? 'Обновление…' : 'Обновить'}
          </Button>
        </div>

        {error ? (
          <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/30 dark:text-rose-200">
            <AlertTriangle className="mt-0.5 h-4 w-4" />
            <span>{error}</span>
          </div>
        ) : null}

        {loading && !entries.length ? (
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
            <Spinner size="sm" />
            Загружаем историю…
          </div>
        ) : null}

        {entries.length ? (
          <>
            <ul className="space-y-3">
              {visibleEntries.map((entry) => {
                const isLatest = latestVersion != null && entry.version === latestVersion;
                const isRestoring = restoringVersion === entry.version;
                return (
                  <li key={entry.id} className="space-y-2 rounded-2xl border border-gray-200/70 bg-white/90 px-3 py-2 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/70">
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1 text-xs text-gray-500 dark:text-dark-300">
                        <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-gray-900 dark:text-dark-50">
                          Версия v{entry.version}
                          {isLatest ? <Badge color="primary">Текущая</Badge> : null}
                        </div>
                        <div>
                          Опубликована:{' '}
                          {formatDateTime(entry.published_at, { fallback: '—', withSeconds: true })}
                        </div>
                        <div>Автор: {entry.published_by || '—'}</div>
                      </div>
                      <Button
                        size="xs"
                        variant="outlined"
                        color="neutral"
                        disabled={isRestoring}
                        onClick={() => onRestore(entry.version)}
                      >
                        {isRestoring ? 'Восстановление…' : 'Восстановить'}
                      </Button>
                    </div>

                    <div className="rounded-xl border border-gray-100/70 bg-gray-50/80 px-3 py-2 text-[11px] leading-5 text-gray-600 dark:border-dark-600/40 dark:bg-dark-700/40 dark:text-dark-200">
                      {entry.comment ? (
                        <span>«{entry.comment}»</span>
                      ) : (
                        <span className="italic text-gray-500 dark:text-dark-300">Комментарий не указан</span>
                      )}
                    </div>

                    <HistoryDiff diff={entry.diff} />
                  </li>
                );
              })}
            </ul>
            {hasMore ? (
              <div className="pt-1">
                <Button size="xs" variant="ghost" onClick={() => setShowAll((prev) => !prev)}>
                  {showAll ? 'Скрыть дополнительные версии' : `Показать всю историю (${entries.length})`}
                </Button>
              </div>
            ) : null}
          </>
        ) : (
          !loading &&
          !error && (
            <div className="rounded-xl border border-dashed border-gray-200 px-3 py-2 text-[11px] text-gray-500 dark:border-dark-600 dark:text-dark-300">
              История появится после первой публикации страницы.
            </div>
          )
        )}
      </div>
    </details>
  );
}

function HistoryDiff({ diff }: { diff: SitePageVersion['diff'] }): React.ReactElement {
  if (!diff || !diff.length) {
    return (
      <div className="rounded-xl border border-gray-100/70 bg-white/80 px-3 py-2 text-[11px] text-gray-500 dark:border-dark-600/40 dark:bg-dark-700/40 dark:text-dark-200">
        Изменений не зафиксировано.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {diff.map((entry, index) => {
        const key = `${entry.type}-${('blockId' in entry ? entry.blockId : entry.field) ?? 'n/a'}-${entry.change}-${index}`;
        return (
          <div
            key={key}
            className="rounded-xl border border-gray-100/70 bg-white/80 px-3 py-2 text-[11px] text-gray-600 dark:border-dark-600/40 dark:bg-dark-700/40 dark:text-dark-200"
          >
            <div className="font-semibold text-gray-900 dark:text-dark-50">{describeDiffEntry(entry)}</div>
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
    updated: 'обновлён',
    moved: 'перемещён',
  };

  if (entry.type === 'block') {
    return `Блок ${entry.blockId} ${verbs[entry.change] ?? entry.change}`;
  }

  const scope = entry.type === 'meta' ? 'Метаданные' : 'Поле';
  const action =
    entry.change === 'removed' ? 'удалено' : entry.change === 'added' ? 'добавлено' : 'обновлено';
  return `${scope} ${entry.field} ${action}`;
}

function renderDiffDetails(entry: SitePageDiffEntry): React.ReactElement | null {
  if (entry.type === 'block' && entry.change === 'moved') {
    const from = entry.from != null ? entry.from : '—';
    const to = entry.to != null ? entry.to : '—';
    return (
      <div className="mt-1 text-[11px] text-gray-600 dark:text-dark-300">
        Позиция: {from} → {to}
      </div>
    );
  }

  const before = 'before' in entry ? entry.before : undefined;
  const after = 'after' in entry ? entry.after : undefined;
  if (before === undefined && after === undefined) {
    return null;
  }

  return (
    <div className="mt-1 space-y-1 text-[11px] text-gray-600 dark:text-dark-300">
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
  try {
    const serialized = typeof value === 'string' ? value : JSON.stringify(value);
    if (!serialized) return '—';
    return serialized.length > 160 ? `${serialized.slice(0, 157)}…` : serialized;
  } catch {
    return String(value);
  }
}

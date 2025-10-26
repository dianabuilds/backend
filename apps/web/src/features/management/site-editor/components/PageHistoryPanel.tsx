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
  const latestVersion = entries.length ? entries[0].version : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-gray-900 dark:text-white">История версий</div>
          <div className="text-xs text-gray-500 dark:text-dark-300">
            Разница между публикациями и комментарии
          </div>
        </div>
        <Button size="sm" variant="ghost" onClick={onRefresh} disabled={loading}>
          {loading ? 'Обновление…' : 'Обновить'}
        </Button>
      </div>

      {error ? (
        <div className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200">
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
            const isRestoring = restoringVersion === entry.version;
            return (
              <li key={entry.id} className="space-y-3 rounded-xl border border-gray-200 p-4 dark:border-dark-600">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1 text-xs text-gray-500 dark:text-dark-300">
                    <div className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
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
                    size="sm"
                    variant="outlined"
                    color="neutral"
                    disabled={isRestoring}
                    onClick={() => onRestore(entry.version)}
                  >
                    {isRestoring ? 'Восстановление…' : 'Восстановить'}
                  </Button>
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

                <DiffList diff={entry.diff} />
              </li>
            );
          })}
        </ul>
      ) : (
        !loading &&
        !error && (
          <div className="rounded-lg border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-300">
            История появится после первой публикации страницы.
          </div>
        )
      )}
    </div>
  );
}

function DiffList({ diff }: { diff: SitePageVersion['diff'] }): React.ReactElement {
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
        const key = `${entry.type}-${('blockId' in entry ? entry.blockId : entry.field) ?? 'n/a'}-${entry.change}-${index}`;
        return (
          <div
            key={key}
            className="rounded-lg bg-gray-50 p-3 text-xs text-gray-700 dark:bg-dark-700 dark:text-dark-100"
          >
            <div className="font-semibold text-gray-900 dark:text-white">{describeDiffEntry(entry)}</div>
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
  const change = entry.change === 'removed' ? 'удалено' : entry.change === 'added' ? 'добавлено' : 'обновлено';
  return `${scope} ${entry.field} ${change}`;
}

function renderDiffDetails(entry: SitePageDiffEntry): React.ReactElement | null {
  if (entry.type === 'block' && entry.change === 'moved') {
    const from = entry.from != null ? entry.from : '—';
    const to = entry.to != null ? entry.to : '—';
    return (
      <div className="mt-2 text-xs text-gray-600 dark:text-dark-300">
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
  try {
    const serialized = typeof value === 'string' ? value : JSON.stringify(value);
    if (!serialized) return '—';
    return serialized.length > 160 ? `${serialized.slice(0, 157)}…` : serialized;
  } catch {
    return String(value);
  }
}


import React from 'react';
import { Badge, Button, Card, Spinner } from '@ui';
import type { SitePageDraftDiffResponse, SitePageDiffEntry } from '@shared/types/management';

type SitePageDiffPanelProps = {
  diff: SitePageDraftDiffResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
};

function renderDiffEntry(entry: SitePageDiffEntry, index: number): React.ReactElement {
  if (entry.type === 'block') {
    const label = {
      added: 'Добавлен блок',
      removed: 'Удалён блок',
      updated: 'Изменён блок',
      moved: 'Перемещён блок',
    }[entry.change];
    const movement =
      entry.change === 'moved' && entry.from != null && entry.to != null
        ? ` (позиция ${entry.from + 1} → ${entry.to + 1})`
        : '';
    return (
      <li key={`${entry.blockId}-${index}`} className="flex items-start gap-2 rounded-md border border-gray-200/70 bg-white/60 px-3 py-2 text-xs shadow-sm dark:border-dark-600/60 dark:bg-dark-800/80">
        <Badge color={entry.change === 'added' ? 'success' : entry.change === 'removed' ? 'error' : 'info'}>
          {entry.change}
        </Badge>
        <div className="flex-1">
          <div className="font-semibold text-gray-900 dark:text-dark-50">
            {label} <span className="font-mono text-[11px] text-primary-500">{entry.blockId}</span>
            {movement}
          </div>
          {entry.change === 'updated' && entry.before && entry.after ? (
            <div className="mt-1 grid gap-2 text-[11px] text-gray-600 dark:text-dark-200 md:grid-cols-2">
              <div>
                <div className="font-medium text-gray-500 dark:text-dark-300">Было</div>
                <pre className="mt-0.5 overflow-x-auto rounded bg-gray-100/80 p-2 dark:bg-dark-700/70">
                  {JSON.stringify(entry.before ?? null, null, 2)}
                </pre>
              </div>
              <div>
                <div className="font-medium text-gray-500 dark:text-dark-300">Стало</div>
                <pre className="mt-0.5 overflow-x-auto rounded bg-gray-100/80 p-2 dark:bg-dark-700/70">
                  {JSON.stringify(entry.after ?? null, null, 2)}
                </pre>
              </div>
            </div>
          ) : null}
        </div>
      </li>
    );
  }

  const label =
    entry.type === 'meta'
      ? 'Изменения метаданных'
      : 'Изменения данных';

  return (
    <li key={`${entry.type}-${entry.field}-${index}`} className="flex items-start gap-2 rounded-md border border-gray-200/70 bg-white/60 px-3 py-2 text-xs shadow-sm dark:border-dark-600/60 dark:bg-dark-800/80">
      <Badge color={entry.change === 'added' ? 'success' : entry.change === 'removed' ? 'error' : 'info'}>
        {entry.change}
      </Badge>
      <div className="flex-1">
        <div className="font-semibold text-gray-900 dark:text-dark-50">
          {label} <span className="font-mono text-[11px] text-primary-500">{entry.field}</span>
        </div>
        {entry.before !== undefined || entry.after !== undefined ? (
          <div className="mt-1 grid gap-2 text-[11px] text-gray-600 dark:text-dark-200 md:grid-cols-2">
            <div>
              <div className="font-medium text-gray-500 dark:text-dark-300">Было</div>
              <pre className="mt-0.5 overflow-x-auto rounded bg-gray-100/80 p-2 dark:bg-dark-700/70">
                {JSON.stringify(entry.before ?? null, null, 2)}
              </pre>
            </div>
            <div>
              <div className="font-medium text-gray-500 dark:text-dark-300">Стало</div>
              <pre className="mt-0.5 overflow-x-auto rounded bg-gray-100/80 p-2 dark:bg-dark-700/70">
                {JSON.stringify(entry.after ?? null, null, 2)}
              </pre>
            </div>
          </div>
        ) : null}
      </div>
    </li>
  );
}

export function SitePageDiffPanel({
  diff,
  loading,
  error,
  onRefresh,
}: SitePageDiffPanelProps): React.ReactElement {
  const hasDiff = diff && Array.isArray(diff.diff) && diff.diff.length > 0;

  return (
    <Card padding="md" className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Изменения щодо публикации</h3>
          <p className="text-xs text-gray-500 dark:text-dark-200">
            Сравнение текущего черновика с опубликованной версией.
          </p>
        </div>
        <Button size="xs" variant="ghost" onClick={onRefresh} disabled={loading}>
          Обновить
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
          <Spinner size="sm" />
          Вычисляем отличие…
        </div>
      ) : null}

      {error ? (
        <div className="rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-600/60 dark:bg-rose-950/40 dark:text-rose-200">
          {error}
        </div>
      ) : null}

      {diff ? (
        <div className="rounded-md border border-gray-200/70 bg-white/70 px-3 py-2 text-[11px] text-gray-600 dark:border-dark-600/60 dark:bg-dark-800/70 dark:text-dark-200">
          Черновик v{diff.draft_version} · Публикация {diff.published_version ?? '—'}
        </div>
      ) : null}

      {hasDiff ? (
        <ul className="space-y-3">
          {diff!.diff!.map((entry, index) => renderDiffEntry(entry, index))}
        </ul>
      ) : !loading && !error ? (
        <div className="rounded-md border border-gray-200/70 bg-gray-50 px-3 py-2 text-xs text-gray-500 dark:border-dark-600/60 dark:bg-dark-800/60 dark:text-dark-200">
          Изменений относительно опубликованной версии не найдено.
        </div>
      ) : null}
    </Card>
  );
}

export default SitePageDiffPanel;

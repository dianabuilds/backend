import React from 'react';
import { Badge, Button, Spinner } from '@ui';
import type { SitePageDraftDiffResponse, SitePageDiffEntry } from '@shared/types/management';

type SitePageDiffPanelProps = {
  diff: SitePageDraftDiffResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
};

function getEntryMeta(entry: SitePageDiffEntry): {
  title: string;
  description: string | null;
  badgeColor: 'primary' | 'success' | 'error' | 'warning' | 'info';
} {
  if (entry.type === 'block') {
    const labels: Record<SitePageDiffEntry['change'], string> = {
      added: 'Добавлен блок',
      removed: 'Удалён блок',
      updated: 'Изменён блок',
      moved: 'Перемещён блок',
    };
    const movement =
      entry.change === 'moved' && entry.from != null && entry.to != null
        ? `Позиция ${entry.from + 1} → ${entry.to + 1}`
        : null;
    return {
      title: `${labels[entry.change] ?? 'Изменение блока'} · ${entry.blockId}`,
      description: movement,
      badgeColor:
        entry.change === 'added'
          ? 'success'
          : entry.change === 'removed'
            ? 'error'
            : entry.change === 'moved'
              ? 'warning'
              : 'info',
    };
  }

  const scope = entry.type === 'meta' ? 'Метаданные' : 'Данные';
  const change =
    entry.change === 'removed' ? 'удалены' : entry.change === 'added' ? 'добавлены' : 'обновлены';
  return {
    title: `${scope}: ${entry.field}`,
    description: `Значения ${change}`,
    badgeColor:
      entry.change === 'added'
        ? 'success'
        : entry.change === 'removed'
          ? 'error'
          : 'info',
  };
}

function renderEntryDetails(entry: SitePageDiffEntry): React.ReactNode {
  const renderJson = (value: unknown) => (
    <pre className="mt-1 max-h-48 overflow-auto rounded-lg bg-gray-100/80 p-2 text-[11px] leading-5 text-gray-700 dark:bg-dark-800/80 dark:text-dark-100">
      {JSON.stringify(value ?? null, null, 2)}
    </pre>
  );

  if (entry.type === 'block') {
    if (entry.change === 'moved') {
      return null;
    }
    if (entry.change === 'updated' && entry.before && entry.after) {
      return (
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <div className="text-[11px] font-semibold text-gray-500 dark:text-dark-300">Было</div>
            {renderJson(entry.before)}
          </div>
          <div>
            <div className="text-[11px] font-semibold text-gray-500 dark:text-dark-300">Стало</div>
            {renderJson(entry.after)}
          </div>
        </div>
      );
    }
    return entry.after ? renderJson(entry.after) : null;
  }

  const before = 'before' in entry ? entry.before : undefined;
  const after = 'after' in entry ? entry.after : undefined;
  if (before === undefined && after === undefined) {
    return null;
  }
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {before !== undefined ? (
        <div>
          <div className="text-[11px] font-semibold text-gray-500 dark:text-dark-300">Было</div>
          {renderJson(before)}
        </div>
      ) : null}
      {after !== undefined ? (
        <div>
          <div className="text-[11px] font-semibold text-gray-500 dark:text-dark-300">Стало</div>
          {renderJson(after)}
        </div>
      ) : null}
    </div>
  );
}

function DiffEntry({ entry, index }: { entry: SitePageDiffEntry; index: number }): React.ReactElement {
  const meta = getEntryMeta(entry);
  const hasDetails =
    entry.type === 'block'
      ? entry.change !== 'moved'
      : true;

  return (
    <li
      key={index}
      className="rounded-2xl border border-gray-200/70 bg-white/95 px-3 py-2 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/70"
    >
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge color={meta.badgeColor}>{entry.change}</Badge>
          <span className="text-sm font-medium text-gray-900 dark:text-dark-50">{meta.title}</span>
        </div>
        {meta.description ? <p className="text-xs text-gray-500 dark:text-dark-200">{meta.description}</p> : null}
        {hasDetails ? renderEntryDetails(entry) : null}
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
    <details
      className="group rounded-2xl border border-gray-200/70 bg-white/95 text-gray-900 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/80 dark:text-dark-50 [&_summary::-webkit-details-marker]:hidden"
    >
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold">
        <span>Изменения к публикации</span>
        <span className="text-xs text-primary-500 group-open:hidden">Развернуть</span>
        <span className="hidden text-xs text-primary-500 group-open:block">Свернуть</span>
      </summary>
      <div className="space-y-3 border-t border-gray-100 px-4 py-4 dark:border-dark-700/60">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-gray-500 dark:text-dark-200">
            Сравнение текущего черновика с опубликованной версией.
          </p>
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
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/30 dark:text-rose-200">
            {error}
          </div>
        ) : null}

        {diff ? (
          <div className="rounded-xl border border-gray-200/70 bg-white/90 px-3 py-2 text-[11px] text-gray-600 dark:border-dark-600/60 dark:bg-dark-800/60 dark:text-dark-200">
            Черновик v{diff.draft_version} · Публикация {diff.published_version ?? '—'}
          </div>
        ) : null}

        {hasDiff ? (
          <ul className="space-y-3">
            {diff!.diff!.map((entry, index) => (
              <DiffEntry key={index} entry={entry} index={index} />
            ))}
          </ul>
        ) : !loading && !error ? (
          <div className="rounded-xl border border-dashed border-gray-200 px-3 py-2 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-300">
            Изменений относительно опубликованной версии не найдено.
          </div>
        ) : null}
      </div>
    </details>
  );
}

export default SitePageDiffPanel;

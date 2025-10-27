import React from 'react';
import { AlertTriangle } from '@icons';
import { Badge, Button, Spinner } from '@ui';
import { formatDateTime } from '@shared/utils/format';
import type { SiteAuditEntry } from '@shared/types/management';

export type SitePageAuditPanelProps = {
  entries: SiteAuditEntry[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
};

function formatAuditAction(action: string | null | undefined): string {
  if (!action) return 'Неизвестное действие';
  const map: Record<string, string> = {
    create: 'Создание',
    update: 'Обновление',
    publish: 'Публикация',
    restore: 'Восстановление',
    draft_save: 'Сохранение черновика',
  };
  return map[action] ?? action;
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

function AuditSnapshot({ snapshot }: { snapshot: Record<string, unknown> | null | undefined }): React.ReactElement | null {
  if (!snapshot || Object.keys(snapshot).length === 0) {
    return null;
  }
  const entries = Object.entries(snapshot).slice(0, 6);
  return (
    <div className="grid gap-2 rounded-xl border border-gray-100/70 bg-white/80 px-3 py-2 text-[11px] text-gray-600 dark:border-dark-600/40 dark:bg-dark-700/40 dark:text-dark-200 sm:grid-cols-2">
      {entries.map(([key, value]) => (
        <div key={key}>
          <div className="font-semibold text-gray-700 dark:text-dark-100">{key}</div>
          <div className="break-all">{formatDiffValue(value)}</div>
        </div>
      ))}
      {Object.keys(snapshot).length > entries.length ? (
        <div className="text-[11px] italic text-gray-500 dark:text-dark-400">…и другие поля</div>
      ) : null}
    </div>
  );
}

export function SitePageAuditPanel({
  entries,
  loading,
  error,
  onRefresh,
}: SitePageAuditPanelProps): React.ReactElement {
  return (
    <details className="group rounded-2xl border border-gray-200/70 bg-white/95 text-gray-900 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/80 dark:text-dark-50 [&_summary::-webkit-details-marker]:hidden">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold">
        <span>Аудит действий</span>
        <span className="text-xs text-primary-500 group-open:hidden">Развернуть</span>
        <span className="hidden text-xs text-primary-500 group-open:block">Свернуть</span>
      </summary>
      <div className="space-y-3 border-t border-gray-100 px-4 py-4 dark:border-dark-700/60">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-gray-500 dark:text-dark-300">Последние события по странице.</p>
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
            Загружаем аудит…
          </div>
        ) : null}

        {entries.length ? (
          <ul className="space-y-3">
            {entries.map((entry) => (
              <li key={entry.id} className="space-y-2 rounded-2xl border border-gray-200/70 bg-white/90 px-3 py-2 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/70">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1 text-xs text-gray-500 dark:text-dark-300">
                    <div className="flex flex-wrap items-center gap-2 text-sm font-semibold text-gray-900 dark:text-dark-50">
                      {formatAuditAction(entry.action)}
                    </div>
                    <div>
                      Записано:{' '}
                      {formatDateTime(entry.created_at, { fallback: '—', withSeconds: true })}
                    </div>
                    <div>Автор: {entry.actor || '—'}</div>
                  </div>
                  {entry.snapshot && typeof entry.snapshot.version !== 'undefined' ? (
                    <Badge color="neutral">v{String(entry.snapshot.version)}</Badge>
                  ) : null}
                </div>
                <AuditSnapshot snapshot={entry.snapshot} />
              </li>
            ))}
          </ul>
        ) : (
          !loading &&
          !error && (
            <div className="rounded-xl border border-dashed border-gray-200 px-3 py-2 text-[11px] text-gray-500 dark:border-dark-600 dark:text-dark-300">
              Записи появятся после действий с этой страницей.
            </div>
          )
        )}
      </div>
    </details>
  );
}

export default SitePageAuditPanel;

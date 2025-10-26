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

export function SitePageAuditPanel({
  entries,
  loading,
  error,
  onRefresh,
}: SitePageAuditPanelProps): React.ReactElement {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-gray-900 dark:text-white">Аудит действий</div>
          <div className="text-xs text-gray-500 dark:text-dark-300">Последние события по странице</div>
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
          Загрузка аудита…
        </div>
      ) : null}

      {entries.length ? (
        <ul className="space-y-3">
          {entries.map((entry) => (
            <li key={entry.id} className="space-y-3 rounded-xl border border-gray-200 p-4 dark:border-dark-600">
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1 text-xs text-gray-500 dark:text-dark-300">
                  <div className="text-sm font-semibold text-gray-900 dark:text-white">
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
          <div className="rounded-lg border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-300">
            Записи аудита появятся после действий с этой страницей.
          </div>
        )
      )}
    </div>
  );
}

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

function AuditSnapshot({
  snapshot,
}: {
  snapshot: Record<string, unknown> | null | undefined;
}): React.ReactElement | null {
  if (!snapshot || Object.keys(snapshot).length === 0) {
    return null;
  }
  const entries = Object.entries(snapshot).slice(0, 6);
  return (
    <div className="grid gap-2 rounded-lg bg-gray-50 p-3 text-xs text-gray-600 dark:bg-dark-700 dark:text-dark-300 sm:grid-cols-2">
      {entries.map(([key, value]) => (
        <div key={key}>
          <div className="font-semibold text-gray-700 dark:text-dark-100">{key}</div>
          <div className="break-all">{formatDiffValue(value)}</div>
        </div>
      ))}
      {Object.keys(snapshot).length > entries.length ? (
        <div className="text-xs italic text-gray-500 dark:text-dark-400">…и другие поля</div>
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


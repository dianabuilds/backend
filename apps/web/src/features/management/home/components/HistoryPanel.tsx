import React from 'react';
import { Badge, Button, Card, Dialog } from '@ui';
import { formatDateTime } from '@shared/utils/format';
import type { HomeHistoryEntry } from '@shared/types/home';

type HistoryPanelProps = {
  entries: HomeHistoryEntry[];
  restoringVersion: number | null;
  onRestore: (entry: HomeHistoryEntry) => void;
};

const DISPLAY_LOCALE = 'ru-RU';
const DISPLAY_TIME_ZONE = 'UTC';
const PREVIEW_LIMIT = 3;

function formatDate(value: string | null): string {
  if (!value) return '—';
  return formatDateTime(value, {
    fallback: '—',
    locale: DISPLAY_LOCALE,
    timeZone: DISPLAY_TIME_ZONE,
    hour12: false,
  });
}

export default function HistoryPanel({ entries, restoringVersion, onRestore }: HistoryPanelProps): React.ReactElement {
  const [dialogOpen, setDialogOpen] = React.useState(false);

  const visibleEntries = React.useMemo(
    () => entries.slice(0, PREVIEW_LIMIT),
    [entries],
  );

  const handleOpenDialog = React.useCallback(() => setDialogOpen(true), []);
  const handleCloseDialog = React.useCallback(() => setDialogOpen(false), []);

  if (!entries.length) {
    return (
      <Card padding="sm" className="text-sm text-gray-600 dark:text-dark-200" data-testid="home-history-panel">
        История публикаций появится после первой публикации.
      </Card>
    );
  }

  const renderEntry = (entry: HomeHistoryEntry) => {
    const isRestoring = restoringVersion === entry.version;
    const disabled = entry.isCurrent || isRestoring;

    return (
      <li
        key={entry.version}
        className="rounded-lg border border-gray-150 p-3 dark:border-dark-500"
        data-testid="home-history-entry"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-900 dark:text-dark-50">Версия v{entry.version}</span>
              {entry.isCurrent ? <Badge color="success">Текущая</Badge> : null}
            </div>
            <div className="text-xs text-gray-500 dark:text-dark-300">
              Опубликована: {formatDate(entry.publishedAt ?? entry.createdAt)}
            </div>
            <div className="text-xs text-gray-500 dark:text-dark-300">
              Автор: {entry.actor ?? '—'}
            </div>
            {entry.comment ? (
              <p className="text-sm text-gray-700 dark:text-dark-200">«{entry.comment}»</p>
            ) : (
              <p className="text-sm text-gray-500 dark:text-dark-400 italic">Комментарий не указан</p>
            )}
          </div>
          <Button
            size="sm"
            variant="outlined"
            color="neutral"
            disabled={disabled}
            onClick={() => onRestore(entry)}
          >
            {isRestoring ? 'Восстановление…' : 'Восстановить'}
          </Button>
        </div>
      </li>
    );
  };

  return (
    <>
      <Card padding="sm" className="space-y-4" data-testid="home-history-panel">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-gray-900 dark:text-dark-50">История публикаций</div>
            <div className="text-xs text-gray-500 dark:text-dark-300">Последние изменения доступны для быстрого восстановления</div>
          </div>
          {entries.length > PREVIEW_LIMIT ? (
            <Button size="sm" variant="ghost" onClick={handleOpenDialog}>
              Показать всю историю
            </Button>
          ) : null}
        </div>

        <ul className="space-y-3">
          {visibleEntries.map(renderEntry)}
        </ul>

        {entries.length > PREVIEW_LIMIT ? (
          <div className="text-xs text-gray-500">
            Показаны последние {PREVIEW_LIMIT} версий из {entries.length}.
          </div>
        ) : null}
      </Card>

      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        title="Вся история публикаций"
        size="lg"
        footer={(
          <Button variant="outlined" color="neutral" onClick={handleCloseDialog}>
            Закрыть
          </Button>
        )}
      >
        <div className="max-h-[480px] space-y-4 overflow-y-auto pr-1">
          <ul className="space-y-3">
            {entries.map(renderEntry)}
          </ul>
        </div>
      </Dialog>
    </>
  );
}

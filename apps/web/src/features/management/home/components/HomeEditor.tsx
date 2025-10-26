import React from 'react';
import { Link } from 'react-router-dom';
import { Badge, Button, Card, Dialog, Spinner, Textarea, useToast } from '@ui';
import { formatDateTime } from '@shared/utils/format';
import type { HomeHistoryEntry } from '@shared/types/home';
import { HomeEditorContext } from '../HomeEditorContext';
import type { HomeEditorContextValue } from '../types';
import { useHomeEditorState } from '../hooks/useHomeEditorState';
import { BlockLibraryPanel } from './BlockLibrary';
import { BlockCanvas } from './BlockCanvas';
import { BlockInspector } from './BlockInspector';
import HomePreview from './HomePreview';
import HistoryPanel from './HistoryPanel';

const DISPLAY_LOCALE = 'ru-RU';
const DISPLAY_TIME_ZONE = 'UTC';

function formatDisplayDateTime(value: string | null): string {
  if (!value) return '—';
  return formatDateTime(value, {
    fallback: '—',
    locale: DISPLAY_LOCALE,
    timeZone: DISPLAY_TIME_ZONE,
    hour12: false,
  });
}

export default function HomeEditor(): React.ReactElement {
  const state = useHomeEditorState();
  const { pushToast } = useToast();

  const {
    loading,
    data,
    setData,
    setBlocks,
    selectBlock,
    selectedBlockId,
    dirty,
    saving,
    savingError,
    lastSavedAt,
    loadDraft,
    saveDraft,
    snapshot,
    slug,
    history,
    publishing,
    restoringVersion,
    publishDraft,
    restoreVersion,
    validation,
    revalidate,
  } = state;

  const contextValue = React.useMemo<HomeEditorContextValue>(() => ({
    loading,
    data,
    setData,
    setBlocks,
    selectBlock,
    selectedBlockId,
    dirty,
    saving,
    savingError,
    lastSavedAt,
    loadDraft,
    saveDraft,
    snapshot,
    slug,
    history,
    publishing,
    restoringVersion,
    publishDraft,
    restoreVersion,
    validation,
    revalidate,
  }), [
    loading,
    data,
    setData,
    setBlocks,
    selectBlock,
    selectedBlockId,
    dirty,
    saving,
    savingError,
    lastSavedAt,
    loadDraft,
    saveDraft,
    snapshot,
    slug,
    history,
    publishing,
    restoringVersion,
    publishDraft,
    restoreVersion,
    validation,
    revalidate,
  ]);

  const [publishDialogOpen, setPublishDialogOpen] = React.useState(false);
  const [publishComment, setPublishComment] = React.useState('');
  const [restoreEntry, setRestoreEntry] = React.useState<HomeHistoryEntry | null>(null);
  const [restoreComment, setRestoreComment] = React.useState('');

  const handleManualSave = React.useCallback(async () => {
    try {
      await saveDraft({ silent: false });
      pushToast({ intent: 'success', description: 'Черновик сохранён' });
    } catch {
      // ошибки обрабатываются внутри saveDraft
    }
  }, [pushToast, saveDraft]);

  const handleOpenPublish = React.useCallback(() => {
    setPublishComment('');
    setPublishDialogOpen(true);
  }, []);

  const handleClosePublish = React.useCallback(() => {
    if (!publishing) {
      setPublishDialogOpen(false);
    }
  }, [publishing]);

  const handleConfirmPublish = React.useCallback(async () => {
    try {
      const trimmed = publishComment.trim();
      await publishDraft({ comment: trimmed.length ? trimmed : undefined });
      pushToast({ intent: 'success', description: 'Конфигурация опубликована' });
      setPublishDialogOpen(false);
      setPublishComment('');
    } catch {
      // ошибки показаны глобально
    }
  }, [publishComment, publishDraft, pushToast]);

  const handleOpenRestore = React.useCallback((entry: HomeHistoryEntry) => {
    setRestoreEntry(entry);
    setRestoreComment('');
  }, []);

  const handleCloseRestore = React.useCallback(() => {
    if (restoringVersion === null) {
      setRestoreEntry(null);
      setRestoreComment('');
    }
  }, [restoringVersion]);

  const handleConfirmRestore = React.useCallback(async () => {
    if (!restoreEntry) {
      return;
    }
    try {
      const trimmed = restoreComment.trim();
      await restoreVersion(restoreEntry.version, { comment: trimmed.length ? trimmed : undefined });
      pushToast({ intent: 'success', description: `Версия v${restoreEntry.version} восстановлена` });
      setRestoreEntry(null);
      setRestoreComment('');
    } catch {
      // ошибки показаны глобально
    }
  }, [restoreComment, restoreEntry, restoreVersion, pushToast]);

  const restoreDialogOpen = restoreEntry !== null;
  const activeRestoreVersion = restoreEntry?.version ?? null;

  const lastSavedLabel = React.useMemo(() => formatDisplayDateTime(lastSavedAt), [lastSavedAt]);
  const publishedLabel = React.useMemo(() => formatDisplayDateTime(snapshot.publishedAt), [snapshot.publishedAt]);
  const versionLabel = snapshot.version ? `v${snapshot.version}` : '—';

  const statusBadge = dirty
    ? <Badge color="warning">Есть несохранённые изменения</Badge>
    : <Badge color="success">Черновик актуален</Badge>;
  const savingBadge = saving ? <Badge color="info">Сохранение…</Badge> : null;
  const publishingBadge = publishing ? <Badge color="info">Публикация…</Badge> : null;

  const headerStats = React.useMemo(() => ([
    {
      label: 'Версия черновика',
      value: versionLabel,
      hint: snapshot.updatedAt ? `Обновлено ${formatDisplayDateTime(snapshot.updatedAt)}` : '—',
    },
    {
      label: 'Последнее сохранение',
      value: lastSavedLabel,
      hint: dirty ? 'Есть изменения, ожидающие сохранения' : 'Синхронизировано',
    },
    {
      label: 'Опубликовано',
      value: publishedLabel,
      hint: snapshot.publishedAt ? 'Текущая опубликованная версия' : 'Черновик ещё не опубликован',
    },
  ]), [dirty, lastSavedLabel, publishedLabel, snapshot.publishedAt, snapshot.updatedAt, versionLabel]);

  const breadcrumbs = React.useMemo(() => ([
    { label: 'Управление', to: '/platform/system' },
    { label: 'Главная страница' },
  ]), []);

  return (
    <HomeEditorContext.Provider value={contextValue}>
      <div className="space-y-6 pb-10">
        <section className="rounded-3xl border border-white/60 bg-white/75 px-4 py-4 shadow-sm backdrop-blur-sm transition dark:border-dark-600/70 dark:bg-dark-800/70 sm:px-6 lg:px-7">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-2">
              <nav aria-label="Хлебные крошки" className="flex flex-wrap items-center gap-1 text-2xs font-medium uppercase tracking-wide text-gray-500 dark:text-dark-200/70">
                {breadcrumbs.map((crumb, index) => {
                  const isLast = index === breadcrumbs.length - 1;
                  if (crumb.to && !isLast) {
                    return (
                      <React.Fragment key={`${crumb.label}-${index}`}>
                        <Link to={crumb.to} className="transition-colors hover:text-primary-600 dark:hover:text-primary-300">
                          {crumb.label}
                        </Link>
                        <span className="opacity-40">/</span>
                      </React.Fragment>
                    );
                  }

                  return (
                    <React.Fragment key={`${crumb.label}-${index}`}>
                      <span className={isLast ? 'text-gray-800 dark:text-white' : ''}>{crumb.label}</span>
                      {!isLast ? <span className="opacity-40">/</span> : null}
                    </React.Fragment>
                  );
                })}
              </nav>

              <div className="flex flex-col gap-2">
                <div className="flex flex-wrap items-center gap-2 lg:gap-3">
                  <h1 className="text-lg font-semibold tracking-tight text-gray-900 dark:text-white sm:text-xl">Редактор главной страницы</h1>
                  {statusBadge}
                  {savingBadge}
                  {publishingBadge}
                </div>
                <p className="text-2xs text-gray-600 dark:text-dark-100/80 sm:text-xs">
                  Автосохранение включено: изменения записываются через несколько секунд бездействия.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-2 lg:gap-3">
              <Button onClick={handleManualSave} disabled={loading || !dirty || saving}>
                {saving ? 'Сохранение…' : 'Сохранить черновик'}
              </Button>
              <Button
                variant="filled"
                onClick={handleOpenPublish}
                disabled={loading || publishing || saving}
              >
                {publishing ? 'Публикация…' : 'Опубликовать'}
              </Button>
            </div>
          </div>

          <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {headerStats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-2xl border border-gray-200/80 bg-white/90 px-3 py-2 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/60"
              >
                <div className="text-2xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/70">{stat.label}</div>
                <div className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">{stat.value}</div>
                {stat.hint ? (
                  <div className="mt-0.5 text-2xs text-gray-500 dark:text-dark-200/60">
                    {stat.hint}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </section>

        {savingError ? (
          <Card padding="sm" className="border-rose-200 bg-rose-50 text-rose-700">
            {savingError}
          </Card>
        ) : null}

        {!validation.valid && validation.general.length ? (
          <Card padding="sm" className="border-amber-200 bg-amber-50 text-amber-800">
            <div className="space-y-1">
              <div className="text-sm font-semibold">Нужно исправить:</div>
              <ul className="list-disc space-y-1 pl-5 text-xs">
                {validation.general.map((error, index) => (
                  <li key={`${error.path}-${index}`}>{error.message}</li>
                ))}
              </ul>
            </div>
          </Card>
        ) : null}

        {loading ? (
          <Card padding="sm" className="flex items-center justify-center py-32">
            <Spinner />
          </Card>
        ) : (
          <div className="grid gap-4 lg:grid-cols-[240px_minmax(0,1fr)] xl:grid-cols-[280px_minmax(0,1fr)_320px]">
            <div className="order-2 lg:order-1">
              <BlockLibraryPanel />
            </div>
            <div className="order-1 lg:order-2 min-w-0 space-y-4">
              <BlockCanvas />
              <HomePreview />
            </div>
            <div className="order-3 space-y-4">
              <BlockInspector />
              <HistoryPanel
                entries={history}
                restoringVersion={restoringVersion}
                onRestore={handleOpenRestore}
              />
            </div>
          </div>
        )}
      </div>

      <Dialog
        open={publishDialogOpen}
        onClose={handleClosePublish}
        title="Опубликовать конфигурацию"
        footer={(
          <>
            <Button variant="outlined" color="neutral" onClick={handleClosePublish} disabled={publishing}>
              Отмена
            </Button>
            <Button onClick={handleConfirmPublish} disabled={publishing}>
              {publishing ? 'Публикация…' : 'Опубликовать'}
            </Button>
          </>
        )}
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600">
            После публикации текущий черновик станет новой опубликованной версией. Вы сможете восстановить предыдущий вариант из истории.
          </p>
          <Textarea
            label="Комментарий к публикации"
            placeholder="Например, что изменилось в этой версии (необязательно)"
            rows={3}
            value={publishComment}
            onChange={(event) => setPublishComment(event.target.value)}
          />
        </div>
      </Dialog>

      <Dialog
        open={restoreDialogOpen}
        onClose={handleCloseRestore}
        title={restoreEntry ? `Восстановить версию v${restoreEntry.version}` : 'Восстановление версии'}
        footer={(
          <>
            <Button variant="outlined" color="neutral" onClick={handleCloseRestore} disabled={restoringVersion !== null}>
              Отмена
            </Button>
            <Button onClick={handleConfirmRestore} disabled={restoringVersion !== null}>
              {restoringVersion === activeRestoreVersion ? 'Восстановление…' : 'Восстановить'}
            </Button>
          </>
        )}
      >
        {restoreEntry ? (
          <div className="space-y-4 text-sm">
            <div className="space-y-1 text-gray-600">
              <div>Версия опубликована: {formatDisplayDateTime(restoreEntry.publishedAt ?? restoreEntry.createdAt)}</div>
              <div>Автор: {restoreEntry.actor ?? '—'}
              </div>

            </div>
            <Textarea
              label="Комментарий к восстановлению"
              placeholder="Опишите, почему откатываемся (необязательно)"
              rows={3}
              value={restoreComment}
              onChange={(event) => setRestoreComment(event.target.value)}
            />
          </div>
        ) : null}
      </Dialog>
    </HomeEditorContext.Provider>
  );
}

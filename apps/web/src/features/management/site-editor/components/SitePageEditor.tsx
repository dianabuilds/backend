import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Badge, Button, Card, Dialog, Select, Spinner, Textarea, useToast } from '@ui';
import { useAuth } from '@shared/auth';
import { formatDateTime } from '@shared/utils/format';
import type { SitePageReviewStatus } from '@shared/types/management';
import { HomeEditorContext } from '../../home/HomeEditorContext';
import type { HomeEditorContextValue } from '../../home/types';
import { BlockCanvas } from '../../home/components/BlockCanvas';
import { BlockInspector } from '../../home/components/BlockInspector';
import { SitePageHistoryPanel } from './PageHistoryPanel';
import { SitePageAuditPanel } from './PageAuditPanel';
import { useSitePageEditorState } from '../hooks/useSitePageEditorState';
import { statusAppearance, typeLabel } from '../utils/pageHelpers';
import { SitePageValidationPanel } from './SitePageValidationPanel';
import { SitePagePreviewPanel } from './SitePagePreviewPanel';
import { SitePageDiffPanel } from './SitePageDiffPanel';
import { SiteBlockLibraryPanel } from './SiteBlockLibraryPanel';
import { SitePageMetricsPanel } from './SitePageMetricsPanel';

const REVIEW_STATUS_OPTIONS: Array<{ value: SitePageReviewStatus; label: string }> = [
  { value: 'none', label: 'Ревью не требуется' },
  { value: 'pending', label: 'На ревью' },
  { value: 'approved', label: 'Одобрено' },
  { value: 'rejected', label: 'Отклонено' },
];

const REVIEW_STATUS_BADGE_COLOR: Record<SitePageReviewStatus, 'neutral' | 'warning' | 'success' | 'error'> = {
  none: 'neutral',
  pending: 'warning',
  approved: 'success',
  rejected: 'error',
};

function ErrorState({ message }: { message: string | null }): React.ReactElement | null {
  if (!message) return null;
  return (
    <Card padding="sm" className="border-rose-200 bg-rose-50 text-rose-700">
      {message}
    </Card>
  );
}

type SitePageEditorProps = {
  pageId: string;
};

export function SitePageEditor({ pageId }: SitePageEditorProps): React.ReactElement {
  const { pushToast } = useToast();
  const {
    page,
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
    pageMetrics,
    metricsLoading,
    metricsError,
    metricsPeriod,
    setMetricsPeriod,
    refreshMetrics,
    reviewStatus,
    setReviewStatus,
    loadDraft,
    saveDraft,
    publishing,
    publishDraft,
    snapshot,
    slug,
    validation,
    revalidate,
    serverValidation,
    serverValidationLoading,
    serverValidationError,
    runServerValidation,
    draftDiff,
    diffLoading,
    diffError,
    refreshDiff,
    preview,
    previewLayouts,
    previewLayout,
    selectPreviewLayout,
    previewLoading,
    previewError,
    refreshPreview,
    restoringVersion,
    restoreVersion,
    siteHistory,
    siteHistoryLoading,
    siteHistoryError,
    refreshHistory,
    auditEntries,
    auditLoading,
    auditError,
    refreshAudit,
    historyForContext,
  } = useSitePageEditorState({ pageId });
  const { user } = useAuth();
  const [publishDialogOpen, setPublishDialogOpen] = React.useState(false);
  const [publishComment, setPublishComment] = React.useState('');

  const handleServerValidation = React.useCallback(() => {
    runServerValidation().catch(() => undefined);
  }, [runServerValidation]);

  const handlePreviewRefresh = React.useCallback(() => {
    refreshPreview().catch(() => undefined);
  }, [refreshPreview]);

  const handleDiffRefresh = React.useCallback(() => {
    refreshDiff().catch(() => undefined);
  }, [refreshDiff]);

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
    history: historyForContext,
    publishing,
    publishDraft,
    restoreVersion,
    restoringVersion,
    validation,
    revalidate,
  }), [
    data,
    dirty,
    historyForContext,
    lastSavedAt,
    loadDraft,
    publishDraft,
    publishing,
    restoreVersion,
    restoringVersion,
    revalidate,
    saving,
    savingError,
    saveDraft,
    selectedBlockId,
    setBlocks,
    setData,
    selectBlock,
    slug,
    snapshot,
    validation,
    loading,
  ]);

  const roles = React.useMemo(() => {
    const set = new Set<string>();
    if (Array.isArray(user?.roles)) {
      user.roles.forEach((role) => {
        if (role) {
          set.add(String(role));
        }
      });
    }
    if (user?.role) {
      set.add(String(user.role));
    }
    return set;
  }, [user]);

  const canPublish = roles.has('site.publisher') || roles.has('site.admin') || roles.has('platform.admin') || roles.has('admin') || roles.has('moderator');

  const reviewStatusLabel = React.useMemo(() => {
    const option = REVIEW_STATUS_OPTIONS.find((item) => item.value === reviewStatus);
    return option ? option.label : reviewStatus;
  }, [reviewStatus]);

  const reviewStatusMessage = React.useMemo(() => {
    switch (reviewStatus) {
      case 'pending':
        return canPublish
          ? 'Черновик отправлен на ревью. Вы можете опубликовать самостоятельно, но зафиксируйте результат в комментарии.'
          : 'Черновик ожидает проверки. После одобрения владелец с правами публикации сможет выпустить страницу.';
      case 'approved':
        return 'Ревью одобрено. Страница готова к публикации.';
      case 'rejected':
        return 'Черновик отклонён. Внесите изменения и переключите статус, чтобы повторно отправить на ревью.';
      case 'none':
      default:
        return canPublish
          ? 'У вас есть права публикации — ревью необязательно. Используйте статусы, если нужно подключить коллег.'
          : 'Ревью не запрошено. Переведите статус на «На ревью», чтобы отправить черновик на проверку.';
    }
  }, [canPublish, reviewStatus]);

  const reviewStatusHint = dirty
    ? 'Сохраните черновик, чтобы зафиксировать новый статус.'
    : 'Изменения статуса сохраняются вместе с черновиком.';

  const handleReviewStatusChange = React.useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    setReviewStatus(event.target.value as SitePageReviewStatus);
  }, [setReviewStatus]);

  const reviewStatusBadgeColor = REVIEW_STATUS_BADGE_COLOR[reviewStatus] ?? 'neutral';
  const publishButtonDisabled = loading || publishing;

  const handleManualSave = React.useCallback(async () => {
    if (saving || publishing) {
      return;
    }
    try {
      await saveDraft({ silent: false });
      pushToast({ intent: 'success', description: 'Черновик сохранён' });
    } catch {
      // Ошибка уже отражена в состоянии savingError
    }
  }, [publishing, pushToast, saveDraft, saving]);

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
    if (publishing) {
      return;
    }
    const trimmed = publishComment.trim();
    try {
      await publishDraft({ comment: trimmed.length ? trimmed : undefined });
      setPublishDialogOpen(false);
      setPublishComment('');
      pushToast({ intent: 'success', description: 'Страница опубликована' });
    } catch {
      // Ошибка уже отражена в состоянии savingError
    }
  }, [publishComment, publishDraft, publishing, pushToast]);

  const handleRestore = React.useCallback(async (version: number) => {
    await restoreVersion(version);
    pushToast({ intent: 'success', description: `Версия v${version} восстановлена в черновик` });
  }, [pushToast, restoreVersion]);

  const headerStats = React.useMemo(() => {
    const stats: Array<{ label: string; value: React.ReactNode; hint?: string }> = [
      {
        label: 'Slug',
        value: <span className="font-mono text-xs text-gray-700 dark:text-dark-100">{slug || '—'}</span>,
      },
      {
        label: 'Черновик',
        value: snapshot.version != null ? `v${snapshot.version}` : '—',
        hint: lastSavedAt ? `обновлён ${formatDateTime(lastSavedAt, { fallback: '—', withSeconds: true })}` : undefined,
      },
      {
        label: 'Публикация',
        value: page?.published_version != null ? `v${page.published_version}` : '—',
        hint: page?.updated_at ? `обновлена ${formatDateTime(page.updated_at, { fallback: '—', withSeconds: true })}` : undefined,
      },
    ];
    return stats;
  }, [lastSavedAt, page?.published_version, page?.updated_at, slug, snapshot.version]);

  const status = page ? statusAppearance(page.status) : null;

  return (
    <HomeEditorContext.Provider value={contextValue}>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Link to="/management/site-editor" className="inline-flex items-center gap-1 text-primary-500 hover:text-primary-600">
                Назад к списку страниц
              </Link>
              {status ? <Badge color={status.color}>{status.label}</Badge> : null}
              {page?.type ? <Badge variant="outline">{typeLabel(page.type)}</Badge> : null}
            </div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">{page?.title ?? 'Страница'}</h1>
            <p className="text-sm text-gray-500 dark:text-dark-200">
              Настройте блоки и сохраните черновик. Автосохранение срабатывает при изменениях.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outlined"
              color="neutral"
              onClick={() => void loadDraft({ silent: false })}
              disabled={loading || saving || publishing}
            >
              Обновить данные
            </Button>
            <Button onClick={handleManualSave} disabled={!dirty || saving || publishing}>
              {saving ? 'Сохранение…' : dirty ? 'Сохранить черновик' : 'Сохранено'}
            </Button>
            {canPublish ? (
              <Button onClick={handleOpenPublish} disabled={publishButtonDisabled}>
                {publishing ? 'Публикация…' : 'Опубликовать'}
              </Button>
            ) : null}
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {headerStats.map((stat) => (
            <div key={stat.label} className="rounded-2xl border border-gray-200/80 bg-white/90 px-3 py-2 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/60">
              <div className="text-2xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200/70">{stat.label}</div>
              <div className="mt-1 text-sm font-semibold text-gray-900 dark:text-white">{stat.value}</div>
              {stat.hint ? <div className="mt-0.5 text-2xs text-gray-500 dark:text-dark-200/60">{stat.hint}</div> : null}
            </div>
          ))}
        </div>

        <SitePageMetricsPanel
          metrics={pageMetrics}
          loading={metricsLoading || loading}
          error={metricsError}
          period={metricsPeriod}
          onChangePeriod={setMetricsPeriod}
          onRefresh={refreshMetrics}
        />

        <Card className="flex flex-col gap-3 p-4 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-200/70">Статус ревью</div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge color={reviewStatusBadgeColor}>{reviewStatusLabel}</Badge>
              {canPublish ? <Badge variant="outline" color="success">Самопубликация</Badge> : null}
            </div>
            <p className="max-w-2xl text-xs text-gray-500 dark:text-dark-200">{reviewStatusMessage}</p>
          </div>
          <div className="flex w-full flex-col gap-2 md:w-56">
            <Select value={reviewStatus} onChange={handleReviewStatusChange} disabled={publishing || saving || loading}>
              {REVIEW_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
            <span className="text-[11px] text-gray-400 dark:text-dark-300">{reviewStatusHint}</span>
          </div>
        </Card>

        <ErrorState message={savingError} />

        <SitePageValidationPanel
          clientValidation={validation}
          serverValidation={serverValidation}
          serverValidationLoading={serverValidationLoading}
          serverValidationError={serverValidationError}
          onRunServerValidation={handleServerValidation}
        />

        {loading ? (
          <Card padding="sm" className="flex items-center justify-center py-32">
            <Spinner />
          </Card>
        ) : (
          <div className="grid gap-4 lg:grid-cols-[260px_minmax(0,1fr)_320px]">
            <div className="order-2 lg:order-1 space-y-4">
              <SiteBlockLibraryPanel />
            </div>
            <div className="order-1 lg:order-2 min-w-0 space-y-4">
              <BlockCanvas />
            </div>
            <div className="order-3 space-y-4">
              <BlockInspector />
              <SitePagePreviewPanel
                preview={preview}
                previewLayout={previewLayout}
                previewLayouts={previewLayouts}
                onSelectLayout={selectPreviewLayout}
                loading={previewLoading}
                error={previewError}
                onRefresh={handlePreviewRefresh}
              />
              <SitePageDiffPanel
                diff={draftDiff}
                loading={diffLoading}
                error={diffError}
                onRefresh={handleDiffRefresh}
              />
              <SitePageHistoryPanel
                entries={siteHistory}
                loading={siteHistoryLoading}
                error={siteHistoryError}
                onRestore={handleRestore}
                restoringVersion={restoringVersion}
                onRefresh={refreshHistory}
              />
              <SitePageAuditPanel
                entries={auditEntries}
                loading={auditLoading}
                error={auditError}
                onRefresh={refreshAudit}
              />
            </div>
          </div>
        )}
      </div>
      <Dialog
        open={publishDialogOpen}
        onClose={handleClosePublish}
        title="Опубликовать страницу"
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
          <p className="text-sm text-gray-600 dark:text-dark-200">
            После публикации текущий черновик станет новой опубликованной версией. История изменений позволит откатиться при необходимости.
          </p>
          {reviewStatus !== 'approved' && reviewStatus !== 'none' ? (
            <p className="text-xs text-amber-600 dark:text-amber-300">
              Текущий статус ревью: {reviewStatusLabel}. Убедитесь, что публикация согласована или зафиксируйте решение в комментарии.
            </p>
          ) : null}
          <Textarea
            label="Комментарий к публикации"
            placeholder="Коротко опишите, что изменилось в этой версии (необязательно)"
            rows={3}
            value={publishComment}
            onChange={(event) => setPublishComment(event.target.value)}
          />
        </div>
      </Dialog>
    </HomeEditorContext.Provider>
  );
}

export default function SitePageEditorContainer(): React.ReactElement | null {
  const params = useParams<{ pageId: string }>();
  if (!params.pageId) {
    return (
      <Card padding="lg">
        <div className="space-y-2 text-sm text-gray-600 dark:text-dark-200">
          <p>Страница не найдена. Вернитесь в каталог и выберите страницу для редактирования.</p>
          <Button as={Link} to="/management/site-editor" variant="ghost" size="sm">
            Вернуться в каталог
          </Button>
        </div>
      </Card>
    );
  }
  return <SitePageEditor pageId={params.pageId} />;
}

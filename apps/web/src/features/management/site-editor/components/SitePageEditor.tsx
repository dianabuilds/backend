import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { Button, Card, Dialog, Input, Spinner, Tabs, Textarea, useToast } from '@ui';
import { useAuth } from '@shared/auth';
import { managementSiteEditorApi } from '@shared/api/management';
import type { UpdateSitePagePayload } from '@shared/api/management/siteEditor/types';
import { reportFeatureError } from '@shared/utils/sentry';
import type { SitePagePreviewResponse, SitePageReviewStatus } from '@shared/types/management';
import { HomeEditorContext } from '../../home/HomeEditorContext';
import type { HomeEditorContextValue, HomeDraftData } from '../../home/types';
import { BlockCanvas } from '../../home/components/BlockCanvas';
import { BlockInspector } from '../../home/components/BlockInspector';
import { BlockLibraryPanel } from '../../home/components/BlockLibrary';
import {
  BlockPreviewPanel,
  extractRenderDataFromPayload,
  normalizePreviewPayload,
  type PreviewFetchResult,
  type PreviewErrorContext,
} from '../../editor-shared';
import { SitePageAuditPanel } from './PageAuditPanel';
import { useSitePageEditorState } from '../hooks/useSitePageEditorState';
import { statusAppearance, typeLabel } from '../utils/pageHelpers';
import { SitePageDiffPanel } from './SitePageDiffPanel';
import { SitePageMetricsPanel } from './SitePageMetricsPanel';
import { SitePageHeader } from './SitePageHeader';
import { SitePageReviewPanel } from './SitePageReviewPanel';
import { SitePageInfoPanel } from './SitePageInfoPanel';
import { SitePageHistoryPanel } from './PageHistoryPanel';

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

const SUPPORTED_LOCALES = ['ru', 'en'] as const;
const LOCALE_LABELS: Record<string, string> = {
  ru: 'Русский',
  en: 'Английский',
};

const KNOWN_ROLES = new Set(['user', 'editor', 'support', 'moderator', 'admin']);
const ROLE_ALIASES: Record<string, string> = {
  'site.viewer': 'user',
  'site.editor': 'editor',
  'site.publisher': 'editor',
  'site.reviewer': 'moderator',
  'site.admin': 'admin',
  'platform.admin': 'admin',
  'platform.moderator': 'moderator',
  'finance_ops': 'support',
};

function ErrorState({ message }: { message: string | null }): React.ReactElement | null {
  if (!message) return null;
  return (
    <Card padding="sm" className="border-rose-200 bg-rose-50 text-rose-700">
      {message}
    </Card>
  );
}

function buildSiteDraftPayload(data: HomeDraftData): {
  data: Record<string, unknown>;
  meta?: Record<string, unknown>;
} {
  const normalizedData: Record<string, unknown> = {
    blocks: Array.isArray(data.blocks) ? data.blocks : [],
  };
  const payload: { data: Record<string, unknown>; meta?: Record<string, unknown> } = {
    data: normalizedData,
  };

  if (data.meta && typeof data.meta === 'object' && data.meta !== null) {
    payload.meta = { ...data.meta };
  }

  return payload;
}

function mapPreviewResponseToResult(response: SitePagePreviewResponse): PreviewFetchResult {
  const layouts: PreviewFetchResult['layouts'] = {};
  const entries = Object.entries(response.layouts ?? {});

  for (const [layoutKey, layoutValue] of entries) {
    if (!layoutValue) {
      continue;
    }
    const rawPayload =
      layoutValue.payload && typeof layoutValue.payload === 'object'
        ? (layoutValue.payload as Record<string, unknown>)
        : null;
    const summarySource: Record<string, unknown> = rawPayload ? { ...rawPayload } : {};
    const rawData = layoutValue.data && typeof layoutValue.data === 'object' ? (layoutValue.data as Record<string, unknown>) : null;
    if (!rawPayload && rawData) {
      Object.assign(summarySource, rawData);
    }
    if (layoutValue.meta && typeof layoutValue.meta === 'object' && layoutValue.meta !== null) {
      summarySource.meta = layoutValue.meta;
    }
    if (layoutValue.generated_at) {
      summarySource.generated_at = layoutValue.generated_at;
    }
    if (response.draft_version != null) {
      summarySource.version = response.draft_version;
    }
    const summary = extractRenderDataFromPayload(summarySource);
    const normalizedPayload = rawPayload ? normalizePreviewPayload(rawPayload) : undefined;
    layouts[layoutKey] = {
      summary,
      payload: normalizedPayload,
    };
  }

  const defaultLayoutKey = entries[0]?.[0];
  const defaultGeneratedAt = entries[0]?.[1]?.generated_at ?? null;

  return {
    layouts,
    defaultLayout: defaultLayoutKey,
    meta: {
      version: response.draft_version ?? null,
      generatedAt: defaultGeneratedAt,
    },
  };
}

type SitePageEditorProps = {
  pageId: string;
};

export function SitePageEditor({ pageId }: SitePageEditorProps): React.ReactElement {
  const { pushToast } = useToast();
  const {
    page,
    loading,
    pageInfoSaving,
    pageInfoError,
    updatePageInfo,
    clearPageInfoError,
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
    draftDiff,
    diffLoading,
    diffError,
    refreshDiff,
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
    sharedBindings,
    sharedAssignments,
    setSharedAssignment,
    clearSharedAssignment,
    updateSharedBindingInfo,
    assignSharedBinding,
    removeSharedBinding,
    activeLocale,
    availableLocales,
    setActiveLocale: switchActiveLocale,
    createLocale,
  } = useSitePageEditorState({ pageId });
  const { user } = useAuth();
  const [publishDialogOpen, setPublishDialogOpen] = React.useState(false);
  const [publishComment, setPublishComment] = React.useState('');
  const [workspaceTab, setWorkspaceTab] = React.useState<'layout' | 'settings' | 'preview'>('layout');
  const [localeDialogOpen, setLocaleDialogOpen] = React.useState(false);
  const [newLocaleValue, setNewLocaleValue] = React.useState('');
  const [localeDialogError, setLocaleDialogError] = React.useState<string | null>(null);

  const localeTabs = React.useMemo(
    () =>
      availableLocales.map((locale) => ({
        key: locale,
        label: LOCALE_LABELS[locale] ?? locale.toUpperCase(),
      })),
    [availableLocales],
  );
  const canAddLocale = availableLocales.length < SUPPORTED_LOCALES.length;

  const fetchSitePreview = React.useCallback(
    async ({ layout, signal }: { layout?: string; signal: AbortSignal }): Promise<PreviewFetchResult> => {
      const payload = buildSiteDraftPayload(data);
      const response = await managementSiteEditorApi.previewSitePage(
        pageId,
        {
          data: payload.data,
          meta: payload.meta,
          layouts: layout ? [layout] : undefined,
          version: snapshot.version ?? undefined,
          locale: activeLocale,
        },
        { signal },
      );
      return mapPreviewResponseToResult(response);
    },
    [activeLocale, data, pageId, snapshot.version],
  );

  const handlePreviewError = React.useCallback(
    (error: unknown, context: PreviewErrorContext) => {
      const blockErrors = Object.values(context.summary.blocks).reduce(
        (acc, issues) => acc + issues.length,
        0,
      );
      reportFeatureError(error, 'site-page-preview', {
        pageId,
        slug,
        dirty: context.dirty,
        saving: context.saving,
        lastSavedAt: context.lastSavedAt,
        validationErrors: context.summary.general.length,
        blockErrors,
        layout: context.layout,
      });
    },
    [pageId, slug],
  );

const handleDiffRefresh = React.useCallback(() => {
  refreshDiff().catch(() => undefined);
}, [refreshDiff]);

const handleUpdatePageInfo = React.useCallback(
  async (changes: UpdateSitePagePayload) => {
    if (!Object.keys(changes).length) {
      return;
    }
    try {
      await updatePageInfo(changes);
      pushToast({ intent: 'success', description: 'Основные параметры страницы обновлены' });
    } catch {
      // Ошибка отображается в панели параметров
    }
  },
  [pushToast, updatePageInfo],
);

  const contextValue = React.useMemo<HomeEditorContextValue>(() => ({
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
    loadDraft,
    saveDraft,
    snapshot,
    slug,
    activeLocale,
    availableLocales,
    setActiveLocale: switchActiveLocale,
    createLocale,
    history: historyForContext,
    publishing,
    publishDraft,
    restoreVersion,
    restoringVersion,
    validation,
    revalidate,
    sharedBindings,
    sharedAssignments,
    setSharedAssignment,
    clearSharedAssignment,
    updateSharedBindingInfo,
    assignSharedBinding,
    removeSharedBinding,
  }), [
    activeLocale,
    availableLocales,
    assignSharedBinding,
    clearSharedAssignment,
    createLocale,
    data,
    dirty,
    historyForContext,
    lastSavedAt,
    loadDraft,
    page,
    publishDraft,
    publishing,
    revalidate,
    removeSharedBinding,
    restoreVersion,
    restoringVersion,
    saving,
    savingError,
    saveDraft,
    selectedBlockId,
    setBlocks,
    setData,
    switchActiveLocale,
    setSharedAssignment,
    selectBlock,
    sharedAssignments,
    sharedBindings,
    slug,
    snapshot,
    updateSharedBindingInfo,
    validation,
    loading,
  ]);

  const roles = React.useMemo(() => {
    const set = new Set<string>();
    const collect = (value: unknown) => {
      if (!value) return;
      const text = String(value).trim().toLowerCase();
      if (!text) return;
      const normalized = ROLE_ALIASES[text] ?? text;
      if (KNOWN_ROLES.has(normalized)) {
        set.add(normalized);
      }
    };
    if (Array.isArray(user?.roles)) {
      user.roles.forEach(collect);
    }
    collect(user?.role);
    return set;
  }, [user]);

  const canPublish = roles.has('editor') || roles.has('moderator') || roles.has('admin');

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

  const blocksCount = data.blocks.length;

  const workspaceTabs = React.useMemo(() => ([
    {
      key: 'layout',
      label: `Структура${blocksCount > 0 ? ` (${blocksCount})` : ''}`,
    },
    {
      key: 'settings',
      label: 'Параметры',
    },
    {
      key: 'preview',
      label: 'Предпросмотр',
    },
  ]), [blocksCount]);

  const handleWorkspaceTabChange = React.useCallback((key: string) => {
    if (key === 'preview') {
      setWorkspaceTab('preview');
      return;
    }
    if (key === 'settings') {
      setWorkspaceTab('settings');
      return;
    }
    setWorkspaceTab('layout');
  }, []);

  const handleLocaleTabChange = React.useCallback(
    (key: string) => {
      if (!key || key === activeLocale) {
        return;
      }
      switchActiveLocale(key);
    },
    [activeLocale, switchActiveLocale],
  );

  const handleCreateLocale = React.useCallback(() => {
    const normalized = newLocaleValue.trim().toLowerCase();
    if (!normalized) {
      setLocaleDialogError('Укажите код локали (например, ru или en)');
      return;
    }
    if (availableLocales.includes(normalized)) {
      setLocaleDialogError('Такая локаль уже добавлена');
      return;
    }
    if (!SUPPORTED_LOCALES.includes(normalized as typeof SUPPORTED_LOCALES[number])) {
      setLocaleDialogError('Поддерживаются локали ru и en');
      return;
    }
    if (!createLocale(normalized)) {
      setLocaleDialogError('Не удалось создать локаль');
      return;
    }
    switchActiveLocale(normalized);
    setLocaleDialogOpen(false);
    setNewLocaleValue('');
    setLocaleDialogError(null);
    pushToast({ intent: 'success', description: `Добавлена локаль ${normalized.toUpperCase()}` });
  }, [availableLocales, createLocale, newLocaleValue, pushToast, switchActiveLocale]);

  const handleOpenLocaleDialog = React.useCallback(() => {
    setLocaleDialogError(null);
    setNewLocaleValue('');
    setLocaleDialogOpen(true);
  }, []);

  const reviewStatusBadgeColor = REVIEW_STATUS_BADGE_COLOR[reviewStatus] ?? 'neutral';

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

  const status = page ? statusAppearance(page.status) : null;

  return (
    <HomeEditorContext.Provider value={contextValue}>
      <div className="space-y-6 pb-12">
        <SitePageHeader
          pageTitle={page?.title ?? 'Страница'}
          pageSlug={slug}
          activeLocale={activeLocale}
          pageStatusBadge={status ? { label: status.label, color: status.color } : null}
          pageTypeLabel={page?.type ? typeLabel(page.type) : null}
          snapshot={snapshot}
          publishedVersion={page?.published_version ?? null}
          lastSavedAt={lastSavedAt}
          dirty={dirty}
          saving={saving}
          publishing={publishing}
          loading={loading}
          canPublish={canPublish}
          onRefresh={() => void loadDraft({ silent: false })}
          onSaveDraft={handleManualSave}
          onOpenPublish={handleOpenPublish}
        />
        <Card className="rounded-3xl border border-white/60 bg-white/80 p-4 shadow-sm backdrop-blur dark:border-dark-600/60 dark:bg-dark-800/70">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-gray-900 dark:text-white">Локали страницы</h2>
              <p className="text-xs text-gray-500 dark:text-dark-200">
                Выберите локаль, с которой работает редактор. Добавьте новую, чтобы подготовить перевод.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              <Tabs items={localeTabs} value={activeLocale} onChange={handleLocaleTabChange} />
              <Button
                variant="ghost"
                color="neutral"
                size="sm"
                onClick={handleOpenLocaleDialog}
                disabled={!canAddLocale}
              >
                {canAddLocale ? 'Добавить локаль' : 'Все локали подключены'}
              </Button>
            </div>
          </div>
        </Card>

        <ErrorState message={savingError} />

        {loading ? (
          <Card padding="sm" className="flex items-center justify-center py-32">
            <Spinner />
          </Card>
        ) : (
          <div className="rounded-4xl border border-gray-100/70 bg-gray-50/80 p-4 shadow-inner dark:border-dark-700/70 dark:bg-dark-900/50 sm:p-5">
            <div className="grid gap-4 lg:grid-cols-[260px_minmax(260px,1fr)_360px]">
              <div className="order-2 space-y-4 lg:order-1">
                <BlockLibraryPanel />
              </div>
              <div className="order-1 min-w-0 space-y-4 lg:order-2">
                <div className="overflow-hidden rounded-2xl border border-white/80 bg-white/95 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
                  <Tabs items={workspaceTabs} value={workspaceTab} onChange={handleWorkspaceTabChange} className="px-4 pt-2" />
                </div>
                {workspaceTab === 'layout' ? (
                  <div className="rounded-3xl border border-white/80 bg-white/95 p-3 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
                    <BlockCanvas compact />
                  </div>
                ) : null}
                {workspaceTab === 'preview' ? (
                  <BlockPreviewPanel
                    loading={loading}
                    slug={slug}
                    dirty={dirty}
                    saving={saving}
                    lastSavedAt={lastSavedAt}
                    validation={validation}
                    revalidate={revalidate}
                    fetchPreview={fetchSitePreview}
                    locale={activeLocale}
                    title="Предпросмотр страницы"
                    description="Генерация payload для предпросмотра с учётом текущего черновика."
                    openWindowLabel="Открыть окно"
                    refreshLabel="Обновить предпросмотр"
                    className="bg-white/95 shadow-sm dark:bg-dark-800"
                    cardPadding="sm"
                    testIdPrefix="site-page-preview"
                    onError={handlePreviewError}
                  />
                ) : null}
                {workspaceTab === 'settings' ? (
                  <div className="space-y-4">
                    <SitePageInfoPanel
                      page={page}
                      pageSlug={slug}
                      activeLocale={activeLocale}
                      isDefaultLocale={activeLocale === (page?.default_locale ?? activeLocale)}
                      disabled={loading || saving || publishing}
                      saving={pageInfoSaving}
                      error={pageInfoError}
                      onSubmit={handleUpdatePageInfo}
                      onClearError={clearPageInfoError}
                    />
                  </div>
                ) : null}
              </div>
              <div className="order-3 space-y-4">
                <BlockInspector />
                <SitePageReviewPanel
                  status={reviewStatus}
                  statusLabel={reviewStatusLabel}
                  badgeColor={reviewStatusBadgeColor}
                  message={reviewStatusMessage}
                  hint={reviewStatusHint}
                  options={REVIEW_STATUS_OPTIONS}
                  disabled={publishing || saving || loading}
                  showSelfPublishBadge={canPublish}
                  onChange={setReviewStatus}
                />
                <details className="group rounded-2xl border border-gray-200/70 bg-white/95 text-gray-900 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/80 dark:text-dark-50 [&_summary::-webkit-details-marker]:hidden">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold">
                    <span>Метрики страницы</span>
                    <span className="text-xs text-primary-500 group-open:hidden">Развернуть</span>
                    <span className="hidden text-xs text-primary-500 group-open:block">Свернуть</span>
                  </summary>
                  <div className="border-t border-gray-100 px-4 py-4 dark:border-dark-700/60">
                    <SitePageMetricsPanel
                      metrics={pageMetrics}
                      loading={metricsLoading || loading}
                      error={metricsError}
                      period={metricsPeriod}
                      onChangePeriod={setMetricsPeriod}
                      onRefresh={refreshMetrics}
                      variant="flat"
                      showTitle={false}
                      className="space-y-4"
                    />
                  </div>
                </details>
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
          </div>
        )}
      </div>
      <Dialog
        open={localeDialogOpen}
        onClose={() => {
          if (!saving && !publishing) {
            setLocaleDialogOpen(false);
          }
        }}
        title="Добавление локали"
        footer={(
          <>
            <Button
              variant="outlined"
              color="neutral"
              onClick={() => setLocaleDialogOpen(false)}
              disabled={saving || publishing}
            >
              Отмена
            </Button>
            <Button onClick={handleCreateLocale} disabled={saving || publishing}>
              Добавить
            </Button>
          </>
        )}
      >
        <div className="space-y-3">
          <p className="text-sm text-gray-600 dark:text-dark-200">
            Укажите код локали (например, <code className="font-mono text-xs">ru</code> или <code className="font-mono text-xs">en</code>).
          </p>
          <Input
            value={newLocaleValue}
            onChange={(event) => {
              setNewLocaleValue(event.target.value);
              setLocaleDialogError(null);
            }}
            placeholder="ru"
          />
          {localeDialogError ? (
            <p className="text-sm text-rose-600 dark:text-rose-300">{localeDialogError}</p>
          ) : null}
        </div>
      </Dialog>

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

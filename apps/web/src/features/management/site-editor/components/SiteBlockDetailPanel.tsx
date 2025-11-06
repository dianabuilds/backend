import React from 'react';
import { AlertTriangle, ExternalLink } from '@icons';
import {
  Badge,
  Button,
  Card,
  Dialog,
  Input,
  Select,
  Spinner,
  Tabs,
  Textarea,
  useToast,
} from '@ui';
import { SharedHeaderLivePreview } from '@shared/site-editor/preview';
import { managementSiteEditorApi } from '@shared/api/management';
import type {
  SiteBlock,
  SiteBlockHistoryItem,
  SiteBlockUsage,
  SiteBlockWarning,
} from '@shared/types/management';
import type {
  PublishSiteBlockPayload,
  SaveSiteBlockPayload,
} from '@shared/api/management/siteEditor/types';
import { extractErrorMessage } from '@shared/utils/errors';
import { formatDateTime } from '@shared/utils/format';
import {
  HISTORY_PAGE_SIZE,
  REVIEW_STATUS_META,
  REVIEW_STATUS_OPTIONS,
  SCOPE_LABELS,
  STATUS_META,
} from './SiteBlockLibraryPage.constants';
import SiteBlockHeaderForm from './SiteBlockHeaderForm';
import { normalizeStringArray, parseStringList, sortStrings } from '../utils/blockHelpers';
import {
  collectLocales,
  isSameStringList,
  joinList,
  pickDocumentationUrl,
} from './SiteBlockLibrary.utils';
import type { DetailTab } from './SiteBlockLibrary.types';
import type { SiteHeaderConfig } from '../schemas/siteHeader';
import { ensureHeaderConfig, createDefaultHeaderConfig } from '../schemas/siteHeader';

type Props = {
  blockId: string | null;
  onBlockMutated: (block: SiteBlock) => void;
};

type DialogMode = 'archive' | 'restore';

function InfoField({ label, value }: { label: string; value: React.ReactNode }): React.ReactElement {
  return (
    <div className="space-y-1 rounded-xl bg-gray-50/80 px-3 py-2 dark:bg-dark-700/50">
      <div className="text-2xs font-semibold uppercase tracking-wide text-gray-400 dark:text-dark-300">
        {label}
      </div>
      <div className="text-xs text-gray-700 dark:text-dark-100">{value}</div>
    </div>
  );
}
export function SiteBlockDetailPanel({ blockId, onBlockMutated }: Props): React.ReactElement {
  const [detailBlock, setDetailBlock] = React.useState<SiteBlock | null>(null);
  const [detailUsage, setDetailUsage] = React.useState<SiteBlockUsage[]>([]);
  const [detailWarnings, setDetailWarnings] = React.useState<SiteBlockWarning[]>([]);
  const [detailLoading, setDetailLoading] = React.useState(false);
  const [detailError, setDetailError] = React.useState<string | null>(null);
  const [detailTab, setDetailTab] = React.useState<DetailTab>('overview');
  const [comment, setComment] = React.useState('');
  const [reviewStatus, setReviewStatus] = React.useState<SiteBlock['review_status']>('none');
  const [blockTitle, setBlockTitle] = React.useState('');
  const [blockSection, setBlockSection] = React.useState('');
  const [blockDefaultLocale, setBlockDefaultLocale] = React.useState('');
  const [blockLocalesText, setBlockLocalesText] = React.useState('');
  const [blockRequiresPublisher, setBlockRequiresPublisher] = React.useState(false);
  const [blockIsTemplate, setBlockIsTemplate] = React.useState(false);
  const [blockOriginBlockId, setBlockOriginBlockId] = React.useState('');
  const [headerConfig, setHeaderConfig] = React.useState<SiteHeaderConfig | null>(null);
  const [headerSnapshot, setHeaderSnapshot] = React.useState<string>(
    JSON.stringify(createDefaultHeaderConfig()),
  );
  const [headerPreviewTheme, setHeaderPreviewTheme] = React.useState<'light' | 'dark'>('light');
  const [headerPreviewDevice, setHeaderPreviewDevice] = React.useState<'desktop' | 'mobile'>('desktop');
  const [headerPreviewLocale, setHeaderPreviewLocale] = React.useState<string | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [saveError, setSaveError] = React.useState<string | null>(null);
  const [publishDialogOpen, setPublishDialogOpen] = React.useState(false);
  const [publishComment, setPublishComment] = React.useState('');
  const [publishing, setPublishing] = React.useState(false);
  const [publishError, setPublishError] = React.useState<string | null>(null);
  const [historyItems, setHistoryItems] = React.useState<SiteBlockHistoryItem[]>([]);
  const [historyTotal, setHistoryTotal] = React.useState(0);
  const [historyLoading, setHistoryLoading] = React.useState(false);
  const [historyLoadingMore, setHistoryLoadingMore] = React.useState(false);
  const [historyError, setHistoryError] = React.useState<string | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = React.useState(0);
  const [archiveDialogOpen, setArchiveDialogOpen] = React.useState(false);
  const [archiveMode, setArchiveMode] = React.useState<DialogMode>('archive');
  const [archiving, setArchiving] = React.useState(false);
  const [archiveError, setArchiveError] = React.useState<string | null>(null);
  const [restoreDialogOpen, setRestoreDialogOpen] = React.useState(false);
  const [restoreTarget, setRestoreTarget] = React.useState<SiteBlockHistoryItem | null>(null);
  const [restoreError, setRestoreError] = React.useState<string | null>(null);
  const [restoring, setRestoring] = React.useState(false);
  const [refreshToken, setRefreshToken] = React.useState(0);
  const { pushToast } = useToast();

  const hydrateDetail = React.useCallback(
    (block: SiteBlock, usage: SiteBlockUsage[] = [], warnings: SiteBlockWarning[] = []) => {
      setDetailBlock(block);
      setDetailUsage(Array.isArray(usage) ? usage : []);
      setDetailWarnings(Array.isArray(warnings) ? warnings : []);
      setComment(block.comment ?? '');
      setReviewStatus(block.review_status);
      setBlockTitle(block.title ?? '');
      setBlockSection(block.section ?? '');
      setBlockDefaultLocale(block.default_locale ?? '');
      const availableLocales = Array.isArray(block.available_locales)
        ? block.available_locales.filter(
            (value): value is string => typeof value === 'string' && value.trim().length > 0,
          )
        : [];
      setBlockLocalesText(joinList(availableLocales));
      setBlockRequiresPublisher(Boolean(block.requires_publisher));
      setBlockIsTemplate(Boolean(block.is_template));
      setBlockOriginBlockId(block.origin_block_id ?? '');
      if (block.section === 'header') {
        const config = ensureHeaderConfig(block.data ?? createDefaultHeaderConfig());
        setHeaderConfig(config);
        setHeaderSnapshot(JSON.stringify(config));
      } else {
        setHeaderConfig(null);
        setHeaderSnapshot(JSON.stringify(block.data ?? {}));
      }
    },
    [],
  );

  React.useEffect(() => {
    if (!blockId) {
      setDetailBlock(null);
      setDetailUsage([]);
      setDetailWarnings([]);
      setDetailError(null);
      return;
    }
    const controller = new AbortController();
    setDetailLoading(true);
    setDetailError(null);
    Promise.resolve(
      managementSiteEditorApi.fetchSiteBlock(blockId, { signal: controller.signal }),
    )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        if (response) {
          hydrateDetail(response.block, response.usage, response.warnings);
        }
      })
      .catch((err) => {
        if ((err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setDetailError(extractErrorMessage(err, 'Не удалось загрузить блок'));
        setDetailBlock(null);
        setDetailUsage([]);
        setDetailWarnings([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setDetailLoading(false);
        }
      });

    return () => controller.abort();
  }, [blockId, hydrateDetail, refreshToken]);

  React.useEffect(() => {
    if (!blockId) {
      setHistoryItems([]);
      setHistoryTotal(0);
      setHistoryError(null);
      setHistoryLoading(false);
      setHistoryLoadingMore(false);
      return;
    }
    const controller = new AbortController();
    setHistoryLoading(true);
    setHistoryLoadingMore(false);
    setHistoryError(null);
    setHistoryItems([]);
    Promise.resolve(
      managementSiteEditorApi.fetchSiteBlockHistory(
        blockId,
        { limit: HISTORY_PAGE_SIZE, offset: 0 },
        { signal: controller.signal },
      ),
    )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        const items = Array.isArray(response?.items) ? response.items : [];
        setHistoryItems(items);
        const total =
          typeof response?.total === 'number'
            ? response.total
            : Array.isArray(response?.items)
            ? response.items.length
            : 0;
        setHistoryTotal(total);
      })
      .catch((err) => {
        if ((err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setHistoryError(extractErrorMessage(err, 'Не удалось загрузить историю версий'));
        setHistoryItems([]);
        setHistoryTotal(0);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setHistoryLoading(false);
        }
      });

    return () => controller.abort();
  }, [blockId, historyRefreshKey, refreshToken]);

  React.useEffect(() => {
    if (!headerConfig) {
      if (headerPreviewLocale !== null) {
        setHeaderPreviewLocale(null);
      }
      return;
    }
    const locales = new Set<string>();
    const fallbackLocale = headerConfig.localization?.fallbackLocale;
    if (typeof fallbackLocale === 'string' && fallbackLocale.trim()) {
      locales.add(fallbackLocale.trim());
    }
    (headerConfig.localization?.available ?? [])
      .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
      .forEach((value) => locales.add(value.trim()));
    if (detailBlock) {
      collectLocales(detailBlock).forEach((locale) => locales.add(locale));
    }
    const list = Array.from(locales);
    if (list.length > 0) {
      const next = headerPreviewLocale && list.includes(headerPreviewLocale) ? headerPreviewLocale : list[0];
      if (next !== headerPreviewLocale) {
        setHeaderPreviewLocale(next);
      }
    } else {
      const fallback =
        (typeof headerConfig.localization?.fallbackLocale === 'string' &&
          headerConfig.localization?.fallbackLocale?.trim()) ||
        detailBlock?.locale ||
        detailBlock?.default_locale ||
        null;
      if (fallback !== headerPreviewLocale) {
        setHeaderPreviewLocale(fallback);
      }
    }
  }, [detailBlock, headerConfig, headerPreviewLocale]);

  React.useEffect(() => {
    setRestoreDialogOpen(false);
    setRestoreTarget(null);
    setRestoreError(null);
    setRestoring(false);
  }, [blockId]);

  React.useEffect(() => {
    setDetailTab('overview');
  }, [blockId]);

  React.useEffect(() => {
    if (blockIsTemplate) {
      setBlockOriginBlockId('');
    }
  }, [blockIsTemplate]);

  const resetDetail = React.useCallback(() => {
    setRefreshToken((value) => value + 1);
  }, []);
  const handleHistoryLoadMore = React.useCallback(async () => {
    if (!detailBlock || historyLoadingMore) {
      return;
    }
    if (historyItems.length >= historyTotal) {
      return;
    }
    setHistoryLoadingMore(true);
    setHistoryError(null);
    try {
      const response = await Promise.resolve(
        managementSiteEditorApi.fetchSiteBlockHistory(detailBlock.id, {
          limit: HISTORY_PAGE_SIZE,
          offset: historyItems.length,
        }),
      );
      const items = Array.isArray(response.items) ? response.items : [];
      setHistoryItems((prev) => [...prev, ...items]);
      if (typeof response.total === 'number') {
        setHistoryTotal(response.total);
      }
    } catch (err) {
      setHistoryError(extractErrorMessage(err, 'Не удалось загрузить историю версий'));
    } finally {
      setHistoryLoadingMore(false);
    }
  }, [detailBlock, historyItems.length, historyLoadingMore, historyTotal]);

  const openArchiveDialog = React.useCallback(
    (mode: DialogMode) => {
      if (!detailBlock) {
        return;
      }
      setArchiveMode(mode);
      setArchiveError(null);
      setArchiveDialogOpen(true);
    },
    [detailBlock],
  );

  const closeArchiveDialog = React.useCallback(() => {
    if (archiving) {
      return;
    }
    setArchiveDialogOpen(false);
    setArchiveError(null);
  }, [archiving]);

  const handleArchiveConfirm = React.useCallback(async () => {
    if (!detailBlock) {
      return;
    }
    setArchiving(true);
    setArchiveError(null);
    try {
      const response = await managementSiteEditorApi.archiveSiteBlock(detailBlock.id, {
        restore: archiveMode === 'restore',
      });
      hydrateDetail(response.block, response.usage, response.warnings);
      onBlockMutated(response.block);
      pushToast({
        intent: 'success',
        description:
          archiveMode === 'restore' ? 'Блок восстановлен из архива' : 'Блок отправлен в архив',
      });
      setArchiveDialogOpen(false);
    } catch (err) {
      setArchiveError(extractErrorMessage(err, 'Не удалось обновить статус блока'));
    } finally {
      setArchiving(false);
    }
  }, [archiveMode, detailBlock, hydrateDetail, onBlockMutated, pushToast]);

  const openRestoreDialog = React.useCallback((item: SiteBlockHistoryItem) => {
    setRestoreTarget(item);
    setRestoreError(null);
    setRestoreDialogOpen(true);
  }, []);

  const closeRestoreDialog = React.useCallback(() => {
    if (restoring) {
      return;
    }
    setRestoreDialogOpen(false);
    setRestoreTarget(null);
    setRestoreError(null);
  }, [restoring]);

  const handleRestoreConfirm = React.useCallback(async () => {
    if (!detailBlock || !restoreTarget) {
      return;
    }
    setRestoring(true);
    setRestoreError(null);
    try {
      const response = await managementSiteEditorApi.restoreSiteBlockVersion(
        detailBlock.id,
        restoreTarget.version,
      );
      hydrateDetail(response.block, response.usage, response.warnings);
      onBlockMutated(response.block);
      setHistoryRefreshKey((value) => value + 1);
      pushToast({
        intent: 'success',
        description: `Версия ${restoreTarget.version} восстановлена`,
      });
      setRestoreDialogOpen(false);
      setRestoreTarget(null);
    } catch (err) {
      setRestoreError(extractErrorMessage(err, 'Не удалось восстановить версию'));
    } finally {
      setRestoring(false);
    }
  }, [detailBlock, hydrateDetail, onBlockMutated, pushToast, restoreTarget]);

  const closePublishDialog = React.useCallback(() => {
    if (publishing) {
      return;
    }
    setPublishDialogOpen(false);
    setPublishComment('');
    setPublishError(null);
  }, [publishing]);

  const headerAvailableLocales = React.useMemo(() => {
    if (!headerConfig) {
      return [];
    }
    const locales = new Set<string>();
    const fallbackLocale = headerConfig.localization?.fallbackLocale;
    if (typeof fallbackLocale === 'string' && fallbackLocale.trim()) {
      locales.add(fallbackLocale.trim());
    }
    (headerConfig.localization?.available ?? [])
      .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
      .forEach((value) => locales.add(value.trim()));
    if (detailBlock) {
      collectLocales(detailBlock).forEach((locale) => locales.add(locale));
    }
    return Array.from(locales);
  }, [detailBlock, headerConfig]);

  const headerPreviewLocaleOptions = React.useMemo(() => {
    if (headerAvailableLocales.length > 0) {
      return headerAvailableLocales;
    }
    return headerPreviewLocale ? [headerPreviewLocale] : [];
  }, [headerAvailableLocales, headerPreviewLocale]);

  const normalizedAvailableLocales = React.useMemo(
    () =>
      sortStrings(
        normalizeStringArray(parseStringList(blockLocalesText).map((locale) => locale.toLowerCase())),
      ),
    [blockLocalesText],
  );

  const currentAvailableLocales = React.useMemo(() => {
    if (!detailBlock) {
      return [];
    }
    return sortStrings(
      normalizeStringArray(
        (Array.isArray(detailBlock.available_locales) ? detailBlock.available_locales : []).map(
          (locale) => (typeof locale === 'string' ? locale.toLowerCase() : ''),
        ),
      ),
    );
  }, [detailBlock]);

  const handlePublish = React.useCallback(async () => {
    if (!detailBlock) {
      return;
    }
    setPublishing(true);
    setPublishError(null);
    try {
      const payload: PublishSiteBlockPayload =
        publishComment.trim().length > 0 ? { comment: publishComment.trim() } : {};
      const response = await managementSiteEditorApi.publishSiteBlock(detailBlock.id, payload);
      hydrateDetail(response.block, response.usage, detailWarnings);
      onBlockMutated(response.block);
      setPublishDialogOpen(false);
      setPublishComment('');
      pushToast({ intent: 'success', description: 'Блок опубликован' });
      setHistoryRefreshKey((value) => value + 1);
    } catch (err) {
      setPublishError(extractErrorMessage(err, 'Не удалось опубликовать блок'));
    } finally {
      setPublishing(false);
    }
  }, [detailBlock, detailWarnings, hydrateDetail, onBlockMutated, publishComment, pushToast]);

  const handleSave = React.useCallback(async () => {
    if (!detailBlock) {
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const baseMeta =
        detailBlock.meta && typeof detailBlock.meta === 'object' && !Array.isArray(detailBlock.meta)
          ? { ...detailBlock.meta }
          : {};
      if ('library' in baseMeta) {
        delete (baseMeta as Record<string, unknown>).library;
      }
      const normalizedTitle = blockTitle.trim() || detailBlock.title || detailBlock.key;
      const normalizedSection = blockSection.trim() || detailBlock.section || 'general';
      const normalizedDefaultLocale = blockDefaultLocale.trim() || detailBlock.default_locale || null;
      const currentVersion =
        typeof detailBlock.version === 'number'
          ? detailBlock.version
          : detailBlock.draft_version ?? detailBlock.published_version ?? 0;
      const normalizedOriginBlock = blockOriginBlockId.trim();
      const payload: SaveSiteBlockPayload = {
        data: headerConfig ? headerConfig : detailBlock.data ?? {},
        comment: comment.trim(),
        review_status: reviewStatus,
        title: normalizedTitle,
        section: normalizedSection,
        default_locale: normalizedDefaultLocale,
        available_locales: normalizedAvailableLocales,
        requires_publisher: blockRequiresPublisher,
        version: currentVersion,
        is_template: blockIsTemplate,
        origin_block_id: normalizedOriginBlock ? normalizedOriginBlock : null,
      };
      if (Object.keys(baseMeta).length > 0) {
        payload.meta = baseMeta;
      }
      const updated = await managementSiteEditorApi.saveSiteBlock(detailBlock.id, payload);
      hydrateDetail(updated, detailUsage, detailWarnings);
      onBlockMutated(updated);
      pushToast({ intent: 'success', description: 'Блок сохранён' });
    } catch (err) {
      setSaveError(extractErrorMessage(err, 'Не удалось сохранить блок'));
    } finally {
      setSaving(false);
    }
  }, [
    blockDefaultLocale,
    blockIsTemplate,
    blockLocalesText,
    normalizedAvailableLocales,
    blockOriginBlockId,
    blockRequiresPublisher,
    blockSection,
    blockTitle,
    comment,
    detailBlock,
    detailUsage,
    detailWarnings,
    headerConfig,
    hydrateDetail,
    onBlockMutated,
    pushToast,
    reviewStatus,
    normalizedAvailableLocales,
  ]);

  const commentDirty = detailBlock ? comment.trim() !== (detailBlock.comment ?? '') : false;
  const reviewDirty = detailBlock ? reviewStatus !== detailBlock.review_status : false;
  const isHeaderBlock = Boolean(headerConfig);
  const headerDirty = headerConfig ? JSON.stringify(headerConfig) !== headerSnapshot : false;
  const baseInfoDirty = detailBlock
    ? blockTitle.trim() !== (detailBlock.title ?? '') ||
      blockSection.trim() !== (detailBlock.section ?? '') ||
      (blockDefaultLocale.trim() || '') !== (detailBlock.default_locale ?? '') ||
      !isSameStringList(normalizedAvailableLocales, currentAvailableLocales) ||
      blockRequiresPublisher !== Boolean(detailBlock.requires_publisher) ||
      blockIsTemplate !== Boolean(detailBlock.is_template) ||
      (blockOriginBlockId.trim() || '') !== (detailBlock.origin_block_id ?? '')
    : false;

  const canSave = Boolean(detailBlock) && (headerDirty || commentDirty || reviewDirty || baseInfoDirty);
  const canPublish =
    Boolean(detailBlock?.draft_version) && detailBlock?.status !== 'archived' && !detailBlock?.is_template;
  const historyHasMore = historyItems.length < historyTotal;
  const isArchived = detailBlock?.status === 'archived';
  return (
    <div className="space-y-4" data-testid="site-block-library-detail">
      <Card className="space-y-3 border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-300">
              {detailBlock ? detailBlock.section || 'Без секции' : 'Блок не выбран'}
            </div>
            <div className="text-xl font-semibold text-gray-900 dark:text-white">
              {detailBlock ? detailBlock.title : 'Выберите блок из списка'}
            </div>
            {detailBlock ? (
              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
                <span className="rounded-md bg-gray-100 px-2 py-1 font-mono dark:bg-dark-700/60">
                  {detailBlock.key}
                </span>
                <span>{SCOPE_LABELS[detailBlock.scope ?? 'unknown'] ?? detailBlock.scope ?? '—'}</span>
                <span>
                  Версия: {detailBlock.version ?? detailBlock.draft_version ?? detailBlock.published_version ?? '—'}
                </span>
                {detailBlock.is_template ? (
                  <Badge color="neutral" variant="soft">
                    Шаблон
                  </Badge>
                ) : null}
                {detailBlock.origin_block_id ? (
                  <Badge color="neutral" variant="outline">
                    Основан на {detailBlock.origin_block_id}
                  </Badge>
                ) : null}
                <span>
                  Обновлён: {formatDateTime(detailBlock.updated_at, { fallback: '—' })}
                </span>
                <span>Автор: {detailBlock.updated_by ?? '—'}</span>
              </div>
            ) : null}
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="flex flex-wrap items-center gap-2">
              {detailBlock ? (
                <>
                  <Badge color={STATUS_META[detailBlock.status].color} variant="soft">
                    {STATUS_META[detailBlock.status].label}
                  </Badge>
                  <Badge color={REVIEW_STATUS_META[detailBlock.review_status].color} variant="outline">
                    {REVIEW_STATUS_META[detailBlock.review_status].label}
                  </Badge>
                </>
              ) : null}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="ghost" color="neutral" size="sm" onClick={resetDetail} disabled={detailLoading}>
                {detailLoading ? 'Обновляем…' : 'Обновить'}
              </Button>
              {detailBlock ? (
                <Button
                  variant="ghost"
                  color={isArchived ? 'primary' : 'error'}
                  size="sm"
                  onClick={() => openArchiveDialog(isArchived ? 'restore' : 'archive')}
                >
                  {isArchived ? 'Вернуть из архива' : 'В архив'}
                </Button>
              ) : null}
            </div>
          </div>
        </div>
        {detailError ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
            {detailError}
          </div>
        ) : null}
        {!detailBlock && !detailLoading ? (
          <div className="text-sm text-gray-600 dark:text-dark-200">
            Выберите блок из списка слева, чтобы увидеть детали и редактировать его.
          </div>
        ) : null}
        {detailLoading ? (
          <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-dark-200">
            <Spinner className="h-4 w-4" /> Загружаем блок…
          </div>
        ) : null}
      </Card>

      {detailBlock ? (
        <Card className="space-y-3 border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Tabs
              value={detailTab}
              onChange={(key) => setDetailTab(key as DetailTab)}
              items={[
                { key: 'overview', label: 'Сводка' },
                { key: 'settings', label: 'Настройки' },
                ...(isHeaderBlock ? [{ key: 'preview', label: 'Предпросмотр' }] : []),
                { key: 'history', label: 'История' },
                {
                  key: 'usage',
                  label: detailUsage.length ? `Использование (${detailUsage.length})` : 'Использование',
                },
                {
                  key: 'warnings',
                  label: detailWarnings.length ? `Предупреждения (${detailWarnings.length})` : 'Предупреждения',
                },
              ]}
            />
            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={handleSave} disabled={!canSave || saving}>
                {saving ? 'Сохраняем…' : 'Сохранить'}
              </Button>
              <Button
                variant="outlined"
                color="primary"
                disabled={!canPublish || publishing}
                onClick={() => setPublishDialogOpen(true)}
              >
                Опубликовать
              </Button>
            </div>
          </div>
          {detailTab === 'overview' ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-3">
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-1">
                    <label htmlFor="block-title" className="text-xs font-semibold text-gray-600 dark:text-dark-200">
                      Название
                    </label>
                    <Input
                      id="block-title"
                      value={blockTitle}
                      onChange={(event) => setBlockTitle(event.target.value)}
                      disabled={saving || publishing}
                    />
                  </div>
                  <div className="space-y-1">
                    <label
                      htmlFor="block-section"
                      className="text-xs font-semibold text-gray-600 dark:text-dark-200"
                    >
                      Секция
                    </label>
                    <Input
                      id="block-section"
                      value={blockSection}
                      onChange={(event) => setBlockSection(event.target.value)}
                      disabled={saving || publishing}
                    />
                  </div>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="space-y-1">
                    <label
                      htmlFor="block-default-locale"
                      className="text-xs font-semibold text-gray-600 dark:text-dark-200"
                    >
                      Базовая локаль
                    </label>
                    <Input
                      id="block-default-locale"
                      value={blockDefaultLocale}
                      onChange={(event) => setBlockDefaultLocale(event.target.value)}
                      disabled={saving || publishing}
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
                      Дополнительные локали
                    </label>
                    <Textarea
                      rows={4}
                      value={blockLocalesText}
                      onChange={(event) => setBlockLocalesText(event.target.value)}
                      disabled={saving || publishing}
                    />
                    <div className="text-2xs text-gray-500 dark:text-dark-300">
                      Вводите локали построчно или через запятую.
                    </div>
                  </div>
                </div>
                <div className="space-y-3 rounded-xl border border-dashed border-gray-200 p-4 dark:border-dark-600">
                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
                        Требует publisher
                      </label>
                      <Select
                        value={blockRequiresPublisher ? 'true' : 'false'}
                        onChange={(event) => setBlockRequiresPublisher(event.target.value === 'true')}
                        disabled={saving || publishing}
                      >
                        <option value="false">Нет</option>
                        <option value="true">Да</option>
                      </Select>
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">Тип</label>
                      <Select
                        value={blockIsTemplate ? 'template' : 'instance'}
                        onChange={(event) => setBlockIsTemplate(event.target.value === 'template')}
                        disabled={saving || publishing}
                      >
                        <option value="instance">Обычный блок</option>
                        <option value="template">Шаблон</option>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
                      Родительский блок
                    </label>
                    <Input
                      value={blockOriginBlockId}
                      onChange={(event) => setBlockOriginBlockId(event.target.value)}
                      disabled={saving || publishing || blockIsTemplate}
                      placeholder="ID шаблона, если блок создан на его основе"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
                    Комментарий
                  </label>
                  <Textarea
                    rows={3}
                    value={comment}
                    onChange={(event) => setComment(event.target.value)}
                    disabled={saving || publishing}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
                    Статус ревью
                  </label>
                  <Select
                    value={reviewStatus}
                    onChange={(event) => setReviewStatus(event.target.value as SiteBlock['review_status'])}
                    disabled={saving || publishing}
                  >
                    {REVIEW_STATUS_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </Select>
                </div>
              </div>

              <div className="space-y-3">
                <div className="grid gap-3 md:grid-cols-2">
                  <InfoField
                    label="Черновик"
                    value={detailBlock.draft_version ? `v${detailBlock.draft_version}` : '—'}
                  />
                  <InfoField
                    label="Опубликовано"
                    value={detailBlock.published_version ? `v${detailBlock.published_version}` : '—'}
                  />
                  <InfoField label="Обновил" value={detailBlock.updated_by ?? '—'} />
                  <InfoField label="Создал" value={detailBlock.created_by ?? '—'} />
                  <InfoField
                    label="Создан"
                    value={formatDateTime(detailBlock.created_at, { fallback: '—' })}
                  />
                  <InfoField
                    label="Последнее использование"
                    value={detailBlock.last_used_at ? formatDateTime(detailBlock.last_used_at) : '—'}
                  />
                </div>
                {detailWarnings.length ? (
                  <div className="space-y-2 rounded-xl border border-amber-300 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-100">
                    <div className="flex items-center gap-2 font-semibold">
                      <AlertTriangle className="h-4 w-4" />
                      Есть предупреждения
                    </div>
                    <ul className="list-disc space-y-1 pl-5">
                      {detailWarnings.map((warning) => (
                        <li key={warning.code}>
                          <span className="font-semibold">{warning.title ?? warning.code}:</span>{' '}
                          {warning.message ?? '—'}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {pickDocumentationUrl(detailBlock) ? (
                  <Button
                    as="a"
                    href={pickDocumentationUrl(detailBlock) ?? '#'}
                    target="_blank"
                    rel="noreferrer"
                    variant="outlined"
                    color="neutral"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <ExternalLink className="h-4 w-4" />
                    Документация
                  </Button>
                ) : null}
                {saveError ? (
                  <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
                    {saveError}
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}
          {detailTab === 'settings' ? (
            <Card className="space-y-4 border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
              <div>
                <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Данные блока</h3>
                <p className="text-xs text-gray-500 dark:text-dark-300">
                  Здесь отражается структура данных текущего блока. Для заголовка доступно редактирование
                  через форму ниже, для остальных блоков — через API.
                </p>
              </div>
              {isHeaderBlock && headerConfig ? (
                <SiteBlockHeaderForm
                  value={headerConfig}
                  onChange={setHeaderConfig}
                  disabled={saving || publishing}
                />
              ) : (
                <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 p-4 text-sm text-gray-500 dark:border-dark-600 dark:bg-dark-900/40 dark:text-dark-200">
                  Данные для этого блока редактируются через API. Сохранение обновит черновик в библиотеке.
                </div>
              )}
            </Card>
          ) : null}

          {detailTab === 'preview' && detailBlock && isHeaderBlock ? (
            <Card className="space-y-4 border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Живой предпросмотр</h3>
                  <p className="text-xs text-gray-500 dark:text-dark-300">
                    Настраивайте визуальные параметры и проверяйте, как блок выглядит в разных режимах.
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Select
                    value={headerPreviewDevice}
                    onChange={(event) =>
                      setHeaderPreviewDevice(event.target.value as 'desktop' | 'mobile')
                    }
                  >
                    <option value="desktop">Desktop</option>
                    <option value="mobile">Mobile</option>
                  </Select>
                  <Select
                    value={headerPreviewTheme}
                    onChange={(event) => setHeaderPreviewTheme(event.target.value as 'light' | 'dark')}
                  >
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                  </Select>
                  <Select
                    value={headerPreviewLocale ?? ''}
                    onChange={(event) => setHeaderPreviewLocale(event.target.value || null)}
                  >
                    {headerPreviewLocaleOptions.map((locale) => (
                      <option key={locale} value={locale}>
                        {locale.toUpperCase()}
                      </option>
                    ))}
                  </Select>
                </div>
              </div>
              <SharedHeaderLivePreview
                config={headerConfig ?? ensureHeaderConfig(detailBlock.data ?? {})}
                device={headerPreviewDevice}
                theme={headerPreviewTheme}
                locale={headerPreviewLocale ?? detailBlock.default_locale ?? 'ru'}
              />
            </Card>
          ) : null}
          {detailTab === 'history' ? (
            <Card className="space-y-3 border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">История версий</h3>
              </div>
              {historyError ? (
                <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
                  {historyError}
                </div>
              ) : null}
              {historyLoading ? (
                <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-300">
                  <Spinner className="h-4 w-4" /> Загружаем историю…
                </div>
              ) : null}
              {!historyLoading && !historyItems.length ? (
                <div className="text-xs text-gray-500 dark:text-dark-300">Версии пока не созданы.</div>
              ) : null}
              <ul className="space-y-2 text-xs text-gray-600 dark:text-dark-200">
                {historyItems.map((item) => {
                  const isCurrentDraft = detailBlock?.draft_version === item.version;
                  const isPublishedVersion = detailBlock?.published_version === item.version;
                  const publishedLabel = item.published_at
                    ? `Опубликовано ${formatDateTime(item.published_at)}`
                    : `Создано ${formatDateTime(item.created_at)}`;
                  const buttonLabel = isPublishedVersion ? 'Сделать черновиком' : 'Восстановить';
                  return (
                    <li
                      key={`${item.version}-${item.created_at}`}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-gray-200 p-3 dark:border-dark-600"
                    >
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <div className="text-sm font-semibold text-gray-800 dark:text-dark-100">
                            Версия {item.version}
                          </div>
                          {isCurrentDraft ? (
                            <Badge color="primary" variant="soft">
                              Текущая
                            </Badge>
                          ) : null}
                          {item.published_at ? (
                            <Badge color={isPublishedVersion ? 'success' : 'neutral'} variant="outline">
                              {isPublishedVersion ? 'В продакшене' : 'Опубликована'}
                            </Badge>
                          ) : (
                            <Badge color="warning" variant="outline">
                              Черновик
                            </Badge>
                          )}
                        </div>
                        <div className="text-[11px] text-gray-500 dark:text-dark-300">{publishedLabel}</div>
                        {item.comment ? (
                          <div className="text-xs text-gray-700 dark:text-dark-100">«{item.comment}»</div>
                        ) : null}
                      </div>
                      {!isCurrentDraft ? (
                        <Button size="xs" variant="outlined" onClick={() => openRestoreDialog(item)} disabled={restoring}>
                          {buttonLabel}
                        </Button>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
              {historyHasMore ? (
                <Button
                  variant="ghost"
                  color="neutral"
                  size="xs"
                  onClick={handleHistoryLoadMore}
                  disabled={historyLoadingMore || restoring}
                >
                  {historyLoadingMore ? 'Загружаем…' : 'Показать ещё'}
                </Button>
              ) : null}
            </Card>
          ) : null}

          {detailTab === 'usage' ? (
            <Card className="space-y-3 border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
              <div className="text-sm font-semibold text-gray-900 dark:text-dark-50">Использование блока</div>
              {detailUsage.length ? (
                <ul className="space-y-2 text-xs text-gray-600 dark:text-dark-200">
                  {detailUsage.map((usage) => (
                    <li
                      key={`${usage.page_id}-${usage.locale ?? 'default'}-${usage.section}`}
                      className="rounded-lg border border-gray-200 p-3 dark:border-dark-600"
                    >
                      <div className="font-semibold text-gray-800 dark:text-dark-100">{usage.title}</div>
                      <div className="flex flex-wrap gap-2">
                        <span className="font-mono text-[11px] text-gray-500 dark:text-dark-300">
                          {usage.slug}
                        </span>
                        <span>{usage.section || '—'}</span>
                        <span>{usage.locale || usage.default_locale || '—'}</span>
                        <span>{usage.status_label || usage.status || '—'}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-xs text-gray-500 dark:text-dark-300">
                  Пока ни одна страница не использует этот блок.
                </div>
              )}
            </Card>
          ) : null}

          {detailTab === 'warnings' ? (
            <Card className="space-y-3 border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
              <div className="text-sm font-semibold text-gray-900 dark:text-dark-50">Предупреждения</div>
              {detailWarnings.length ? (
                <ul className="space-y-2 text-xs text-gray-600 dark:text-dark-200">
                  {detailWarnings.map((warning) => (
                    <li
                      key={warning.code}
                      className="rounded-lg border border-amber-300 bg-amber-50 p-3 dark:border-amber-500/30 dark:bg-amber-500/10"
                    >
                      <div className="font-semibold text-amber-900 dark:text-amber-100">
                        {warning.title ?? warning.code}
                      </div>
                      <div className="text-amber-800 dark:text-amber-100/80">{warning.message ?? '—'}</div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-xs text-gray-500 dark:text-dark-300">
                  Для этого блока нет активных предупреждений.
                </div>
              )}
            </Card>
          ) : null}
        </Card>
      ) : null}
      <Dialog
        open={publishDialogOpen}
        onClose={closePublishDialog}
        title="Публикация блока"
        footer={
          <>
            <Button variant="outlined" color="neutral" onClick={closePublishDialog} disabled={publishing}>
              Отмена
            </Button>
            <Button onClick={handlePublish} disabled={publishing}>
              {publishing ? 'Публикуем…' : 'Опубликовать'}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-sm text-gray-600 dark:text-dark-200">
            Блок будет опубликован и обновит страницы, где он используется. Оставьте комментарий, чтобы зафиксировать изменения.
          </p>
          <Textarea
            rows={3}
            value={publishComment}
            onChange={(event) => setPublishComment(event.target.value)}
            placeholder="Комментарий к публикации"
          />
          {publishError ? (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
              {publishError}
            </div>
          ) : null}
        </div>
      </Dialog>

      <Dialog
        open={archiveDialogOpen}
        onClose={closeArchiveDialog}
        title={archiveMode === 'restore' ? 'Восстановить блок из архива' : 'Отправить блок в архив'}
        footer={
          <>
            <Button variant="outlined" color="neutral" onClick={closeArchiveDialog} disabled={archiving}>
              Отмена
            </Button>
            <Button onClick={handleArchiveConfirm} disabled={archiving}>
              {archiving ? 'Применяем…' : archiveMode === 'restore' ? 'Восстановить' : 'В архив'}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-sm text-gray-600 dark:text-dark-200">
            {archiveMode === 'restore'
              ? 'Блок снова станет доступен редакторам и вернётся в публикации.'
              : 'Блок исчезнет из публикаций, но останется в истории. Можно будет вернуть позже.'}
          </p>
          {archiveError ? (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
              {archiveError}
            </div>
          ) : null}
        </div>
      </Dialog>

      <Dialog
        open={restoreDialogOpen}
        onClose={closeRestoreDialog}
        title="Восстановление версии"
        footer={
          <>
            <Button variant="outlined" color="neutral" onClick={closeRestoreDialog} disabled={restoring}>
              Отмена
            </Button>
            <Button onClick={handleRestoreConfirm} disabled={restoring || !restoreTarget}>
              {restoring ? 'Восстанавливаем…' : 'Вернуть'}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-sm text-gray-600 dark:text-dark-200">
            {restoreTarget
              ? `Версия ${restoreTarget.version} станет текущим черновиком блока. Публикацию можно выполнить отдельно.`
              : 'Выберите версию, чтобы восстановить её как текущий черновик.'}
          </p>
          {restoreTarget?.comment ? (
            <div className="space-y-1 rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-600 dark:border-dark-600 dark:bg-dark-900/40 dark:text-dark-200">
              <div className="font-semibold text-gray-800 dark:text-dark-100">Комментарий</div>
              <div>{restoreTarget.comment}</div>
            </div>
          ) : null}
          {restoreError ? (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
              {restoreError}
            </div>
          ) : null}
        </div>
      </Dialog>
    </div>
  );
}

export default SiteBlockDetailPanel;

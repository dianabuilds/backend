import React from 'react';
import { AlertTriangle } from '@icons';
import { Badge, Button, Card, Dialog, Input, Select, Spinner, Tabs, TagInput, Textarea, useToast } from '@ui';
import { SharedHeaderLivePreview, HeroBlockPreview } from '@shared/site-editor/preview';
import { managementSiteEditorApi } from '@shared/api/management';
import { ApiRequestError } from '@shared/api/client/base';
import { ensureArray, isObjectRecord, pickString } from '@shared/api/management/utils';
import { normalizeBlockUsage } from '@shared/api/management/siteEditor/normalizers';
import type { SiteBlock, SiteBlockHistoryItem, SiteBlockUsage } from '@shared/types/management';
import type {
  PublishSiteBlockPayload,
  SaveSiteBlockPayload,
} from '@shared/api/management/siteEditor/types';
import { extractErrorMessage } from '@shared/utils/errors';
import { formatDateTime } from '@shared/utils/format';
import { REVIEW_STATUS_OPTIONS } from './SiteBlockLibraryPage.constants';
import SiteBlockHeaderForm from './SiteBlockHeaderForm';
import SiteBlockHeroForm from './SiteBlockHeroForm';
import SiteBlockFooterForm from './SiteBlockFooterForm';
import { normalizeStringArray, sortStrings } from '../utils/blockHelpers';
import { collectLocales, isSameStringList, pickDocumentationUrl } from './SiteBlockLibrary.utils';
import type { DetailTab } from './SiteBlockLibrary.types';
import type { SiteHeaderConfig } from '../schemas/siteHeader';
import { ensureHeaderConfig, createDefaultHeaderConfig } from '../schemas/siteHeader';
import {
  ensureHeroConfig,
  createDefaultHeroLocale,
  type HeroBlockConfig,
} from '@shared/site-editor/schemas/heroBlock';
import { ensureFooterConfig, type FooterConfig } from '../schemas/footerBlock';
import { useSiteBlockDetail } from '../hooks/useSiteBlockDetail';
import SiteBlockDetailHeader from './SiteBlockDetailHeader';

type Props = {
  blockId: string | null;
  onBlockMutated: (block: SiteBlock) => void;
};

type DialogMode = 'archive' | 'restore';

const KNOWN_LOCALES = ['ru', 'en'] as const;

function hasMenuContent(group?: SiteHeaderConfig['navigation']['primary']): boolean {
  if (!Array.isArray(group)) {
    return false;
  }
  return group.some((item) => {
    const selfContent = item.label.trim().length > 0 || item.href.trim().length > 0;
    const childContent = Array.isArray(item.children) && item.children.length > 0;
    return selfContent || childContent;
  });
}

function normalizeHeaderConfig(raw: unknown): SiteHeaderConfig {
  const ensured = ensureHeaderConfig(raw);
  const branding = ensured.branding;
  const brandingHasContent =
    branding.title.trim().length > 0 ||
    (typeof branding.subtitle === 'string' && branding.subtitle.trim().length > 0) ||
    branding.href.trim().length > 0 ||
    (branding.logo?.light ?? '').trim().length > 0 ||
    (branding.logo?.dark ?? '').trim().length > 0;

  const navigation = ensured.navigation;
  const menuHasContent =
    hasMenuContent(navigation.primary) ||
    hasMenuContent(navigation.secondary) ||
    hasMenuContent(navigation.utility) ||
    hasMenuContent(navigation.mobile?.menu);

  const desktopCta = navigation.cta;
  const desktopCtaHasContent =
    desktopCta != null &&
    ((desktopCta.label ?? '').trim().length > 0 || (desktopCta.href ?? '').trim().length > 0);

  const mobileCta = navigation.mobile?.cta ?? null;
  const mobileCtaHasContent =
    mobileCta != null &&
    ((mobileCta.label ?? '').trim().length > 0 || (mobileCta.href ?? '').trim().length > 0);

  if (brandingHasContent || menuHasContent || desktopCtaHasContent || mobileCtaHasContent) {
    return ensured;
  }
  return createDefaultHeaderConfig();
}
export function SiteBlockDetailPanel({ blockId, onBlockMutated }: Props): React.ReactElement {
  const {
    block: detailBlock,
    usage: detailUsage,
    warnings: detailWarnings,
    loading: detailLoading,
    error: detailError,
    refresh: refreshDetail,
    mutate: mutateDetail,
    history,
  } = useSiteBlockDetail(blockId);
  const [detailTab, setDetailTab] = React.useState<DetailTab>('overview');
  const prevBlockIdRef = React.useRef<string | null>(null);
  const [comment, setComment] = React.useState('');
  const [reviewStatus, setReviewStatus] = React.useState<SiteBlock['review_status']>('none');
  const [blockTitle, setBlockTitle] = React.useState('');
  const [blockSection, setBlockSection] = React.useState('');
  const [blockDefaultLocale, setBlockDefaultLocale] = React.useState('');
  const [blockExtraLocales, setBlockExtraLocales] = React.useState<string[]>([]);
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
  const [heroConfig, setHeroConfig] = React.useState<HeroBlockConfig | null>(null);
  const [heroSnapshot, setHeroSnapshot] = React.useState<string>('{}');
  const [heroPreviewTheme, setHeroPreviewTheme] = React.useState<'light' | 'dark'>('light');
  const [heroPreviewLocale, setHeroPreviewLocale] = React.useState<string | null>(null);
  const [footerConfig, setFooterConfig] = React.useState<FooterConfig | null>(null);
  const [footerSnapshot, setFooterSnapshot] = React.useState<string>('{}');
  const prevDetailBlockRef = React.useRef<SiteBlock | null>(null);

  const normalizedAvailableLocales = React.useMemo(() => {
    const locales = new Set<string>();
    const defaultLocale = blockDefaultLocale.trim().toLowerCase();
    if (defaultLocale) {
      locales.add(defaultLocale);
    }
    blockExtraLocales.forEach((value) => {
      const normalized = value.trim().toLowerCase();
      if (normalized && normalized !== defaultLocale) {
        locales.add(normalized);
      }
    });
    return sortStrings(normalizeStringArray(Array.from(locales)));
  }, [blockDefaultLocale, blockExtraLocales]);

  const heroLocaleOptions = React.useMemo(() => {
    const locales = new Set<string>();
    const defaultLocaleCandidate = (blockDefaultLocale || detailBlock?.default_locale || '')
      .trim()
      .toLowerCase();
    if (defaultLocaleCandidate) {
      locales.add(defaultLocaleCandidate);
    }
    normalizedAvailableLocales.forEach((locale) => locales.add(locale));
    if (detailBlock?.available_locales) {
      detailBlock.available_locales
        .filter((locale): locale is string => typeof locale === 'string')
        .forEach((locale) => {
          const normalized = locale.trim().toLowerCase();
          if (normalized) {
            locales.add(normalized);
          }
        });
    }
    if (detailBlock?.locale) {
      locales.add(detailBlock.locale.trim().toLowerCase());
    }
    if (!locales.size) {
      locales.add('ru');
    }
    return Array.from(locales);
  }, [blockDefaultLocale, detailBlock, normalizedAvailableLocales]);
  const [saving, setSaving] = React.useState(false);
  const [saveError, setSaveError] = React.useState<string | null>(null);
  const [publishDialogOpen, setPublishDialogOpen] = React.useState(false);
  const [publishComment, setPublishComment] = React.useState('');
  const [publishing, setPublishing] = React.useState(false);
  const [publishError, setPublishError] = React.useState<string | null>(null);
  const [publishAckRequired, setPublishAckRequired] = React.useState(false);
  const [publishAckUsage, setPublishAckUsage] = React.useState<SiteBlockUsage[]>([]);
  const [publishAckConfirmed, setPublishAckConfirmed] = React.useState(false);
  const [publishAckMessage, setPublishAckMessage] = React.useState<string | null>(null);
  const [archiveDialogOpen, setArchiveDialogOpen] = React.useState(false);
  const [archiveMode, setArchiveMode] = React.useState<DialogMode>('archive');
  const [archiving, setArchiving] = React.useState(false);
  const [archiveError, setArchiveError] = React.useState<string | null>(null);
  const [restoreDialogOpen, setRestoreDialogOpen] = React.useState(false);
  const [restoreTarget, setRestoreTarget] = React.useState<SiteBlockHistoryItem | null>(null);
  const [restoreError, setRestoreError] = React.useState<string | null>(null);
  const [restoring, setRestoring] = React.useState(false);
  const { pushToast } = useToast();
  const {
    items: historyItems,
    total: historyTotal,
    loading: historyLoading,
    loadingMore: historyLoadingMore,
    error: historyError,
    refresh: refreshHistory,
    loadMore: loadMoreHistory,
  } = history;

  const openPublishDialog = React.useCallback(() => {
    setPublishDialogOpen(true);
    setPublishError(null);
    const hasUsage = detailUsage.length > 0;
    setPublishAckRequired(hasUsage);
    setPublishAckUsage(hasUsage ? detailUsage : []);
    setPublishAckConfirmed(!hasUsage);
    setPublishAckMessage(
      hasUsage
        ? 'Блок используется на следующих страницах. Подтвердите публикацию, чтобы они обновились.'
        : null,
    );
  }, [detailUsage]);

  React.useEffect(() => {
    if (!detailBlock) {
      prevDetailBlockRef.current = null;
      setComment('');
      setReviewStatus('none');
      setBlockTitle('');
      setBlockSection('');
      setBlockDefaultLocale('');
      setBlockExtraLocales([]);
      setBlockRequiresPublisher(false);
      setBlockIsTemplate(false);
      setBlockOriginBlockId('');
      setHeaderConfig(null);
      setHeaderSnapshot(JSON.stringify({}));
      setHeroConfig(null);
      setHeroSnapshot('{}');
      setHeroPreviewLocale(null);
      setFooterConfig(null);
      setFooterSnapshot('{}');
      return;
    }
    if (prevDetailBlockRef.current === detailBlock) {
      return;
    }
    prevDetailBlockRef.current = detailBlock;
    setComment(detailBlock.comment ?? '');
    setReviewStatus(detailBlock.review_status);
    setBlockTitle(detailBlock.title ?? '');
    setBlockSection(detailBlock.section ?? '');
    const defaultLocale = detailBlock.default_locale?.trim() ?? '';
    setBlockDefaultLocale(defaultLocale);
    const availableLocales = Array.isArray(detailBlock.available_locales)
      ? detailBlock.available_locales.filter(
          (value): value is string => typeof value === 'string' && value.trim().length > 0,
        )
      : [];
    const normalizedExtras = Array.from(
      new Set(
        availableLocales
          .map((value) => value.trim().toLowerCase())
          .filter((value) => value && value !== defaultLocale.toLowerCase()),
      ),
    );
    setBlockExtraLocales(normalizedExtras);
    setBlockRequiresPublisher(Boolean(detailBlock.requires_publisher));
    setBlockIsTemplate(Boolean(detailBlock.is_template));
    setBlockOriginBlockId(detailBlock.origin_block_id ?? '');
    const heroLocaleSeed = new Set<string>();
    if (defaultLocale) {
      heroLocaleSeed.add(defaultLocale.toLowerCase());
    }
    normalizedExtras.forEach((locale) => heroLocaleSeed.add(locale));
    availableLocales.forEach((locale) => heroLocaleSeed.add(locale.trim().toLowerCase()));
    if (detailBlock.locale) {
      heroLocaleSeed.add(detailBlock.locale.trim().toLowerCase());
    }
    if (!heroLocaleSeed.size) {
      heroLocaleSeed.add('ru');
    }
    const initialHeroLocales = Array.from(heroLocaleSeed);

    if (detailBlock.section === 'header') {
      const config = normalizeHeaderConfig(detailBlock.data ?? {});
      setHeaderConfig(config);
      setHeaderSnapshot(JSON.stringify(config));
    } else {
      setHeaderConfig(null);
      setHeaderSnapshot(JSON.stringify(detailBlock.data ?? {}));
    }
    if (detailBlock.section === 'hero') {
      const config = ensureHeroConfig(detailBlock.data ?? {}, initialHeroLocales);
      setHeroConfig(config);
      setHeroSnapshot(JSON.stringify(config));
      const preferredLocale =
        detailBlock.default_locale?.trim().toLowerCase() ??
        initialHeroLocales[0] ??
        'ru';
      setHeroPreviewLocale((current) =>
        current && initialHeroLocales.includes(current) ? current : preferredLocale,
      );
      setHeroPreviewTheme(config.layout.theme);
    } else {
      setHeroConfig(null);
      setHeroSnapshot('{}');
      setHeroPreviewLocale(null);
    }
    if (detailBlock.section === 'footer') {
      const config = ensureFooterConfig(detailBlock.data ?? {});
      setFooterConfig(config);
      setFooterSnapshot(JSON.stringify(config));
    } else {
      setFooterConfig(null);
      setFooterSnapshot('{}');
    }
  }, [detailBlock]);

  React.useEffect(() => {
    const normalizedDefault = blockDefaultLocale.trim().toLowerCase();
    setBlockExtraLocales((prev) => {
      const next = prev.filter((value) => value !== normalizedDefault);
      if (next.length === prev.length) {
        return prev;
      }
      return next;
    });
  }, [blockDefaultLocale]);

  React.useEffect(() => {
    if (!heroConfig) {
      return;
    }
    const missing = heroLocaleOptions.filter((locale) => !heroConfig.locales[locale]);
    if (!missing.length) {
      return;
    }
    setHeroConfig((prev) => {
      if (!prev) {
        return prev;
      }
      const nextLocales = { ...prev.locales };
      missing.forEach((locale) => {
        nextLocales[locale] = createDefaultHeroLocale();
      });
      return {
        ...prev,
        locales: nextLocales,
      };
    });
  }, [heroConfig, heroLocaleOptions]);

  React.useEffect(() => {
    if (!heroLocaleOptions.length) {
      setHeroPreviewLocale(null);
      return;
    }
    setHeroPreviewLocale((current) =>
      current && heroLocaleOptions.includes(current) ? current : heroLocaleOptions[0],
    );
  }, [heroLocaleOptions]);

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
    if (prevBlockIdRef.current === blockId) {
      return;
    }
    prevBlockIdRef.current = blockId;
    setDetailTab('overview');
  }, [blockId]);

  React.useEffect(() => {
    if (blockIsTemplate) {
      setBlockOriginBlockId('');
    }
  }, [blockIsTemplate]);

  const resetDetail = React.useCallback(() => {
    refreshDetail();
    refreshHistory();
  }, [refreshDetail, refreshHistory]);
  const handleHistoryLoadMore = React.useCallback(() => loadMoreHistory(), [loadMoreHistory]);

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
      mutateDetail({
        block: response.block,
        usage: response.usage,
        warnings: response.warnings,
      });
      onBlockMutated(response.block);
      refreshHistory();
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
  }, [archiveMode, detailBlock, mutateDetail, onBlockMutated, pushToast, refreshHistory]);

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
      mutateDetail({
        block: response.block,
        usage: response.usage,
        warnings: response.warnings,
      });
      onBlockMutated(response.block);
      refreshHistory();
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
  }, [detailBlock, mutateDetail, onBlockMutated, pushToast, refreshHistory, restoreTarget]);

  const closePublishDialog = React.useCallback(() => {
    if (publishing) {
      return;
    }
    setPublishDialogOpen(false);
    setPublishComment('');
    setPublishError(null);
    setPublishAckRequired(false);
    setPublishAckUsage([]);
    setPublishAckConfirmed(false);
    setPublishAckMessage(null);
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

  const handleExtraLocalesChange = React.useCallback(
    (values: string[]) => {
      const normalizedDefault = blockDefaultLocale.trim().toLowerCase();
      const normalized = Array.from(
        new Set(
          values
            .map((value) => value.trim().toLowerCase())
            .filter((value) => value && value !== normalizedDefault),
        ),
      );
      setBlockExtraLocales(normalized);
    },
    [blockDefaultLocale],
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
    const mustConfirmUsage = publishAckRequired;
    if (mustConfirmUsage && !publishAckConfirmed) {
      setPublishError('Подтвердите публикацию: поставьте галочку ниже, чтобы обновить связанные страницы.');
      return;
    }
    setPublishing(true);
    setPublishError(null);
    try {
      const payload: PublishSiteBlockPayload & { acknowledge_usage?: boolean } = {};
      const normalizedComment = publishComment.trim();
      if (normalizedComment.length > 0) {
        payload.comment = normalizedComment;
      }
      if (typeof detailBlock.draft_version === 'number') {
        payload.version = detailBlock.draft_version;
      }
      if (mustConfirmUsage && publishAckConfirmed) {
        payload.acknowledge_usage = true;
      }
      const response = await managementSiteEditorApi.publishSiteBlock(detailBlock.id, payload);
      mutateDetail({
        block: response.block,
        usage: response.usage,
        warnings: detailWarnings,
      });
      onBlockMutated(response.block);
      setPublishDialogOpen(false);
      setPublishComment('');
      setPublishAckRequired(false);
      setPublishAckUsage([]);
      setPublishAckConfirmed(false);
      setPublishAckMessage(null);
      pushToast({ intent: 'success', description: 'Блок опубликован' });
      refreshHistory();
    } catch (err) {
      if (err instanceof ApiRequestError) {
        const details = err.details;
        const baseDetail =
          isObjectRecord(details) && isObjectRecord(details.detail) ? details.detail : details;
        if (isObjectRecord(baseDetail) && pickString(baseDetail.error) === 'site_block_ack_required') {
          const usageList = ensureArray(baseDetail.usage, normalizeBlockUsage);
          setPublishAckUsage(usageList);
          setPublishAckRequired(true);
          setPublishAckConfirmed(false);
          setPublishAckMessage(
            pickString(baseDetail.message) ??
              'Блок используется на нескольких страницах. Подтвердите публикацию, чтобы обновить их.',
          );
          setPublishError(null);
          return;
        }
      }
      setPublishError(extractErrorMessage(err, 'Не удалось опубликовать блок'));
    } finally {
      setPublishing(false);
    }
  }, [
    detailBlock,
    detailWarnings,
    mutateDetail,
    onBlockMutated,
    publishAckConfirmed,
    publishAckRequired,
    publishComment,
    pushToast,
    refreshHistory,
  ]);

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
      const dataPayload = headerConfig ?? heroConfig ?? footerConfig ?? detailBlock.data ?? {};
      const payload: SaveSiteBlockPayload = {
        data: dataPayload,
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
      mutateDetail({
        block: updated,
        usage: detailUsage,
        warnings: detailWarnings,
      });
      onBlockMutated(updated);
      if (detailBlock.section === 'header' && headerConfig) {
        setHeaderSnapshot(JSON.stringify(headerConfig));
      }
      if (detailBlock.section === 'hero' && heroConfig) {
        setHeroSnapshot(JSON.stringify(heroConfig));
      }
      if (detailBlock.section === 'footer' && footerConfig) {
        setFooterSnapshot(JSON.stringify(footerConfig));
      }
      pushToast({ intent: 'success', description: 'Блок сохранён' });
    } catch (err) {
      setSaveError(extractErrorMessage(err, 'Не удалось сохранить блок'));
    } finally {
      setSaving(false);
    }
  }, [
    blockDefaultLocale,
    blockIsTemplate,
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
    heroConfig,
    footerConfig,
    mutateDetail,
    onBlockMutated,
    pushToast,
    reviewStatus,
  ]);

  const commentDirty = detailBlock ? comment.trim() !== (detailBlock.comment ?? '') : false;
  const reviewDirty = detailBlock ? reviewStatus !== detailBlock.review_status : false;
  const isHeaderBlock = detailBlock?.section === 'header' && Boolean(headerConfig);
  const isHeroBlock = detailBlock?.section === 'hero' && Boolean(heroConfig);
  const isFooterBlock = detailBlock?.section === 'footer' && Boolean(footerConfig);
  const headerDirty = headerConfig ? JSON.stringify(headerConfig) !== headerSnapshot : false;
  const heroDirty = heroConfig ? JSON.stringify(heroConfig) !== heroSnapshot : false;
  const footerDirty = footerConfig ? JSON.stringify(footerConfig) !== footerSnapshot : false;
  const baseInfoDirty = detailBlock
    ? blockTitle.trim() !== (detailBlock.title ?? '') ||
      blockSection.trim() !== (detailBlock.section ?? '') ||
      (blockDefaultLocale.trim() || '') !== (detailBlock.default_locale ?? '') ||
      !isSameStringList(normalizedAvailableLocales, currentAvailableLocales) ||
      blockRequiresPublisher !== Boolean(detailBlock.requires_publisher) ||
      blockIsTemplate !== Boolean(detailBlock.is_template) ||
      (blockOriginBlockId.trim() || '') !== (detailBlock.origin_block_id ?? '')
    : false;

  const canSave =
    Boolean(detailBlock) &&
    (headerDirty || heroDirty || footerDirty || commentDirty || reviewDirty || baseInfoDirty);
  const canPublish =
    Boolean(detailBlock?.draft_version) && detailBlock?.status !== 'archived' && !detailBlock?.is_template;
  const historyHasMore = historyItems.length < historyTotal;
  const isArchived = detailBlock?.status === 'archived';
  const archiveLabel = archiving
    ? (isArchived ? 'Возвращаем…' : 'Отправляем…')
    : (isArchived ? 'Вернуть из архива' : 'В архив');
  const archiveColor: 'primary' | 'error' = isArchived ? 'primary' : 'error';
  const documentationUrl = detailBlock ? pickDocumentationUrl(detailBlock) : null;
  return (
    <div className="space-y-4" data-testid="site-block-library-detail">
      {detailBlock ? (
        <SiteBlockDetailHeader
          block={detailBlock}
          loading={detailLoading}
          onRefresh={resetDetail}
          onPublish={openPublishDialog}
          onSave={handleSave}
          saving={saving}
          publishing={publishing}
          publishDisabled={!canPublish || !detailBlock}
          saveDisabled={!canSave || !detailBlock}
          onArchive={() => openArchiveDialog(isArchived ? 'restore' : 'archive')}
          archiveDisabled={archiving || detailLoading || saving || publishing}
          archiveLabel={archiveLabel}
          archiveColor={archiveColor}
        />
      ) : (
        <Card className="space-y-3 border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
          {detailError ? (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{detailError}</div>
          ) : (
            <div className="text-sm text-gray-600">Выберите блок из списка слева, чтобы увидеть детали.</div>
          )}
        </Card>
      )}
      {detailBlock && detailError ? (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{detailError}</div>
      ) : null}
      {detailLoading ? (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Spinner className="h-4 w-4" /> Загружаем блок…
        </div>
      ) : null}
      {detailBlock ? (
        <Card className="space-y-3 border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Tabs
              value={detailTab}
              onChange={(key) => setDetailTab(key as DetailTab)}
              items={[
                { key: 'overview', label: 'Сводка' },
                { key: 'settings', label: 'Настройки' },
                ...(isHeaderBlock || isHeroBlock ? [{ key: 'preview', label: 'Предпросмотр' }] : []),
                { key: 'history', label: 'История' },
                {
                  key: 'usage',
                  label: detailUsage.length ? `Использование (${detailUsage.length})` : 'Использование',
                },
              ]}
            />
            {documentationUrl ? (
              <Button
                as="a"
                variant="ghost"
                color="neutral"
                size="sm"
                href={documentationUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                Документация
              </Button>
            ) : null}
          </div>
          {detailTab === 'overview' ? (
            <div className="space-y-4">
              <Card className="space-y-4 border border-gray-200 bg-white p-5 shadow-sm dark:border-dark-600/80 dark:bg-dark-800">
                <div className="grid gap-4 md:grid-cols-2">
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
                    <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">Секция</label>
                    <div className="flex items-center gap-2 rounded-lg border border-dashed border-gray-200 px-3 py-2 text-xs text-gray-600 dark:border-dark-600 dark:text-dark-200">
                      <Badge color="neutral" variant="soft">
                        {blockSection || '—'}
                      </Badge>
                      <span className="text-2xs text-gray-400">
                        Слот размещения блока. Изменяется на странице, а не в библиотеке.
                      </span>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">Базовая локаль</label>
                    <Select
                      value={blockDefaultLocale || ''}
                      onChange={(event) => setBlockDefaultLocale(event.target.value.trim().toLowerCase())}
                      disabled={saving || publishing}
                    >
                      <option value="">Не выбрана</option>
                      {Array.from(KNOWN_LOCALES).map((locale) => (
                        <option key={locale} value={locale}>
                          {locale === 'ru' ? 'Русский (ru)' : 'English (en)'}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">
                      Дополнительные локали
                    </label>
                    <TagInput
                      value={blockExtraLocales}
                      onChange={handleExtraLocalesChange}
                      placeholder="добавьте локаль (например, en)"
                      disabled={saving || publishing}
                    />
                    <div className="text-2xs text-gray-500 dark:text-dark-300">
                      Доступные локали: {KNOWN_LOCALES.join(', ')}. Добавляйте значения по Enter.
                    </div>
                  </div>
                </div>
                <Card className="space-y-3 border border-dashed border-gray-200 bg-gray-50/60 p-4 dark:border-dark-600 dark:bg-dark-800/40">
                  <div className="grid gap-3 md:grid-cols-2">
                    <div className="space-y-1">
                      <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">Требует publisher</label>
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
                    <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">Родительский блок</label>
                    <Input
                      value={blockOriginBlockId}
                      onChange={(event) => setBlockOriginBlockId(event.target.value)}
                      disabled={saving || publishing || blockIsTemplate}
                      placeholder="ID шаблона, если блок создан на его основе"
                    />
                  </div>
                </Card>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">Комментарий</label>
                  <Textarea
                    rows={3}
                    value={comment}
                    onChange={(event) => setComment(event.target.value)}
                    disabled={saving || publishing}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-gray-600 dark:text-dark-200">Статус ревью</label>
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
              </Card>

              <div className="space-y-3">
                {detailWarnings.length ? (
                  <Card className="space-y-2 border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-100">
                    <div className="flex items-center gap-2 font-semibold">
                      <AlertTriangle className="h-4 w-4" />
                      Есть предупреждения
                    </div>
                    <ul className="list-disc space-y-1 pl-5">
                      {detailWarnings.map((warning, index) => (
                        <li key={`${warning.code}-${index}`}>
                          <span className="font-semibold">{warning.title ?? warning.code}:</span> {warning.message ?? '—'}
                        </li>
                      ))}
                    </ul>
                  </Card>
                ) : null}
              </div>
            </div>
          ) : null}
          {saveError ? (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
              {saveError}
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
              ) : isHeroBlock && heroConfig ? (
                <SiteBlockHeroForm
                  value={heroConfig}
                  onChange={setHeroConfig}
                  localeOptions={heroLocaleOptions}
                  defaultLocale={blockDefaultLocale || 'ru'}
                  disabled={saving || publishing}
                />
              ) : isFooterBlock && footerConfig ? (
                <SiteBlockFooterForm
                  value={footerConfig}
                  onChange={setFooterConfig}
                  disabled={saving || publishing}
                />
              ) : (
                <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 p-4 text-sm text-gray-500 dark:border-dark-600 dark:bg-dark-900/40 dark:text-dark-200">
                  Данные для этого блока редактируются через API. Сохранение обновит черновик в библиотеке.
                </div>
              )}
            </Card>
          ) : null}

          {detailTab === 'preview' && detailBlock ? (
            isHeaderBlock && headerConfig ? (
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
                  config={headerConfig ?? normalizeHeaderConfig(detailBlock.data ?? {})}
                  device={headerPreviewDevice}
                  theme={headerPreviewTheme}
                  locale={headerPreviewLocale ?? detailBlock.default_locale ?? 'ru'}
                />
              </Card>
            ) : isHeroBlock && heroConfig ? (
              <Card className="space-y-4 border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Hero-блок</h3>
                    <p className="text-xs text-gray-500 dark:text-dark-300">
                      Проверьте, как выглядит первый экран на разных локалях и темах.
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Select
                      value={heroPreviewTheme}
                      onChange={(event) => setHeroPreviewTheme(event.target.value as 'light' | 'dark')}
                    >
                      <option value="light">Light</option>
                      <option value="dark">Dark</option>
                    </Select>
                    <Select
                      value={heroPreviewLocale ?? heroLocaleOptions[0] ?? 'ru'}
                      onChange={(event) => setHeroPreviewLocale(event.target.value || null)}
                    >
                      {heroLocaleOptions.map((locale) => (
                        <option key={locale} value={locale}>
                          {locale.toUpperCase()}
                        </option>
                      ))}
                    </Select>
                  </div>
                </div>
                {heroPreviewLocale ? (
                  <HeroBlockPreview
                    config={heroConfig}
                    locale={heroPreviewLocale}
                    theme={heroPreviewTheme}
                  />
                ) : (
                  <div className="rounded-xl border border-dashed border-gray-200 p-4 text-center text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
                    Нет локалей для предпросмотра
                  </div>
                )}
              </Card>
            ) : null
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
            <Button
              onClick={handlePublish}
              disabled={publishing || (publishAckRequired && !publishAckConfirmed)}
            >
              {publishing ? 'Публикуем…' : 'Опубликовать'}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-sm text-gray-600 dark:text-dark-200">
            Блок будет опубликован и обновит страницы, где он используется. Оставьте комментарий, чтобы зафиксировать изменения.
          </p>
          {publishAckRequired ? (
            <div className="space-y-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-100">
              <div className="text-sm font-semibold text-amber-900 dark:text-amber-100">Подтверждение публикации</div>
              {publishAckMessage ? (
                <p className="text-xs text-amber-700 dark:text-amber-200">{publishAckMessage}</p>
              ) : null}
              <div className="max-h-60 space-y-1 overflow-y-auto rounded-md border border-amber-200/60 bg-white/80 pr-1 dark:border-amber-500/30 dark:bg-amber-500/10">
                {(publishAckUsage.length ? publishAckUsage : detailUsage).length ? (
                  (publishAckUsage.length ? publishAckUsage : detailUsage).map((item) => (
                    <div
                      key={item.page_id}
                      className="flex flex-wrap items-center justify-between gap-2 rounded border border-amber-200/70 bg-white/90 px-2 py-1 text-[11px] text-amber-900 dark:border-amber-500/40 dark:bg-amber-500/20 dark:text-amber-50"
                    >
                      <div className="flex min-w-0 flex-1 flex-col">
                        <span className="truncate font-semibold">{item.title || item.slug}</span>
                        <span className="truncate text-2xs uppercase tracking-wide text-amber-700 dark:text-amber-200">
                          {item.slug}
                        </span>
                      </div>
                      <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-700 dark:bg-amber-500/30 dark:text-amber-100">
                        {item.section || '—'}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="flex min-h-[48px] items-center justify-center rounded border border-amber-200/60 bg-white/70 p-2 text-xs text-amber-700 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
                    Нет данных об использующих страницах.
                  </div>
                )}
              </div>
              <label className="flex items-start gap-2 text-xs text-amber-800 dark:text-amber-50">
                <input
                  type="checkbox"
                  className="mt-1 h-3.5 w-3.5 accent-amber-600"
                  checked={publishAckConfirmed}
                  onChange={(event) => setPublishAckConfirmed(event.target.checked)}
                />
                <span>Подтверждаю, что публикация обновит перечисленные страницы.</span>
              </label>
            </div>
          ) : null}
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

import * as React from 'react';
import { managementSiteEditorApi } from '@shared/api/management';
import { extractErrorMessage } from '@shared/utils/errors';
import type { HomeHistoryEntry } from '@shared/types/home';
import type {
  SiteAuditEntry,
  SitePageDraft,
  SitePageSummary,
  SitePageVersion,
  SiteDraftValidationResult,
  SitePageDraftDiffResponse,
  SitePagePreviewResponse,
  SitePageMetricsResponse,
  SiteMetricsPeriod,
} from '@shared/types/management';
import {
  validateHomeDraft,
  type ValidationSummary,
} from '../../home/validation';
import type {
  HomeBlock,
  HomeBlockDataSource,
  HomeBlockDataSourceEntity,
  HomeBlockDataSourceMode,
  HomeDraftData,
  HomeDraftSnapshot,
} from '../../home/types';

export type UseSitePageEditorStateOptions = {
  pageId: string;
  autosaveMs?: number;
};

const DEFAULT_AUTOSAVE_MS = 1500;

const DEFAULT_DATA: HomeDraftData = {
  blocks: [],
  meta: null,
};

const DEFAULT_SNAPSHOT: HomeDraftSnapshot = {
  version: null,
  updatedAt: null,
  publishedAt: null,
};

type AnyRecord = Record<string, unknown>;

const ALLOWED_BLOCK_TYPES: ReadonlyArray<HomeBlock['type']> = [
  'hero',
  'dev_blog_list',
  'quests_carousel',
  'nodes_carousel',
  'popular_carousel',
  'editorial_picks',
  'recommendations',
  'custom_carousel',
];

const ALLOWED_BLOCK_TYPE_SET = new Set<HomeBlock['type']>(ALLOWED_BLOCK_TYPES);

function isRecord(value: unknown): value is AnyRecord {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

function normalizeDataSource(value: unknown): HomeBlockDataSource | null {
  if (!isRecord(value)) {
    return null;
  }
  const mode = value.mode;
  if (mode !== 'manual' && mode !== 'auto') {
    return null;
  }
  const result: HomeBlockDataSource = {
    mode: mode as HomeBlockDataSourceMode,
  };
  const entity = value.entity;
  if (entity === 'node' || entity === 'quest' || entity === 'dev_blog' || entity === 'custom') {
    result.entity = entity as HomeBlockDataSourceEntity;
  }
  if (isRecord(value.filter)) {
    result.filter = { ...value.filter };
  }
  if (Array.isArray(value.items)) {
    const items = value.items.filter((item): item is string | number => {
      if (typeof item === 'string') {
        return item.trim().length > 0;
      }
      return typeof item === 'number' && Number.isFinite(item);
    });
    if (items.length > 0) {
      result.items = items;
    }
  }
  return result;
}

function normalizeBlock(raw: unknown, index: number): HomeBlock | null {
  if (!isRecord(raw)) {
    return null;
  }
  const idRaw = raw.id;
  let id = typeof idRaw === 'string' ? idRaw.trim() : '';
  if (!id) {
    id = `block-${index + 1}`;
  }
  const typeRaw = raw.type;
  const type = typeof typeRaw === 'string' && ALLOWED_BLOCK_TYPE_SET.has(typeRaw as HomeBlock['type'])
    ? (typeRaw as HomeBlock['type'])
    : 'hero';
  const enabledRaw = raw.enabled;
  const enabled = typeof enabledRaw === 'boolean' ? enabledRaw : true;

  const block: HomeBlock = {
    id,
    type,
    enabled,
  };

  if (typeof raw.title === 'string') {
    block.title = raw.title;
  }
  if (isRecord(raw.slots)) {
    block.slots = { ...raw.slots };
  }
  if (isRecord(raw.layout)) {
    block.layout = { ...raw.layout };
  }
  const dataSource = normalizeDataSource(raw.dataSource ?? raw.data_source);
  if (dataSource) {
    block.dataSource = dataSource;
  }

  return block;
}

function normalizeDraftData(raw: unknown): HomeDraftData {
  if (!isRecord(raw)) {
    return DEFAULT_DATA;
  }
  const rawBlocks = Array.isArray(raw.blocks) ? raw.blocks : [];
  const blocks: HomeBlock[] = [];
  rawBlocks.forEach((item, index) => {
    const block = normalizeBlock(item, index);
    if (block) {
      blocks.push(block);
    }
  });
  const meta = isRecord(raw.meta) ? { ...raw.meta } : null;
  return {
    blocks,
    meta,
  };
}

function cloneMeta(meta: HomeDraftData['meta']): Record<string, unknown> | undefined {
  if (!meta) {
    return undefined;
  }
  const entries = Object.entries(meta);
  if (!entries.length) {
    return undefined;
  }
  return entries.reduce<Record<string, unknown>>((acc, [key, value]) => {
    acc[key] = value;
    return acc;
  }, {});
}

function buildDraftPayload(data: HomeDraftData): { data: Record<string, unknown>; meta?: Record<string, unknown> } {
  const normalizedData: Record<string, unknown> = {
    blocks: Array.isArray(data.blocks) ? data.blocks : [],
  };
  const meta = cloneMeta(data.meta ?? null);
  const payload: { data: Record<string, unknown>; meta?: Record<string, unknown> } = {
    data: normalizedData,
  };
  if (meta) {
    payload.meta = meta;
  }
  return payload;
}

function makeSnapshot(draft: SitePageDraft | null): HomeDraftSnapshot {
  if (!draft) {
    return DEFAULT_SNAPSHOT;
  }
  return {
    version: draft.version ?? null,
    updatedAt: draft.updated_at ?? null,
    publishedAt: null,
  };
}

function mapHistoryToHomeEntries(
  pageId: string,
  versions: SitePageVersion[],
  currentPublishedVersion: number | null | undefined,
): HomeHistoryEntry[] {
  return versions.map((entry) => ({
    configId: pageId,
    version: entry.version,
    action: 'publish',
    actor: entry.published_by ?? null,
    actorTeam: null,
    comment: entry.comment ?? null,
    createdAt: entry.published_at ?? entry.published_at ?? '',
    publishedAt: entry.published_at ?? null,
    isCurrent: currentPublishedVersion != null && entry.version === currentPublishedVersion,
  }));
}

export type SitePageEditorState = {
  page: SitePageSummary | null;
  loading: boolean;
  data: HomeDraftData;
  setData: (updater: (prev: HomeDraftData) => HomeDraftData) => void;
  setBlocks: (blocks: HomeBlock[]) => void;
  selectBlock: (blockId: string | null) => void;
  selectedBlockId: string | null;
  dirty: boolean;
  saving: boolean;
  savingError: string | null;
  lastSavedAt: string | null;
  pageMetrics: SitePageMetricsResponse | null;
  metricsLoading: boolean;
  metricsError: string | null;
  metricsPeriod: SiteMetricsPeriod;
  setMetricsPeriod: (period: SiteMetricsPeriod) => void;
  refreshMetrics: () => void;
  reviewStatus: SitePageDraft['review_status'];
  setReviewStatus: (status: SitePageDraft['review_status']) => void;
  loadDraft: (opts?: { silent?: boolean }) => Promise<void>;
  saveDraft: (opts?: { silent?: boolean }) => Promise<void>;
  snapshot: HomeDraftSnapshot;
  slug: string;
  validation: ValidationSummary;
  revalidate: () => ValidationSummary;
  serverValidation: SiteDraftValidationResult | null;
  serverValidationLoading: boolean;
  serverValidationError: string | null;
  runServerValidation: () => Promise<SiteDraftValidationResult>;
  draftDiff: SitePageDraftDiffResponse | null;
  diffLoading: boolean;
  diffError: string | null;
  refreshDiff: () => Promise<void>;
  preview: SitePagePreviewResponse | null;
  previewLayouts: string[];
  previewLayout: string;
  selectPreviewLayout: (layout: string) => void;
  previewLoading: boolean;
  previewError: string | null;
  refreshPreview: (options?: { layouts?: string[] }) => Promise<void>;
  publishing: boolean;
  publishDraft: (options?: { comment?: string }) => Promise<void>;
  restoringVersion: number | null;
  restoreVersion: (version: number) => Promise<void>;
  siteHistory: SitePageVersion[];
  siteHistoryLoading: boolean;
  siteHistoryError: string | null;
  refreshHistory: () => Promise<void>;
  auditEntries: SiteAuditEntry[];
  auditLoading: boolean;
  auditError: string | null;
  refreshAudit: () => Promise<void>;
  historyForContext: HomeHistoryEntry[];
};

export function useSitePageEditorState(
  options: UseSitePageEditorStateOptions,
): SitePageEditorState {
  const { pageId, autosaveMs = DEFAULT_AUTOSAVE_MS } = options;

  const [page, setPage] = React.useState<SitePageSummary | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [dataState, setDataState] = React.useState<HomeDraftData>(DEFAULT_DATA);
  const [selectedBlockId, setSelectedBlockId] = React.useState<string | null>(null);
  const [dirty, setDirty] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [savingError, setSavingError] = React.useState<string | null>(null);
  const [lastSavedAt, setLastSavedAt] = React.useState<string | null>(null);
  const [reviewStatusState, setReviewStatusState] = React.useState<SitePageDraft['review_status']>('none');
  const [publishing, setPublishing] = React.useState(false);
  const [metricsPeriodState, setMetricsPeriodState] = React.useState<SiteMetricsPeriod>('7d');
  const [pageMetrics, setPageMetrics] = React.useState<SitePageMetricsResponse | null>(null);
  const [metricsLoading, setMetricsLoading] = React.useState(false);
  const [metricsError, setMetricsError] = React.useState<string | null>(null);
  const [snapshot, setSnapshot] = React.useState<HomeDraftSnapshot>(DEFAULT_SNAPSHOT);
  const [validation, setValidation] = React.useState<ValidationSummary>(validateHomeDraft(DEFAULT_DATA));
  const [restoringVersion, setRestoringVersion] = React.useState<number | null>(null);

  const [siteHistory, setSiteHistory] = React.useState<SitePageVersion[]>([]);
  const [siteHistoryLoading, setSiteHistoryLoading] = React.useState(false);
  const [siteHistoryError, setSiteHistoryError] = React.useState<string | null>(null);

  const [auditEntries, setAuditEntries] = React.useState<SiteAuditEntry[]>([]);
  const [auditLoading, setAuditLoading] = React.useState(false);
  const [auditError, setAuditError] = React.useState<string | null>(null);

  const [serverValidation, setServerValidation] = React.useState<SiteDraftValidationResult | null>(null);
  const [serverValidationLoading, setServerValidationLoading] = React.useState(false);
  const [serverValidationError, setServerValidationError] = React.useState<string | null>(null);

  const [draftDiff, setDraftDiff] = React.useState<SitePageDraftDiffResponse | null>(null);
  const [diffLoading, setDiffLoading] = React.useState(false);
  const [diffError, setDiffError] = React.useState<string | null>(null);

  const [preview, setPreview] = React.useState<SitePagePreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = React.useState(false);
  const [previewError, setPreviewError] = React.useState<string | null>(null);
  const [previewLayout, setPreviewLayout] = React.useState<string>('desktop');

  const previewLayouts = React.useMemo(
    () => (preview ? Object.keys(preview.layouts) : []),
    [preview],
  );

  const dataRef = React.useRef<HomeDraftData>(DEFAULT_DATA);
  const draftVersionRef = React.useRef<number>(0);
  const reviewStatusRef = React.useRef<SitePageDraft['review_status']>('none');
  const savingRef = React.useRef(false);
  const publishingRef = React.useRef(false);
  const metricsLocaleRef = React.useRef<string>('ru');
  const metricsAbortRef = React.useRef<AbortController | null>(null);
  const autosaveTimer = React.useRef<number | null>(null);

  const clearAutosaveTimer = React.useCallback(() => {
    if (autosaveTimer.current != null) {
      window.clearTimeout(autosaveTimer.current);
      autosaveTimer.current = null;
    }
  }, []);

  React.useEffect(() => {
    if (!preview) {
      return;
    }
    const layouts = Object.keys(preview.layouts);
    if (layouts.length === 0) {
      return;
    }
    if (!layouts.includes(previewLayout)) {
      setPreviewLayout(layouts[0]);
    }
  }, [preview, previewLayout]);

  const runServerValidation = React.useCallback(async (): Promise<SiteDraftValidationResult> => {
    setServerValidationLoading(true);
    setServerValidationError(null);
    try {
      const payload = buildDraftPayload(dataRef.current);
      const result = await managementSiteEditorApi.validateSitePageDraft(pageId, {
        data: payload.data,
        meta: payload.meta,
      });
      setServerValidation(result);
      return result;
    } catch (error) {
      const message = extractErrorMessage(error, 'Не удалось выполнить проверку.');
      setServerValidationError(message);
      throw error;
    } finally {
      setServerValidationLoading(false);
    }
  }, [pageId]);

  const refreshDiff = React.useCallback(async () => {
    setDiffLoading(true);
    setDiffError(null);
    try {
      const response = await managementSiteEditorApi.diffSitePageDraft(pageId);
      setDraftDiff(response);
    } catch (error) {
      setDiffError(extractErrorMessage(error, 'Не удалось получить diff.'));
    } finally {
      setDiffLoading(false);
    }
  }, [pageId]);

  const refreshPreview = React.useCallback(
    async ({ layouts }: { layouts?: string[] } = {}) => {
      setPreviewLoading(true);
      setPreviewError(null);
      try {
        const payload = buildDraftPayload(dataRef.current);
        const response = await managementSiteEditorApi.previewSitePage(pageId, {
          data: payload.data,
          meta: payload.meta,
          layouts,
          version: draftVersionRef.current || undefined,
        });
        setPreview(response);
      } catch (error) {
        setPreviewError(extractErrorMessage(error, 'Не удалось получить предпросмотр.'));
      } finally {
        setPreviewLoading(false);
      }
    },
    [pageId],
  );

  const selectPreviewLayout = React.useCallback(
    (layout: string) => {
      setPreviewLayout(layout);
      if (preview && preview.layouts[layout]) {
        return;
      }
      refreshPreview({ layouts: [layout] }).catch(() => undefined);
    },
    [preview, refreshPreview],
  );

  const refreshHistory = React.useCallback(async () => {
    setSiteHistoryLoading(true);
    setSiteHistoryError(null);
    try {
      const response = await managementSiteEditorApi.fetchSitePageHistory(pageId, { limit: 10, offset: 0 });
      setSiteHistory(response.items);
    } catch (error) {
      setSiteHistoryError(extractErrorMessage(error, 'Не удалось загрузить историю версий.'));
    } finally {
      setSiteHistoryLoading(false);
    }
  }, [pageId]);

  const refreshAudit = React.useCallback(async () => {
    setAuditLoading(true);
    setAuditError(null);
    try {
      const response = await managementSiteEditorApi.fetchSiteAudit({
        entityType: 'page',
        entityId: pageId,
        limit: 10,
        offset: 0,
      });
      setAuditEntries(response.items);
    } catch (error) {
      setAuditError(extractErrorMessage(error, 'Не удалось загрузить аудит.'));
    } finally {
      setAuditLoading(false);
    }
  }, [pageId]);

  const revalidate = React.useCallback((): ValidationSummary => {
    const summary = validateHomeDraft(dataRef.current);
    setValidation(summary);
    return summary;
  }, []);

  const fetchMetrics = React.useCallback(
    async (
      { silent = false, periodOverride }: { silent?: boolean; periodOverride?: SiteMetricsPeriod } = {},
    ) => {
      if (!pageId) {
        return;
      }
      metricsAbortRef.current?.abort();
      const controller = new AbortController();
      metricsAbortRef.current = controller;
      if (!silent) {
        setMetricsLoading(true);
      }
      setMetricsError(null);
      try {
        const periodToUse = periodOverride ?? metricsPeriodState;
        const response = await managementSiteEditorApi.fetchSitePageMetrics(
          pageId,
          {
            period: periodToUse,
            locale: metricsLocaleRef.current,
          },
          { signal: controller.signal },
        );
        setPageMetrics(response);
      } catch (error) {
        if ((error as Error)?.name === 'AbortError') {
          return;
        }
        const message = extractErrorMessage(error, 'Не удалось загрузить метрики.');
        setMetricsError(message);
      } finally {
        metricsAbortRef.current = null;
        setMetricsLoading(false);
      }
    },
    [metricsPeriodState, pageId],
  );

  const loadDraft = React.useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    const controller = new AbortController();
    if (!silent) {
      setLoading(true);
    }
    setSavingError(null);
    try {
      const [pageSummary, draft] = await Promise.all([
        managementSiteEditorApi.fetchSitePage(pageId, { signal: controller.signal }),
        managementSiteEditorApi.fetchSitePageDraft(pageId, { signal: controller.signal }),
      ]);
      if (!pageSummary) {
        throw new Error('site_page_not_found');
      }
      metricsLocaleRef.current = pageSummary.locale || 'ru';
      setPageMetrics(null);
      setMetricsError(null);
      setPage(pageSummary);
      draftVersionRef.current = draft?.version ?? pageSummary.draft_version ?? 1;
      reviewStatusRef.current = draft?.review_status ?? 'none';
      setReviewStatusState(reviewStatusRef.current);
      const normalized = normalizeDraftData(draft?.data ?? null);
      dataRef.current = normalized;
      setDataState(normalized);
      setSelectedBlockId(normalized.blocks[0]?.id ?? null);
      setDirty(false);
      setSnapshot(makeSnapshot(draft ?? null));
      setLastSavedAt(draft?.updated_at ?? null);
      setValidation(validateHomeDraft(normalized));
      setServerValidation(null);
      setServerValidationError(null);
      setDraftDiff(null);
      setDiffError(null);
      setPreview(null);
      setPreviewError(null);
      setPreviewLayout('desktop');
      void refreshDiff().catch(() => undefined);
      void refreshPreview().catch(() => undefined);
      void refreshHistory();
      void refreshAudit();
      void fetchMetrics({ silent: true }).catch(() => undefined);
    } catch (error) {
      setSavingError(extractErrorMessage(error, 'Не удалось загрузить черновик страницы.'));
      throw error;
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }, [fetchMetrics, pageId, refreshAudit, refreshDiff, refreshHistory, refreshPreview]);

  const saveDraft = React.useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (savingRef.current) {
      return;
    }
    const summary = revalidate();
    if (!summary.valid) {
      if (!silent) {
        setSavingError('Исправьте ошибки в конфигурации перед сохранением.');
      }
      throw new Error('site_page_validation_failed');
    }
    clearAutosaveTimer();
    savingRef.current = true;
    if (!silent) {
      setSaving(true);
    }
    setSavingError(null);
    try {
      const payload = buildDraftPayload(dataRef.current);
      const draft = await managementSiteEditorApi.saveSitePageDraft(
        pageId,
        {
          version: draftVersionRef.current,
          data: payload.data,
          meta: payload.meta,
          review_status: reviewStatusRef.current,
        },
      );
      draftVersionRef.current = draft.version;
      reviewStatusRef.current = draft.review_status;
      setReviewStatusState(draft.review_status);
      setSnapshot(makeSnapshot(draft));
      setDirty(false);
      setLastSavedAt(draft.updated_at ?? new Date().toISOString());
      setPage((prev) => (prev ? ({ ...prev, draft_version: draft.version }) : prev));
      runServerValidation().catch(() => undefined);
      refreshDiff().catch(() => undefined);
      refreshPreview().catch(() => undefined);
    } catch (error) {
      const message = extractErrorMessage(error, 'Не удалось сохранить черновик.');
      setSavingError(message);
      throw error;
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  }, [clearAutosaveTimer, pageId, revalidate, refreshDiff, refreshPreview, runServerValidation]);

  const scheduleAutosave = React.useCallback(() => {
    if (autosaveMs <= 0) {
      return;
    }
    clearAutosaveTimer();
    autosaveTimer.current = window.setTimeout(() => {
      autosaveTimer.current = null;
      void saveDraft({ silent: true }).catch(() => {});
    }, autosaveMs);
  }, [autosaveMs, clearAutosaveTimer, saveDraft]);

  const setReviewStatus = React.useCallback((status: SitePageDraft['review_status']) => {
    if (reviewStatusRef.current === status) {
      return;
    }
    reviewStatusRef.current = status;
    setReviewStatusState(status);
    setDirty(true);
    setSavingError(null);
    scheduleAutosave();
  }, [scheduleAutosave]);

  const setData = React.useCallback((updater: (prev: HomeDraftData) => HomeDraftData) => {
    setDataState((prev) => {
      const next = updater(prev);
      dataRef.current = next;
      return next;
    });
    setDirty(true);
    setSavingError(null);
    scheduleAutosave();
  }, [scheduleAutosave]);

  const setMetricsPeriod = React.useCallback(
    (period: SiteMetricsPeriod) => {
      setMetricsPeriodState(period);
      fetchMetrics({ periodOverride: period }).catch(() => undefined);
    },
    [fetchMetrics],
  );

  const refreshMetrics = React.useCallback(() => {
    fetchMetrics().catch(() => undefined);
  }, [fetchMetrics]);

  const setBlocks = React.useCallback((blocks: HomeBlock[]) => {
    setData((prev) => ({
      ...prev,
      blocks,
    }));
  }, [setData]);

  const selectBlock = React.useCallback((blockId: string | null) => {
    setSelectedBlockId(blockId);
  }, []);

  const restoreVersion = React.useCallback(async (version: number) => {
    if (!Number.isFinite(version)) {
      throw new Error('site_page_restore_invalid_version');
    }
    setRestoringVersion(version);
    setSavingError(null);
    clearAutosaveTimer();
    try {
      const draft = await managementSiteEditorApi.restoreSitePageVersion(pageId, version);
      if (!draft) {
        throw new Error('site_page_restore_failed');
      }
      draftVersionRef.current = draft.version;
      reviewStatusRef.current = draft.review_status;
      setReviewStatusState(draft.review_status);
      const normalized = normalizeDraftData(draft.data);
      dataRef.current = normalized;
      setDataState(normalized);
      setSelectedBlockId(normalized.blocks[0]?.id ?? null);
      setDirty(false);
      setSnapshot(makeSnapshot(draft));
      setLastSavedAt(draft.updated_at ?? new Date().toISOString());
      setValidation(validateHomeDraft(normalized));
      await Promise.all([
        refreshHistory(),
        refreshAudit(),
        refreshDiff(),
        refreshPreview(),
      ]);
      runServerValidation().catch(() => undefined);
    } finally {
      setRestoringVersion(null);
    }
  }, [clearAutosaveTimer, pageId, refreshAudit, refreshDiff, refreshHistory, refreshPreview, runServerValidation]);

  const publishDraft = React.useCallback(async ({ comment }: { comment?: string } = {}) => {
    if (publishingRef.current) {
      return;
    }
    try {
      if (dirty) {
        await saveDraft({ silent: false });
      } else {
        const summary = revalidate();
        if (!summary.valid) {
          setSavingError('Исправьте ошибки перед публикацией.');
          throw new Error('site_page_publish_validation_failed');
        }
      }
      publishingRef.current = true;
      setSavingError(null);
      setPublishing(true);
      clearAutosaveTimer();
      await managementSiteEditorApi.publishSitePage(pageId, {
        comment: comment ?? undefined,
      });
      reviewStatusRef.current = 'none';
      setReviewStatusState('none');
      await loadDraft({ silent: true });
      await Promise.allSettled([
        refreshHistory(),
        refreshAudit(),
        refreshDiff(),
        refreshPreview(),
      ]);
      await fetchMetrics({ silent: true }).catch(() => undefined);
    } catch (error) {
      const message = extractErrorMessage(error, 'Не удалось опубликовать страницу.');
      setSavingError(message);
      throw error;
    } finally {
      publishingRef.current = false;
      setPublishing(false);
    }
  }, [clearAutosaveTimer, dirty, fetchMetrics, loadDraft, pageId, refreshAudit, refreshDiff, refreshHistory, refreshPreview, revalidate, saveDraft]);

  React.useEffect(() => {
    setValidation(validateHomeDraft(dataState));
  }, [dataState]);

  React.useEffect(() => {
    clearAutosaveTimer();
    setDirty(false);
    setSavingError(null);
    void loadDraft();
    return () => {
      clearAutosaveTimer();
    };
  }, [clearAutosaveTimer, loadDraft, pageId]);

  React.useEffect(() => () => {
    metricsAbortRef.current?.abort();
  }, []);

  React.useEffect(() => () => {
    clearAutosaveTimer();
  }, [clearAutosaveTimer]);

  const historyForContext = React.useMemo(() => {
    return mapHistoryToHomeEntries(pageId, siteHistory, page?.published_version ?? null);
  }, [pageId, page?.published_version, siteHistory]);

  return {
    page,
    loading,
    data: dataState,
    setData,
    setBlocks,
    selectBlock,
  selectedBlockId,
  dirty,
  saving,
  savingError,
  lastSavedAt,
  metricsPeriod: metricsPeriodState,
  setMetricsPeriod,
  pageMetrics,
  metricsLoading,
  metricsError,
  refreshMetrics,
  reviewStatus: reviewStatusState,
  setReviewStatus,
  loadDraft,
  saveDraft,
  publishing,
  publishDraft,
  snapshot,
  slug: page?.slug ?? '',
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
  };
}

import * as React from 'react';
import { validateHomeDraft, type ValidationSummary } from '../validation';
import { getDraft, publishHome, restoreHome, saveDraft as persistDraft } from '@shared/api/home';
import { buildHomeConfigPayload } from '../utils/payload';
import type { HomeConfigSnapshot, HomeHistoryEntry } from '@shared/types/home';
import { extractErrorMessage } from '@shared/utils/errors';
import type { HomeBlock, HomeBlockDataSource, HomeBlockDataSourceEntity, HomeBlockDataSourceMode, HomeDraftData, HomeDraftSnapshot } from '../types';

export type UseHomeEditorStateOptions = {
  slug?: string;
  autosaveMs?: number;
};

export type UseHomeEditorStateResult = {
  loading: boolean;
  data: HomeDraftData;
  snapshot: HomeDraftSnapshot;
  slug: string;
  selectedBlockId: string | null;
  dirty: boolean;
  saving: boolean;
  savingError: string | null;
  lastSavedAt: string | null;
  history: HomeHistoryEntry[];
  publishing: boolean;
  restoringVersion: number | null;
  publishDraft: (options?: { comment?: string }) => Promise<void>;
  restoreVersion: (version: number, options?: { comment?: string }) => Promise<void>;
  validation: ValidationSummary;
  setData: (updater: (prev: HomeDraftData) => HomeDraftData) => void;
  setBlocks: (blocks: HomeBlock[]) => void;
  selectBlock: (blockId: string | null) => void;
  loadDraft: (opts?: { silent?: boolean }) => Promise<void>;
  saveDraft: (opts?: { silent?: boolean }) => Promise<void>;
  revalidate: () => ValidationSummary;
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
  } else if (raw.slots === null) {
    block.slots = null;
  }
  if (isRecord(raw.layout)) {
    block.layout = { ...raw.layout };
  } else if (raw.layout === null) {
    block.layout = null;
  }
  const dataSource = normalizeDataSource(raw.dataSource);
  if (dataSource) {
    block.dataSource = dataSource;
  }
  return block;
}

function normalizeDraftData(value: unknown): HomeDraftData {
  if (!isRecord(value)) {
    return DEFAULT_DATA;
  }
  const blocksInput = Array.isArray(value.blocks) ? value.blocks : [];
  const blocks: HomeBlock[] = blocksInput
    .map((item, index) => normalizeBlock(item, index))
    .filter((item): item is HomeBlock => !!item);

  const meta = isRecord(value.meta) ? { ...value.meta } : null;

  return {
    blocks,
    meta,
  };
}

function makeSnapshot(snapshot: HomeConfigSnapshot | null | undefined): HomeDraftSnapshot {
  if (!snapshot) {
    return DEFAULT_SNAPSHOT;
  }
  return {
    version: Number.isFinite(snapshot.version) ? snapshot.version : null,
    updatedAt: typeof snapshot.updated_at === 'string' ? snapshot.updated_at : null,
    publishedAt: typeof snapshot.published_at === 'string' ? snapshot.published_at : null,
  };
}

export function useHomeEditorState(
  { slug = 'main', autosaveMs = DEFAULT_AUTOSAVE_MS }: UseHomeEditorStateOptions = {},
): UseHomeEditorStateResult {
  const [loading, setLoading] = React.useState<boolean>(true);
  const [data, setDataState] = React.useState<HomeDraftData>(DEFAULT_DATA);
  const [snapshot, setSnapshot] = React.useState<HomeDraftSnapshot>(DEFAULT_SNAPSHOT);
  const [selectedBlockId, setSelectedBlockId] = React.useState<string | null>(null);
  const [dirty, setDirty] = React.useState<boolean>(false);
  const [saving, setSaving] = React.useState<boolean>(false);
  const [savingError, setSavingError] = React.useState<string | null>(null);
  const [lastSavedAt, setLastSavedAt] = React.useState<string | null>(null);
  const [history, setHistory] = React.useState<HomeHistoryEntry[]>([]);
  const [publishing, setPublishing] = React.useState<boolean>(false);
  const [restoringVersion, setRestoringVersion] = React.useState<number | null>(null);
  const [validation, setValidation] = React.useState<ValidationSummary>(() => validateHomeDraft(DEFAULT_DATA));

  const autosaveTimer = React.useRef<number | null>(null);
  const savingRef = React.useRef<boolean>(false);
  const dataRef = React.useRef<HomeDraftData>(DEFAULT_DATA);
  const publishingRef = React.useRef<boolean>(false);
  const restoringRef = React.useRef<number | null>(null);

  React.useEffect(() => () => {
    if (autosaveTimer.current) {
      window.clearTimeout(autosaveTimer.current);
      autosaveTimer.current = null;
    }
  }, []);

  const clearAutosaveTimer = React.useCallback(() => {
    if (autosaveTimer.current) {
      window.clearTimeout(autosaveTimer.current);
      autosaveTimer.current = null;
    }
  }, []);

  const revalidate = React.useCallback((): ValidationSummary => {
    const summary = validateHomeDraft(dataRef.current);
    setValidation(summary);
    return summary;
  }, []);

  const saveDraft = React.useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (savingRef.current) {
      return;
    }
    const summary = revalidate();
    if (!summary.valid) {
      if (!silent) {
        setSavingError('Исправьте ошибки в конфигурации перед сохранением.');
      }
      throw new Error('home_validation_failed');
    }
    clearAutosaveTimer();
    savingRef.current = true;
    if (!silent) {
      setSaving(true);
    }
    setSavingError(null);
    try {
      const payload = buildHomeConfigPayload(slug, dataRef.current);
      const snapshotResponse = await persistDraft(payload);
      setSnapshot(makeSnapshot(snapshotResponse));
      setDirty(false);
      setLastSavedAt(snapshotResponse.updated_at ?? new Date().toISOString());
    } catch (error) {
      const message = extractErrorMessage(error, 'Не удалось сохранить черновик.');
      setSavingError(message);
      throw error;
    } finally {
      savingRef.current = false;
      setSaving(false);
    }
  }, [clearAutosaveTimer, revalidate, slug]);

    const loadDraft = React.useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    if (!silent) {
      setLoading(true);
    }
    setSavingError(null);
    try {
      const payload = await getDraft({ slug });
      const draftSnapshot = payload.draft ?? payload.published ?? null;
      setHistory(payload.history ?? []);
      setSnapshot(makeSnapshot(draftSnapshot));
      const normalized = normalizeDraftData(draftSnapshot?.data);
      dataRef.current = normalized;
      setDataState(normalized);
      setSelectedBlockId(normalized.blocks[0]?.id ?? null);
      setDirty(false);
      setLastSavedAt(draftSnapshot?.updated_at ?? null);
      setValidation(validateHomeDraft(normalized));
    } catch (error) {
      setSavingError(extractErrorMessage(error, "Не удалось загрузить черновик."));
      throw error;
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  }, [slug]);

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
          setSavingError('Исправьте ошибки в конфигурации перед публикацией.');
          throw new Error('home_validation_failed');
        }
      }
      publishingRef.current = true;
      setPublishing(true);
      clearAutosaveTimer();
      const payload = buildHomeConfigPayload(slug, dataRef.current);
      const requestPayload = comment ? { ...payload, comment } : payload;
      await publishHome(requestPayload);
      await loadDraft({ silent: true });
    } finally {
      publishingRef.current = false;
      setPublishing(false);
    }
  }, [clearAutosaveTimer, dirty, loadDraft, revalidate, saveDraft, slug]);

  const restoreVersion = React.useCallback(async (version: number, { comment }: { comment?: string } = {}) => {
    if (!Number.isFinite(version)) {
      throw new Error('home_invalid_restore_version');
    }
    if (restoringRef.current === version) {
      return;
    }
    restoringRef.current = version;
    setRestoringVersion(version);
    setSavingError(null);
    clearAutosaveTimer();
    try {
      const payload = buildHomeConfigPayload(slug, dataRef.current);
      const requestPayload = comment ? { slug: payload.slug, comment } : { slug: payload.slug };
      const restored = await restoreHome(version, requestPayload);
      setSnapshot(makeSnapshot(restored.draft));
      const normalized = normalizeDraftData(restored.draft.data);
      dataRef.current = normalized;
      setDataState(normalized);
      setSelectedBlockId(normalized.blocks[0]?.id ?? null);
      setDirty(false);
      setLastSavedAt(restored.draft.updated_at ?? new Date().toISOString());
      setValidation(validateHomeDraft(normalized));
    } finally {
      restoringRef.current = null;
      setRestoringVersion(null);
    }
  }, [clearAutosaveTimer, slug]);

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

  const setBlocks = React.useCallback((blocks: HomeBlock[]) => {
    setData((prev) => ({
      ...prev,
      blocks,
    }));
  }, [setData]);

  const selectBlock = React.useCallback((blockId: string | null) => {
    setSelectedBlockId(blockId);
  }, []);

  React.useEffect(() => {
    setValidation(validateHomeDraft(data));
  }, [data]);

  React.useEffect(() => {
    void loadDraft();
  }, [loadDraft]);

  return {
    loading,
    data,
    snapshot,
    slug,
    selectedBlockId,
    dirty,
    saving,
    savingError,
    lastSavedAt,
    history,
    publishing,
    restoringVersion,
    validation,
    setData,
    setBlocks,
    selectBlock,
    publishDraft,
    restoreVersion,
    loadDraft,
    saveDraft,
    revalidate,
  };
}


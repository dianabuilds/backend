import {
  type HomeBlock,
  type HomeDraftData,
} from '../../home/types';
import {
  validateHomeDraft,
  type ValidationSummary as HomeValidationSummary,
} from '../../home/validation';
import type {
  DraftBlock,
  DraftData,
  DraftPreviewMapperOptions,
  DraftPreviewPayload,
  DraftValidationSummary,
  SiteDraftAdapter,
} from './types';
import type {
  SitePagePreviewLayout,
  SitePagePreviewResponse,
} from '@shared/types/management';

const HOME_ALLOWED_BLOCK_TYPES: ReadonlyArray<HomeBlock['type']> = [
  'hero',
  'dev_blog_list',
  'quests_carousel',
  'nodes_carousel',
  'popular_carousel',
  'editorial_picks',
  'recommendations',
  'custom_carousel',
];

function normalizeDataSource(value: unknown): DraftBlock['dataSource'] | null {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null;
  }
  const record = value as Record<string, unknown>;
  const mode = record.mode;
  if (mode !== 'manual' && mode !== 'auto') {
    return null;
  }
  const dataSource: DraftBlock['dataSource'] = {
    mode,
  };
  const entity = record.entity;
  if (entity === 'node' || entity === 'quest' || entity === 'dev_blog' || entity === 'custom') {
    dataSource.entity = entity;
  }
  if (record.filter && typeof record.filter === 'object') {
    dataSource.filter = { ...(record.filter as Record<string, unknown>) };
  }
  if (Array.isArray(record.items)) {
    const items = (record.items as unknown[]).filter(
      (item): item is string | number =>
        (typeof item === 'string' && item.trim().length > 0) ||
        (typeof item === 'number' && Number.isFinite(item)),
    );
    if (items.length > 0) {
      dataSource.items = items;
    }
  }
  return dataSource;
}

function normalizeBlock(raw: unknown, index: number): DraftBlock | null {
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) {
    return null;
  }
  const record = raw as Record<string, unknown>;
  const pickString = (...keys: string[]): string | null => {
    for (const key of keys) {
      const value = record[key];
      if (typeof value === 'string') {
        const trimmed = value.trim();
        if (trimmed.length > 0) {
          return trimmed;
        }
      }
    }
    return null;
  };
  const pickBoolean = (...keys: string[]): boolean | null => {
    for (const key of keys) {
      const value = record[key];
      if (typeof value === 'boolean') {
        return value;
      }
      if (typeof value === 'string') {
        const normalized = value.trim().toLowerCase();
        if (normalized === 'true') {
          return true;
        }
        if (normalized === 'false') {
          return false;
        }
      }
    }
    return null;
  };
  const idRaw = record.id;
  let id = typeof idRaw === 'string' ? idRaw.trim() : '';
  if (!id) {
    id = `block-${index + 1}`;
  }
  const typeRaw = record.type;
  const type =
    typeof typeRaw === 'string' && HOME_ALLOWED_BLOCK_TYPES.includes(typeRaw as HomeBlock['type'])
      ? (typeRaw as HomeBlock['type'])
      : 'hero';
  const enabledRaw = record.enabled;
  const enabled = typeof enabledRaw === 'boolean' ? enabledRaw : true;

  const block: DraftBlock = {
    id,
    type,
    enabled,
  };

  if (typeof record.title === 'string') {
    block.title = record.title;
  }
  if (record.slots && typeof record.slots === 'object') {
    block.slots = { ...(record.slots as Record<string, unknown>) };
  }
  if (record.layout && typeof record.layout === 'object') {
    block.layout = { ...(record.layout as Record<string, unknown>) };
  }
  const dataSource = normalizeDataSource(record.dataSource ?? record.data_source);
  if (dataSource) {
    block.dataSource = dataSource;
  }
  if (typeof record.source === 'string') {
    const source = record.source.trim().toLowerCase();
    if (source === 'site' || source === 'manual' || source === 'global') {
      block.source = source === 'global' ? 'site' : (source as DraftBlock['source']);
    }
  }
  const blockKey = pickString('block_key', 'blockKey', 'key', 'site_block_key', 'siteBlockKey');
  if (blockKey) {
    block.siteBlockKey = blockKey;
  }
  const blockIdValue = pickString('block_id', 'blockId', 'site_block_id', 'siteBlockId');
  if (blockIdValue) {
    block.siteBlockId = blockIdValue;
  }
  const localeValue = pickString('locale', 'site_block_locale', 'siteBlockLocale', 'block_locale');
  if (localeValue) {
    block.siteBlockLocale = localeValue;
  }
  const sectionValue = pickString('section', 'zone', 'site_block_section', 'siteBlockSection', 'block_section');
  if (sectionValue) {
    block.siteBlockSection = sectionValue;
  }
  const siteTitle = pickString('block_title', 'site_block_title', 'siteBlockTitle');
  if (siteTitle) {
    block.siteBlockTitle = siteTitle;
  }
  const siteStatus = pickString('block_status', 'site_block_status', 'siteBlockStatus');
  if (siteStatus) {
    block.siteBlockStatus = siteStatus;
  }
  const siteReviewStatus = pickString('block_review_status', 'site_block_review_status', 'siteBlockReviewStatus');
  if (siteReviewStatus) {
    block.siteBlockReviewStatus = siteReviewStatus;
  }
  const requiresPublisher = pickBoolean(
    'block_requires_publisher',
    'site_block_requires_publisher',
    'siteBlockRequiresPublisher',
  );
  if (requiresPublisher !== null) {
    block.siteBlockRequiresPublisher = requiresPublisher;
  }
  const hasPendingPublish = pickBoolean(
    'block_has_pending_publish',
    'site_block_has_pending_publish',
    'siteBlockHasPendingPublish',
  );
  if (hasPendingPublish !== null) {
    block.siteBlockHasPendingPublish = hasPendingPublish;
  }
  const hasDraft = pickBoolean('block_has_draft', 'site_block_has_draft', 'siteBlockHasDraft');
  if (hasDraft !== null) {
    block.siteBlockHasDraft = hasDraft;
  }
  const updatedAt = pickString('block_updated_at', 'site_block_updated_at', 'siteBlockUpdatedAt');
  if (updatedAt) {
    block.siteBlockUpdatedAt = updatedAt;
  }
  const updatedBy = pickString('block_updated_by', 'site_block_updated_by', 'siteBlockUpdatedBy');
  if (updatedBy) {
    block.siteBlockUpdatedBy = updatedBy;
  }
  return block;
}

function normalizeDraftData(
  raw: unknown,
  options: {
    meta?: Record<string, unknown> | null;
    assignments?: Record<string, string | null> | null;
  } = {},
): DraftData {
  const source = raw && typeof raw === 'object' && !Array.isArray(raw) ? (raw as Record<string, unknown>) : {};
  const rawBlocks = Array.isArray(source.blocks) ? source.blocks : [];
  const blocks: DraftBlock[] = [];
  rawBlocks.forEach((item, index) => {
    const block = normalizeBlock(item, index);
    if (block) {
      blocks.push(block);
    }
  });
  const meta = options.meta ? { ...options.meta } : null;
  const assignments =
    options.assignments && typeof options.assignments === 'object'
      ? { ...options.assignments }
      : {};
  return {
    blocks,
    meta,
    shared: {
      assignments,
    },
  };
}

function buildDraftPayload(data: DraftData): { data: Record<string, unknown>; meta?: Record<string, unknown> } {
  const blocksPayload = Array.isArray(data.blocks)
    ? data.blocks.map((block) => {
        const base: Record<string, unknown> = {
          id: block.id,
          type: block.type,
          enabled: block.enabled,
        };
        if (block.title) {
          base.title = block.title;
        }
        if (block.slots) {
          base.slots = block.slots;
        }
        if (block.layout) {
          base.layout = block.layout;
        }
        if (block.dataSource) {
          base.dataSource = block.dataSource;
        }
        if (block.source === 'site' && block.siteBlockKey) {
          base.source = 'global';
          base.key = block.siteBlockKey;
          base.section = block.siteBlockSection ?? block.type;
          if (block.siteBlockId) {
            base.block_id = block.siteBlockId;
          }
          if (block.siteBlockLocale) {
            base.locale = block.siteBlockLocale;
          }
        }
        return base;
      })
    : [];
  const payload: Record<string, unknown> = {
    blocks: blocksPayload,
  };
  const assignments =
    data.shared && typeof data.shared === 'object' ? data.shared.assignments ?? {} : {};
  const filteredAssignments = Object.entries(assignments).reduce<Record<string, string>>(
    (acc, [section, value]) => {
      if (typeof value === 'string' && value.trim().length > 0) {
        acc[section] = value.trim();
      }
      return acc;
    },
    {},
  );
  if (Object.keys(filteredAssignments).length > 0) {
    payload.shared = {
      assignments: filteredAssignments,
    };
  }
  if (data.meta && Object.keys(data.meta).length > 0) {
    payload.meta = { ...data.meta };
  }
  return { data: payload };
}

function mapPreviewResponse(
  response: SitePagePreviewResponse | null | undefined,
  options: DraftPreviewMapperOptions = {},
): DraftPreviewPayload | null {
  if (!response) {
    return null;
  }
  const desiredLayout = options.layout?.trim();
  if (desiredLayout && Array.isArray(response.preview_variants)) {
    const variant = response.preview_variants.find((entry) => entry?.layout === desiredLayout);
    const payload = extractPreviewPayload(variant?.response);
    if (payload) {
      return payload;
    }
  }
  const previewPayload = extractPreviewPayload(response.preview);
  if (previewPayload) {
    return previewPayload;
  }
  if (desiredLayout && response.layouts?.[desiredLayout]) {
    const payload = extractLayoutPayload(response.layouts[desiredLayout]);
    if (payload) {
      return payload;
    }
  }
  const [firstLayout] = Object.keys(response.layouts ?? {});
  if (firstLayout) {
    const payload = extractLayoutPayload(response.layouts[firstLayout]);
    if (payload) {
      return payload;
    }
  }
  return null;
}

function extractPreviewPayload(document?: SitePagePreviewResponse['preview'] | null): DraftPreviewPayload | null {
  if (!document || typeof document !== 'object') {
    return null;
  }
  const record = document as Record<string, unknown>;
  if (record.payload && typeof record.payload === 'object') {
    return record.payload as DraftPreviewPayload;
  }
  if (record.data && typeof record.data === 'object') {
    return record.data as DraftPreviewPayload;
  }
  return null;
}

function extractLayoutPayload(layout?: SitePagePreviewLayout | null): DraftPreviewPayload | null {
  if (!layout || typeof layout !== 'object') {
    return null;
  }
  const record = layout as Record<string, unknown>;
  if (record.payload && typeof record.payload === 'object') {
    return record.payload as DraftPreviewPayload;
  }
  if (record.data && typeof record.data === 'object') {
    return record.data as DraftPreviewPayload;
  }
  return null;
}

function convertValidationSummary(summary: HomeValidationSummary): DraftValidationSummary {
  return {
    valid: summary.valid,
    general: summary.general,
    blocks: summary.blocks,
  };
}

export const homeDraftAdapter: SiteDraftAdapter = {
  allowedBlockTypes: HOME_ALLOWED_BLOCK_TYPES,
  createEmptyData(): DraftData {
    return {
      blocks: [],
      meta: null,
      shared: {
        assignments: {},
      },
    };
  },
  normalizeDraftData,
  buildDraftPayload,
  mapPreviewResponse,
  validateDraft(data: DraftData): DraftValidationSummary {
    const result = validateHomeDraft(data as HomeDraftData);
    return convertValidationSummary(result);
  },
};

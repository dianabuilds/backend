import type {
  SiteAuditEntry,
  SiteBlock,
  SiteBlockHistoryItem,
  SiteBlockMetricsResponse,
  SiteBlockMetricsTopPage,
  SiteBlockPublishJob,
  SiteBlockTemplate,
  SiteBlockUsage,
  SiteBlockWarning,
  SiteDraftValidationResult,
  SiteMetricAlert,
  SiteMetricValue,
  SiteMetricsRange,
  SitePageAttachedBlock,
  SitePageBlockReference,
  SitePageDiffEntry,
  SitePageDraft,
  SitePageMetricsResponse,
  SitePagePreviewLayout,
  SitePagePreviewResponse,
  SitePagePreviewDocument,
  SitePagePreviewVariant,
  SitePagePreviewLocale,
  SitePageSummary,
  SitePageVersion,
  SiteValidationErrorEntry,
} from '@shared/types/management';

import {
  BLOCK_STATUSES,
  PAGE_STATUSES,
  PAGE_TYPES,
  REVIEW_STATUSES,
} from './constants';
import type { SiteBlockPreviewItem, SiteBlockPreviewResponse } from './types';

import {
  ensureArray,
  isObjectRecord,
  pickBoolean,
  pickNullableString,
  pickNumber,
  pickString,
} from '../utils';

export function normalizePage(value: unknown): SitePageSummary | null {
  if (!isObjectRecord(value)) {
    return null;
  }

  const id = pickString(value.id);
  const slug = pickString(value.slug);
  const title = pickString(value.title);
  const typeRaw = pickString(value.type);
  const statusRaw = pickString(value.status);

  if (!id || !slug || !title) {
    return null;
  }

  const type = PAGE_TYPES.includes(typeRaw as typeof PAGE_TYPES[number])
    ? (typeRaw as typeof PAGE_TYPES[number])
    : 'landing';
  const status = PAGE_STATUSES.includes(statusRaw as typeof PAGE_STATUSES[number])
    ? (statusRaw as typeof PAGE_STATUSES[number])
    : 'draft';

  const publishedVersion = pickNumber(value.published_version);
  const draftVersion = pickNumber(value.draft_version);
  const pinned = pickBoolean(value.pinned);
  const defaultLocale = pickString(value.default_locale) ?? pickString(value.locale) ?? 'ru';
  const availableLocales = ensureArray(
    value.available_locales,
    (entry): string | null => {
      if (typeof entry !== 'string') {
        return null;
      }
      const normalized = entry.trim();
      return normalized || null;
    },
  ).filter((entry): entry is string => typeof entry === 'string' && entry.length > 0);
  const localizedSlugs = isObjectRecord(value.slug_localized)
    ? Object.entries(value.slug_localized).reduce<Record<string, string>>((acc, [locale, slugValue]) => {
        if (typeof slugValue === 'string' && locale) {
          acc[locale] = slugValue;
        }
        return acc;
      }, {})
    : undefined;
  let sharedBindings = ensureArray(
    value.shared_bindings,
    normalizePageAttachedBlock,
  ).filter((item): item is SitePageAttachedBlock => item != null);
  if (!sharedBindings.length) {
    sharedBindings = ensureArray(
      (value as Record<string, unknown>).bindings,
      normalizePageAttachedBlock,
    ).filter((item): item is SitePageAttachedBlock => item != null);
  }
  const blockRefs = ensureArray(
    (value as Record<string, unknown>).block_refs,
    normalizePageBlockReference,
  ).filter((item): item is SitePageBlockReference => item != null);

  return {
    id,
    slug,
    title,
    type,
    status,
    locale: defaultLocale,
    owner: pickNullableString(value.owner),
    updated_at: pickNullableString(value.updated_at),
    published_version: publishedVersion ?? null,
    draft_version: draftVersion ?? null,
    has_pending_review: pickBoolean(value.has_pending_review) ?? null,
    pinned: pinned ?? null,
    default_locale: defaultLocale,
    available_locales: availableLocales.length ? availableLocales : undefined,
    localized_slugs: localizedSlugs,
    shared_bindings: sharedBindings.length ? sharedBindings : undefined,
    bindings: sharedBindings.length ? sharedBindings : undefined,
    block_refs: blockRefs.length ? blockRefs : undefined,
  };
}

export function normalizeDraft(value: unknown): SitePageDraft | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const pageId = pickString(value.page_id) ?? pickString(value.pageId);
  const version = pickNumber(value.version);
  if (!pageId || !Number.isFinite(version)) {
    return null;
  }
  const data = isObjectRecord(value.data) ? (value.data as Record<string, unknown>) : {};
  const meta = isObjectRecord(value.meta) ? (value.meta as Record<string, unknown>) : {};
  const reviewStatusRaw = pickString(value.review_status) ?? 'none';
  const reviewStatus = REVIEW_STATUSES.has(reviewStatusRaw)
    ? (reviewStatusRaw as SitePageDraft['review_status'])
    : 'none';
  const defaultLocale = pickString(value.default_locale) ?? pickString(value.locale) ?? 'ru';
  const availableLocales = ensureArray(
    value.available_locales,
    (entry): string | null => {
      if (typeof entry !== 'string') {
        return null;
      }
      const normalized = entry.trim();
      return normalized || null;
    },
  ).filter((entry): entry is string => typeof entry === 'string' && entry.length > 0);
  const slugLocalized = isObjectRecord(value.slug_localized)
    ? Object.entries(value.slug_localized).reduce<Record<string, string>>((acc, [locale, slugValue]) => {
        if (typeof slugValue === 'string' && locale) {
          acc[locale] = slugValue;
        }
        return acc;
      }, {})
    : undefined;
  let sharedBindings = ensureArray(
    value.shared_bindings,
    normalizePageAttachedBlock,
  ).filter((item): item is SitePageAttachedBlock => item != null);
  if (!sharedBindings.length) {
    sharedBindings = ensureArray(
      (value as Record<string, unknown>).bindings,
      normalizePageAttachedBlock,
    ).filter((item): item is SitePageAttachedBlock => item != null);
  }
  const blockRefs = ensureArray(
    (value as Record<string, unknown>).block_refs,
    normalizePageBlockReference,
  ).filter((item): item is SitePageBlockReference => item != null);

  return {
    page_id: pageId,
    version: version as number,
    data,
    meta,
    default_locale: defaultLocale,
    available_locales: availableLocales.length ? availableLocales : undefined,
    slug_localized: slugLocalized,
    active_locale: pickString(value.active_locale) ?? undefined,
    fallback_locale: pickString(value.fallback_locale) ?? undefined,
    comment: pickNullableString(value.comment) ?? null,
    review_status: reviewStatus,
    updated_at: pickNullableString(value.updated_at),
    updated_by: pickNullableString(value.updated_by),
    shared_bindings: sharedBindings.length ? sharedBindings : undefined,
    bindings: sharedBindings.length ? sharedBindings : undefined,
    block_refs: blockRefs.length ? blockRefs : undefined,
  };
}

export function normalizeValidationErrorEntry(value: unknown): SiteValidationErrorEntry | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const message = pickString(value.message);
  if (!message) {
    return null;
  }
  const path = pickString(value.path) ?? '/';
  const validator = pickNullableString(value.validator) ?? undefined;
  return { path, message, validator };
}

export function normalizeValidationResult(value: unknown): SiteDraftValidationResult {
  if (!isObjectRecord(value)) {
    return {
      valid: false,
      code: 'site_page_validation_failed',
      errors: { general: [], blocks: {} },
    };
  }
  const valid = pickBoolean(value.valid) ?? false;
  if (valid) {
    const data = isObjectRecord(value.data) ? (value.data as Record<string, unknown>) : {};
    const meta = isObjectRecord(value.meta) ? (value.meta as Record<string, unknown>) : {};
    return {
      valid: true,
      data,
      meta,
    };
  }
  const code = pickString((value as Record<string, unknown>).code) ?? 'site_page_validation_failed';
  const errorsValue = isObjectRecord((value as Record<string, unknown>).errors)
    ? ((value as Record<string, unknown>).errors as Record<string, unknown>)
    : {};
  const general = ensureArray(errorsValue.general, normalizeValidationErrorEntry);
  const blocksSource = isObjectRecord(errorsValue.blocks)
    ? (errorsValue.blocks as Record<string, unknown>)
    : {};
  const blocks: Record<string, SiteValidationErrorEntry[]> = {};
  for (const [blockId, raw] of Object.entries(blocksSource)) {
    if (!blockId) {
      continue;
    }
    const entries = ensureArray(raw, normalizeValidationErrorEntry);
    if (entries.length) {
      blocks[blockId] = entries;
    }
  }
  return {
    valid: false,
    code,
    errors: {
      general,
      blocks,
    },
  };
}

export function normalizeBlock(value: unknown): SiteBlock | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  const key = pickString(value.key);
  const title = pickString(value.title);
  if (!id || !key || !title) {
    return null;
  }
  const templateId =
    pickNullableString(value.template_id) ?? pickNullableString((value as Record<string, unknown>).templateId) ?? null;
  const templateKey =
    pickNullableString(value.template_key) ?? pickNullableString((value as Record<string, unknown>).templateKey) ?? null;
  const section = pickString(value.section) ?? 'general';
  const locale = pickNullableString(value.locale) ?? null;
  const scopeRaw = pickNullableString(value.scope) ?? null;
  const scope = scopeRaw === 'shared' || scopeRaw === 'page' ? scopeRaw : null;
  const defaultLocale = pickNullableString(value.default_locale) ?? null;
  const availableLocales = Array.isArray(value.available_locales)
    ? value.available_locales
        .map((entry) => (typeof entry === 'string' && entry.trim() ? entry.trim() : null))
        .filter((entry): entry is string => Boolean(entry))
    : null;
  const statusRaw = pickString(value.status) ?? 'draft';
  const status = BLOCK_STATUSES.includes(statusRaw as typeof BLOCK_STATUSES[number])
    ? (statusRaw as typeof BLOCK_STATUSES[number])
    : 'draft';
  const reviewStatusRaw = pickString(value.review_status) ?? 'none';
  const reviewStatus = REVIEW_STATUSES.has(reviewStatusRaw)
    ? (reviewStatusRaw as SiteBlock['review_status'])
    : 'none';
  const requiresPublisher = pickBoolean(value.requires_publisher) ?? false;
  const publishedVersion = pickNumber(value.published_version) ?? null;
  const draftVersion = pickNumber(value.draft_version) ?? null;
  const version = pickNumber(value.version) ?? draftVersion ?? publishedVersion ?? null;
  const usageCount = pickNumber(value.usage_count) ?? null;
  const comment = pickNullableString(value.comment) ?? null;
  const data = isObjectRecord(value.data) ? (value.data as Record<string, unknown>) : undefined;
  const meta = isObjectRecord(value.meta) ? (value.meta as Record<string, unknown>) : undefined;
  const updatedAt = pickNullableString(value.updated_at) ?? null;
  const updatedBy = pickNullableString(value.updated_by) ?? null;
  const createdAt = pickNullableString(value.created_at) ?? null;
  const createdBy = pickNullableString(value.created_by) ?? null;
  const lastUsedAt = pickNullableString(value.last_used_at) ?? null;
  const hasPendingPublish = pickBoolean(value.has_pending_publish);
  const isTemplate = pickBoolean(value.is_template) ?? false;
  const originBlockId = pickNullableString(value.origin_block_id) ?? null;
  const extras = isObjectRecord(value.extras) ? (value.extras as Record<string, unknown>) : undefined;
  const librarySource = isObjectRecord(value.library_source)
    ? (() => {
        const sourceKey = pickString(value.library_source.key);
        if (!sourceKey) {
          return null;
        }
        return {
          key: sourceKey,
          section: pickString(value.library_source.section) ?? section,
          locale: pickNullableString(value.library_source.locale) ?? locale,
          updated_at: pickNullableString(value.library_source.updated_at) ?? null,
          updated_by: pickNullableString(value.library_source.updated_by) ?? null,
          thumbnail_url: pickNullableString(value.library_source.thumbnail_url) ?? null,
          sync_state: pickNullableString(value.library_source.sync_state) ?? null,
        };
      })()
    : null;
  const localeStatuses = Array.isArray(value.locale_statuses)
    ? value.locale_statuses
        .map((entry) => {
          if (!isObjectRecord(entry)) {
            return null;
          }
          const localeCode = pickString(entry.locale);
          if (!localeCode) {
            return null;
          }
          return {
            locale: localeCode,
            required: Boolean(entry.required),
            status: pickString(entry.status) ?? 'unknown',
          };
        })
        .filter((entry): entry is { locale: string; required: boolean; status: string } => entry != null)
    : undefined;
  const componentSchema = isObjectRecord(value.component_schema)
    ? (() => {
        const schemaKey = pickString(value.component_schema.key);
        const schemaVersion = pickString(value.component_schema.version);
        const schemaUrl = pickString(value.component_schema.schema_url);
        if (!schemaKey || !schemaVersion || !schemaUrl) {
          return null;
        }
        return {
          key: schemaKey,
          version: schemaVersion,
          schema_url: schemaUrl,
        };
      })()
    : null;

  return {
    id,
    key,
    title,
    template_id: templateId,
    template_key: templateKey ?? undefined,
    section,
    locale,
    scope,
    default_locale: defaultLocale,
    available_locales: availableLocales ?? undefined,
    status,
    review_status: reviewStatus,
    requires_publisher: requiresPublisher,
    published_version: publishedVersion,
    draft_version: draftVersion,
    version,
    usage_count: usageCount,
    comment,
    data,
    meta,
    updated_at: updatedAt,
    updated_by: updatedBy,
    created_at: createdAt,
    created_by: createdBy,
    last_used_at: lastUsedAt,
    has_pending_publish: hasPendingPublish ?? null,
    extras,
    is_template: isTemplate,
    origin_block_id: originBlockId,
    library_source: librarySource,
    locale_statuses: localeStatuses,
    component_schema: componentSchema,
  };
}

export function normalizeBlockUsage(value: unknown): SiteBlockUsage | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const blockId = pickString(value.block_id);
  const pageId = pickString(value.page_id);
  const slug = pickString(value.slug);
  const title = pickString(value.title);
  const statusRaw = pickString(value.status) ?? 'draft';
  const status = PAGE_STATUSES.includes(statusRaw as typeof PAGE_STATUSES[number])
    ? (statusRaw as typeof PAGE_STATUSES[number])
    : 'draft';
  if (!blockId || !pageId || !slug || !title) {
    return null;
  }
  const section = pickString(value.section) ?? 'general';
  const scopeRaw = pickNullableString(value.scope) ?? null;
  const scope = scopeRaw === 'shared' || scopeRaw === 'page' ? scopeRaw : null;
  const defaultLocale = pickNullableString(value.default_locale) ?? null;
  const statusLabel = pickNullableString(value.status_label) ?? null;
  return {
    block_id: blockId,
    page_id: pageId,
    slug,
    title,
    status,
    section,
    locale: pickNullableString(value.locale) ?? null,
    has_draft: pickBoolean(value.has_draft) ?? null,
    has_draft_binding: pickBoolean(value.has_draft_binding) ?? null,
    last_published_at: pickNullableString(value.last_published_at) ?? null,
    owner: pickNullableString(value.owner) ?? null,
    scope,
    default_locale: defaultLocale,
    status_label: statusLabel,
  };
}

export function normalizeBlockWarning(value: unknown): SiteBlockWarning | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const code = pickString(value.code);
  const pageId = pickString(value.page_id);
  const message = pickString(value.message);
  if (!code || !pageId || !message) {
    return null;
  }
  return { code, page_id: pageId, message, title: pickNullableString(value.title) ?? null };
}

export function normalizeBlockPublishJob(value: unknown): SiteBlockPublishJob | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const jobId = pickString(value.job_id);
  const type = pickString(value.type);
  const status = pickString(value.status);
  if (!jobId || !type || !status) {
    return null;
  }
  return { job_id: jobId, type, status };
}

export function normalizeBlockHistoryItem(
  value: unknown,
): SiteBlockHistoryItem | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  const blockId = pickString(value.block_id);
  const version = pickNumber(value.version);
  if (!id || !blockId || !Number.isFinite(version)) {
    return null;
  }
  const data = isObjectRecord(value.data) ? (value.data as Record<string, unknown>) : {};
  const meta = isObjectRecord(value.meta) ? (value.meta as Record<string, unknown>) : {};
  const diff = ensureArray<SitePageDiffEntry>(value.diff, normalizeDiffEntry);
  let sharedBindings = ensureArray(
    value.shared_bindings,
    normalizePageAttachedBlock,
  ).filter((item): item is SitePageAttachedBlock => item != null);
  if (!sharedBindings.length) {
    sharedBindings = ensureArray(
      (value as Record<string, unknown>).bindings,
      normalizePageAttachedBlock,
    ).filter((item): item is SitePageAttachedBlock => item != null);
  }
  return {
    id,
    block_id: blockId,
    version: version as number,
    data,
    meta,
    comment: pickNullableString(value.comment) ?? null,
    diff,
    published_at: pickNullableString(value.published_at) ?? null,
    published_by: pickNullableString(value.published_by) ?? null,
    created_at: pickNullableString(value.created_at) ?? null,
    created_by: pickNullableString(value.created_by) ?? null,
  };
}

export function normalizeDiffEntry(value: unknown): SitePageDiffEntry | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const type = pickString(value.type);
  const change = pickString(value.change);
  if (!type || !change) {
    return null;
  }

  if (type === 'block') {
    const blockId =
      pickString(value.blockId) ?? pickString((value as Record<string, unknown>)['block_id']);
    if (!blockId) {
      return null;
    }
    const before = isObjectRecord(value.before) ? (value.before as Record<string, unknown>) : null;
    const after = isObjectRecord(value.after) ? (value.after as Record<string, unknown>) : null;
    const from = Number.isFinite(value.from) ? Number(value.from) : null;
    const to = Number.isFinite(value.to) ? Number(value.to) : null;
    const allowedChanges = new Set<SitePageDiffEntry['change']>([
      'added',
      'removed',
      'updated',
      'moved',
    ]);
    const normalizedChange = allowedChanges.has(change as SitePageDiffEntry['change'])
      ? (change as SitePageDiffEntry['change'])
      : 'updated';
    return {
      type: 'block',
      blockId,
      change: normalizedChange,
      before,
      after,
      from,
      to,
    };
  }

  if (type === 'data' || type === 'meta') {
    const field = pickString(value.field);
    if (!field) {
      return null;
    }
    const allowedChanges = new Set<Exclude<SitePageDiffEntry['change'], 'moved'>>([
      'added',
      'removed',
      'updated',
    ]);
    const normalizedChange = allowedChanges.has(change as Exclude<SitePageDiffEntry['change'], 'moved'>)
      ? (change as Exclude<SitePageDiffEntry['change'], 'moved'>)
      : 'updated';
    return {
      type,
      field,
      change: normalizedChange,
      before: (value as Record<string, unknown>).before,
      after: (value as Record<string, unknown>).after,
    };
  }

  return null;
}

export function normalizePageVersion(value: unknown): SitePageVersion | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  const pageId = pickString(value.page_id) ?? pickString(value.pageId);
  const version = pickNumber(value.version);
  if (!id || !pageId || !Number.isFinite(version)) {
    return null;
  }
  const data = isObjectRecord(value.data) ? (value.data as Record<string, unknown>) : {};
  const meta = isObjectRecord(value.meta) ? (value.meta as Record<string, unknown>) : {};
  const diff = ensureArray<SitePageDiffEntry>(value.diff, normalizeDiffEntry);
  let sharedBindings = ensureArray(
    value.shared_bindings,
    normalizePageAttachedBlock,
  ).filter((item): item is SitePageAttachedBlock => item != null);
  if (!sharedBindings.length) {
    sharedBindings = ensureArray(
      (value as Record<string, unknown>).bindings,
      normalizePageAttachedBlock,
    ).filter((item): item is SitePageAttachedBlock => item != null);
  }

  return {
    id,
    page_id: pageId,
    version: version as number,
    data,
    meta,
    comment: pickNullableString(value.comment) ?? null,
    diff: diff.length ? diff : null,
    published_at: pickNullableString(value.published_at),
    published_by: pickNullableString(value.published_by),
    shared_bindings: sharedBindings.length ? sharedBindings : undefined,
  };
}

export function normalizePreviewLayout(value: unknown): SitePagePreviewLayout | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const layout = pickString(value.layout) ?? '';
  const generatedAt = pickString(value.generated_at) ?? '';
  const data = isObjectRecord(value.data) ? (value.data as Record<string, unknown>) : {};
  const meta = isObjectRecord(value.meta) ? (value.meta as Record<string, unknown>) : {};
  const payload = isObjectRecord(value.payload) ? (value.payload as Record<string, unknown>) : undefined;
  return {
    layout: layout || 'desktop',
    generated_at: generatedAt || '',
    data,
    meta,
    payload,
  };
}

export function normalizePreviewResponse(value: unknown): SitePagePreviewResponse {
  if (!isObjectRecord(value)) {
    throw new Error('site_page_preview_invalid_response');
  }
  const page = normalizePage((value as Record<string, unknown>).page);
  if (!page) {
    throw new Error('site_page_preview_invalid_page');
  }
  const layoutsRaw = isObjectRecord((value as Record<string, unknown>).layouts)
    ? ((value as Record<string, unknown>).layouts as Record<string, unknown>)
    : {};
  const layouts: Record<string, SitePagePreviewLayout> = {};
  for (const [key, rawLayout] of Object.entries(layoutsRaw)) {
    const normalized = normalizePreviewLayout(rawLayout);
    if (!normalized) {
      continue;
    }
    const layoutKey = key || normalized.layout;
    layouts[layoutKey] = {
      ...normalized,
      layout: normalized.layout || layoutKey,
    };
  }
  const previewRaw = (value as Record<string, unknown>).preview;
  const preview = isObjectRecord(previewRaw)
    ? (previewRaw as SitePagePreviewDocument)
    : null;

  const variantsRaw = Array.isArray((value as Record<string, unknown>).preview_variants)
    ? ((value as Record<string, unknown>).preview_variants as unknown[])
    : [];
  const previewVariants: SitePagePreviewVariant[] = [];
  for (const rawVariant of variantsRaw) {
    if (!isObjectRecord(rawVariant)) {
      continue;
    }
    const layout = pickString(rawVariant.layout);
    const responseDoc = isObjectRecord(rawVariant.response)
      ? (rawVariant.response as SitePagePreviewDocument)
      : null;
    if (!layout || !responseDoc) {
      continue;
    }
    previewVariants.push({
      layout,
      response: responseDoc,
    });
  }

  const defaultLocale = pickString((value as Record<string, unknown>).default_locale) ?? null;
  const availableLocalesRaw = Array.isArray((value as Record<string, unknown>).available_locales)
    ? ((value as Record<string, unknown>).available_locales as unknown[])
    : [];
  const availableLocales = availableLocalesRaw.filter(
    (entry): entry is string => typeof entry === 'string' && entry.trim().length > 0,
  );

  const localizedSlugs = isObjectRecord((value as Record<string, unknown>).localized_slugs)
    ? Object.fromEntries(
        Object.entries(
          (value as Record<string, unknown>).localized_slugs as Record<string, unknown>,
        ).map(([key, slug]) => [key, pickString(slug) ?? '']),
      )
    : undefined;

  const shared = isObjectRecord((value as Record<string, unknown>).shared)
    ? ((value as Record<string, unknown>).shared as Record<string, unknown>)
    : null;

  const locales = isObjectRecord((value as Record<string, unknown>).locales)
    ? ((value as Record<string, unknown>).locales as Record<string, SitePagePreviewLocale>)
    : null;

  const metaLocalized = isObjectRecord((value as Record<string, unknown>).meta_localized)
    ? ((value as Record<string, unknown>).meta_localized as Record<string, unknown>)
    : undefined;

  const bindings = ensureArray(
    (value as Record<string, unknown>).bindings,
    normalizePageAttachedBlock,
  ).filter((item): item is SitePageAttachedBlock => item != null);

  const blockRefs = Array.isArray((value as Record<string, unknown>).block_refs)
    ? ((value as Record<string, unknown>).block_refs as unknown[])
        .filter(isObjectRecord)
        .map((entry) => entry as SitePageBlockReference)
    : [];

  if (preview && previewVariants.length === 0) {
    previewVariants.push({
      layout: 'default',
      response: preview,
    });
  }

  return {
    page,
    draft_version: pickNumber((value as Record<string, unknown>).draft_version) ?? 0,
    published_version: pickNumber((value as Record<string, unknown>).published_version) ?? null,
    requested_version: pickNumber((value as Record<string, unknown>).requested_version) ?? null,
    version_mismatch: pickBoolean((value as Record<string, unknown>).version_mismatch) ?? false,
    bindings,
    shared_bindings: bindings.length ? bindings : undefined,
    block_refs: blockRefs,
    default_locale: defaultLocale,
    available_locales: availableLocales.length ? availableLocales : undefined,
    localized_slugs: localizedSlugs,
    preview: preview ?? undefined,
    preview_variants: previewVariants.length ? previewVariants : undefined,
    shared,
    locales,
    layouts,
    meta_localized: metaLocalized,
  };
}

export function normalizeAuditEntry(value: unknown): SiteAuditEntry | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  const entityType = pickString(value.entity_type);
  const entityId = pickString(value.entity_id);
  const action = pickString(value.action);
  const createdAt = pickString(value.created_at);
  if (!id || !entityType || !entityId || !action || !createdAt) {
    return null;
  }
  const snapshot = isObjectRecord(value.snapshot) ? (value.snapshot as Record<string, unknown>) : null;
  return {
    id,
    entity_type: entityType,
    entity_id: entityId,
    action,
    snapshot,
    actor: pickNullableString(value.actor) ?? null,
    created_at: createdAt,
  };
}

export function normalizeBlockPreviewItem(value: unknown): SiteBlockPreviewItem | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const title = pickString(value.title);
  if (!title) {
    return null;
  }
  return {
    id: pickNullableString(value.id) ?? pickNullableString(value.slug),
    title,
    subtitle: pickNullableString(value.subtitle),
    href: pickNullableString(value.href),
    badge: pickNullableString(value.badge),
    provider: pickNullableString(value.provider),
    score: pickNumber(value.score) ?? null,
    probability: pickNumber(value.probability) ?? null,
  };
}

export function normalizeBlockPreviewResponse(
  block: string,
  value: unknown,
): SiteBlockPreviewResponse {
  if (!isObjectRecord(value)) {
    return {
      block,
      locale: 'ru',
      items: [],
      source: 'mock',
      fetched_at: new Date().toISOString(),
      meta: {},
    };
  }
  const blockId = pickString(value.block) ?? block;
  const locale = pickString(value.locale) ?? 'ru';
  const items = ensureArray(value.items, normalizeBlockPreviewItem).filter(
    (item): item is SiteBlockPreviewItem => item != null,
  );
  const source = pickString(value.source) ?? (items.length ? 'live' : 'mock');
  const fetchedAt =
    pickString(value.fetched_at) ??
    pickString((value as Record<string, unknown>).fetchedAt) ??
    new Date().toISOString();
  const meta = isObjectRecord(value.meta) ? (value.meta as Record<string, unknown>) : {};
  return {
    block: blockId,
    locale,
    items,
    source,
    fetched_at: fetchedAt,
    meta,
  };
}

export function normalizeMetricValueRecord(value: unknown): SiteMetricValue {
  if (!isObjectRecord(value)) {
    return { value: null };
  }
  const metric: SiteMetricValue = {
    value: pickNumber(value.value) ?? null,
  };
  const delta = pickNumber(value.delta);
  if (delta != null && Number.isFinite(delta)) {
    metric.delta = delta;
  }
  const unit = pickString(value.unit);
  if (unit) {
    metric.unit = unit;
  }
  const trendRaw = (value as Record<string, unknown>).trend;
  if (Array.isArray(trendRaw)) {
    const trendValues = trendRaw
      .map((item) => (typeof item === 'number' ? item : Number(item)))
      .filter((item) => Number.isFinite(item));
    if (trendValues.length) {
      metric.trend = trendValues as number[];
    }
  }
  return metric;
}

export function normalizeMetricAlertRecord(value: unknown): SiteMetricAlert | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const code = pickString(value.code);
  const message = pickString(value.message);
  if (!code || !message) {
    return null;
  }
  const severity = pickString(value.severity);
  const normalizedSeverity: SiteMetricAlert['severity'] =
    severity === 'critical' || severity === 'warning' || severity === 'info'
      ? severity
      : 'info';
  return {
    code,
    message,
    severity: normalizedSeverity,
  };
}

export function normalizeMetricsRange(value: unknown): SiteMetricsRange {
  if (!isObjectRecord(value)) {
    return { start: '', end: '' };
  }
  return {
    start: pickString(value.start) ?? '',
    end: pickString(value.end) ?? '',
  };
}

export function normalizePageMetricsResponse(value: unknown): SitePageMetricsResponse {
  if (!isObjectRecord(value)) {
    return {
      page_id: '',
      period: '7d',
      range: { start: '', end: '' },
      status: 'no_data',
      metrics: {},
      alerts: [],
    };
  }
  const metricsRaw = isObjectRecord(value.metrics) ? value.metrics : {};
  const metrics: Record<string, SiteMetricValue> = {};
  for (const [key, metricValue] of Object.entries(metricsRaw)) {
    metrics[key] = normalizeMetricValueRecord(metricValue);
  }
  const alerts = ensureArray(value.alerts, normalizeMetricAlertRecord).filter(
    (alert): alert is SiteMetricAlert => alert != null,
  );
  const payload: SitePageMetricsResponse = {
    page_id: pickString(value.page_id) ?? '',
    period: pickString(value.period) ?? '7d',
    range: normalizeMetricsRange(value.range),
    status: pickString(value.status) ?? 'unknown',
    source_lag_ms: pickNumber(value.source_lag_ms) ?? null,
    metrics,
    alerts,
  };
  if (isObjectRecord(value.previous_range)) {
    payload.previous_range = normalizeMetricsRange(value.previous_range);
  }
  return payload;
}

export function normalizeBlockMetricsTopPage(value: unknown): SiteBlockMetricsTopPage | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const pageId = pickString(value.page_id);
  const slug = pickString(value.slug);
  const title = pickString(value.title);
  if (!pageId || !slug || !title) {
    return null;
  }
  return {
    page_id: pageId,
    slug,
    title,
    impressions: pickNumber(value.impressions) ?? null,
    clicks: pickNumber(value.clicks) ?? null,
    ctr: pickNumber(value.ctr) ?? null,
  };
}

export function normalizeBlockMetricsResponse(
  value: unknown,
): SiteBlockMetricsResponse {
  if (!isObjectRecord(value)) {
    return {
      block_id: '',
      period: '7d',
      range: { start: '', end: '' },
      status: 'no_data',
      metrics: {},
      alerts: [],
      top_pages: [],
    };
  }
  const metricsRaw = isObjectRecord(value.metrics) ? value.metrics : {};
  const metrics: Record<string, SiteMetricValue> = {};
  for (const [key, metricValue] of Object.entries(metricsRaw)) {
    metrics[key] = normalizeMetricValueRecord(metricValue);
  }
  const alerts = ensureArray(value.alerts, normalizeMetricAlertRecord).filter(
    (alert): alert is SiteMetricAlert => alert != null,
  );
  const topPages = ensureArray(value.top_pages, normalizeBlockMetricsTopPage).filter(
    (item): item is SiteBlockMetricsTopPage => item != null,
  );
  const payload: SiteBlockMetricsResponse = {
    block_id: pickString(value.block_id) ?? '',
    period: pickString(value.period) ?? '7d',
    range: normalizeMetricsRange(value.range),
    status: pickString(value.status) ?? 'unknown',
    source_lag_ms: pickNumber(value.source_lag_ms) ?? null,
    metrics,
    alerts,
    top_pages: topPages,
  };
  if (isObjectRecord(value.previous_range)) {
    payload.previous_range = normalizeMetricsRange(value.previous_range);
  }
  return payload;
}

export function normalizeBlockTemplate(value: unknown): SiteBlockTemplate | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const id = pickString(value.id);
  const key = pickString(value.key);
  const title = pickString(value.title);
  if (!id || !key || !title) {
    return null;
  }
  const section = pickString(value.section) ?? 'general';
  const status = pickString(value.status) ?? 'available';
  const defaultLocale = pickString(value.default_locale) ?? 'ru';
  let availableLocales = Array.isArray(value.available_locales)
    ? value.available_locales
        .map((entry) => (typeof entry === 'string' && entry.trim() ? entry.trim() : null))
        .filter((entry): entry is string => Boolean(entry))
    : [];
  if (!availableLocales.length) {
    availableLocales = [defaultLocale];
  } else if (!availableLocales.includes(defaultLocale)) {
    availableLocales = [defaultLocale, ...availableLocales];
  }
  const toStringArray = (input: unknown): string[] => {
    if (!input) {
      return [];
    }
    const raw = Array.isArray(input) ? input : String(input).split(',');
    const result: string[] = [];
    for (const entry of raw) {
      const text = typeof entry === 'string' ? entry.trim() : String(entry ?? '').trim();
      if (!text || result.includes(text)) {
        continue;
      }
      result.push(text);
    }
    return result;
  };
  const defaultData = isObjectRecord(value.default_data)
    ? (value.default_data as Record<string, unknown>)
    : {};
  const defaultMeta = isObjectRecord(value.default_meta)
    ? (value.default_meta as Record<string, unknown>)
    : {};
  const sources = toStringArray(value.sources);
  const surfaces = toStringArray(value.surfaces);
  const owners = toStringArray(value.owners);
  const catalogLocales = toStringArray(value.catalog_locales);
  const keywords = toStringArray(value.keywords);
  const requiresPublisher = pickBoolean(value.requires_publisher) ?? false;
  const allowSharedScope = pickBoolean(value.allow_shared_scope);
  const allowPageScope = pickBoolean(value.allow_page_scope);
  return {
    id,
    key,
    title,
    section,
    status,
    description: pickNullableString(value.description) ?? null,
    default_locale: defaultLocale,
    available_locales: availableLocales,
    default_data: defaultData,
    default_meta: defaultMeta,
    block_type: pickNullableString(value.block_type),
    category: pickNullableString(value.category),
    sources,
    surfaces,
    owners,
    catalog_locales: catalogLocales,
    documentation_url: pickNullableString(value.documentation_url),
    keywords,
    preview_kind: pickNullableString(value.preview_kind),
    status_note: pickNullableString(value.status_note),
    requires_publisher: requiresPublisher,
    allow_shared_scope: allowSharedScope ?? true,
    allow_page_scope: allowPageScope ?? true,
    shared_note: pickNullableString(value.shared_note),
    key_prefix: pickNullableString(value.key_prefix),
    created_at: pickNullableString(value.created_at) ?? null,
    created_by: pickNullableString(value.created_by) ?? null,
    updated_at: pickNullableString(value.updated_at) ?? null,
    updated_by: pickNullableString(value.updated_by) ?? null,
  };
}

function normalizePageBlockReference(
  value: unknown,
): SitePageBlockReference | null {
  if (typeof value === 'string') {
    const cleaned = value.trim();
    return cleaned ? { key: cleaned } : null;
  }
  if (!isObjectRecord(value)) {
    return null;
  }
  const key =
    pickString(value.key) ??
    pickString(value.block_key) ??
    pickString(value.id) ??
    pickString(value.block_id);
  if (!key) {
    return null;
  }
  const section = pickNullableString(value.section) ?? pickNullableString(value.zone);
  return { key, section: section ?? undefined };
}

export function normalizePageAttachedBlock(
  value: unknown,
): SitePageAttachedBlock | null {
  const base = normalizePageBlockReference(value);
  if (!base) {
    return null;
  }
  const record = isObjectRecord(value) ? value : {};
  const statusRaw = pickString(record.status);
  const reviewStatusRaw = pickString(record.review_status);
  const status = BLOCK_STATUSES.includes(
    statusRaw as typeof BLOCK_STATUSES[number],
  )
    ? (statusRaw as SitePageAttachedBlock['status'])
    : statusRaw || undefined;
  const reviewStatus =
    reviewStatusRaw && REVIEW_STATUSES.has(reviewStatusRaw)
      ? (reviewStatusRaw as SitePageAttachedBlock['review_status'])
      : reviewStatusRaw || undefined;
  const hasDraft = pickBoolean(record.has_draft);
  const hasDraftBinding = pickBoolean(record.has_draft_binding);
  const lastPublishedAt = pickNullableString(record.last_published_at) ?? undefined;
  const owner = pickNullableString(record.owner) ?? undefined;
  const extras = isObjectRecord(record.extras) ? (record.extras as Record<string, unknown>) : undefined;
  return {
    ...base,
    block_id: pickNullableString(record.block_id) ?? pickNullableString(record.id) ?? undefined,
    title: pickNullableString(record.title) ?? undefined,
    status,
    locale: pickNullableString(record.locale) ?? undefined,
    requires_publisher: pickBoolean(record.requires_publisher) ?? undefined,
    published_version: pickNumber(record.published_version) ?? undefined,
    draft_version: pickNumber(record.draft_version) ?? undefined,
    review_status: reviewStatus,
    updated_at: pickNullableString(record.updated_at) ?? undefined,
    updated_by: pickNullableString(record.updated_by) ?? undefined,
    has_draft: hasDraft ?? undefined,
    has_draft_binding: hasDraftBinding ?? undefined,
    last_published_at: lastPublishedAt,
    owner,
    extras,
  };
}





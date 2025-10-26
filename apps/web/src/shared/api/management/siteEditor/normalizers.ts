import type {
  SiteAuditEntry,
  SiteDraftValidationResult,
  SiteGlobalBlock,
  SiteGlobalBlockHistoryItem,
  SiteGlobalBlockMetricsResponse,
  SiteGlobalBlockPublishJob,
  SiteGlobalBlockUsage,
  SiteGlobalBlockWarning,
  SiteBlockMetricsTopPage,
  SiteMetricAlert,
  SiteMetricValue,
  SiteMetricsRange,
  SitePageDiffEntry,
  SitePageDraft,
  SitePageMetricsResponse,
  SitePagePreviewLayout,
  SitePagePreviewResponse,
  SitePageSummary,
  SitePageVersion,
  SiteValidationErrorEntry,
} from '@shared/types/management';

import {
  GLOBAL_BLOCK_STATUSES,
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

  return {
    id,
    slug,
    title,
    type,
    status,
    locale: pickString(value.locale) ?? 'ru',
    owner: pickNullableString(value.owner),
    updated_at: pickNullableString(value.updated_at),
    published_version: publishedVersion ?? null,
    draft_version: draftVersion ?? null,
    has_pending_review: pickBoolean(value.has_pending_review) ?? null,
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

  return {
    page_id: pageId,
    version: version as number,
    data,
    meta,
    comment: pickNullableString(value.comment) ?? null,
    review_status: reviewStatus,
    updated_at: pickNullableString(value.updated_at),
    updated_by: pickNullableString(value.updated_by),
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

export function normalizeGlobalBlock(value: unknown): SiteGlobalBlock | null {
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
  const locale = pickNullableString(value.locale) ?? null;
  const statusRaw = pickString(value.status) ?? 'draft';
  const status = GLOBAL_BLOCK_STATUSES.includes(statusRaw as typeof GLOBAL_BLOCK_STATUSES[number])
    ? (statusRaw as typeof GLOBAL_BLOCK_STATUSES[number])
    : 'draft';
  const reviewStatusRaw = pickString(value.review_status) ?? 'none';
  const reviewStatus = REVIEW_STATUSES.has(reviewStatusRaw)
    ? (reviewStatusRaw as SiteGlobalBlock['review_status'])
    : 'none';
  const requiresPublisher = pickBoolean(value.requires_publisher) ?? false;
  const publishedVersion = pickNumber(value.published_version) ?? null;
  const draftVersion = pickNumber(value.draft_version) ?? null;
  const usageCount = pickNumber(value.usage_count) ?? null;
  const comment = pickNullableString(value.comment) ?? null;
  const data = isObjectRecord(value.data) ? (value.data as Record<string, unknown>) : undefined;
  const meta = isObjectRecord(value.meta) ? (value.meta as Record<string, unknown>) : undefined;
  const updatedAt = pickNullableString(value.updated_at) ?? null;
  const updatedBy = pickNullableString(value.updated_by) ?? null;
  const hasPendingPublish = pickBoolean(value.has_pending_publish);

  return {
    id,
    key,
    title,
    section,
    locale,
    status,
    review_status: reviewStatus,
    requires_publisher: requiresPublisher,
    published_version: publishedVersion,
    draft_version: draftVersion,
    usage_count: usageCount,
    comment,
    data,
    meta,
    updated_at: updatedAt,
    updated_by: updatedBy,
    has_pending_publish: hasPendingPublish ?? null,
  };
}

export function normalizeGlobalBlockUsage(value: unknown): SiteGlobalBlockUsage | null {
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
  return {
    block_id: blockId,
    page_id: pageId,
    slug,
    title,
    status,
    section,
    locale: pickNullableString(value.locale) ?? null,
    has_draft: pickBoolean(value.has_draft) ?? null,
    last_published_at: pickNullableString(value.last_published_at) ?? null,
  };
}

export function normalizeGlobalBlockWarning(value: unknown): SiteGlobalBlockWarning | null {
  if (!isObjectRecord(value)) {
    return null;
  }
  const code = pickString(value.code);
  const pageId = pickString(value.page_id);
  const message = pickString(value.message);
  if (!code || !pageId || !message) {
    return null;
  }
  return { code, page_id: pageId, message };
}

export function normalizeGlobalBlockPublishJob(value: unknown): SiteGlobalBlockPublishJob | null {
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

export function normalizeGlobalBlockHistoryItem(
  value: unknown,
): SiteGlobalBlockHistoryItem | null {
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
  return {
    layout: layout || 'desktop',
    generated_at: generatedAt || '',
    data,
    meta,
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
  return {
    page,
    draft_version: pickNumber((value as Record<string, unknown>).draft_version) ?? 0,
    published_version: pickNumber((value as Record<string, unknown>).published_version) ?? null,
    requested_version: pickNumber((value as Record<string, unknown>).requested_version) ?? null,
    version_mismatch: pickBoolean((value as Record<string, unknown>).version_mismatch) ?? false,
    layouts,
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
): SiteGlobalBlockMetricsResponse {
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
  const payload: SiteGlobalBlockMetricsResponse = {
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

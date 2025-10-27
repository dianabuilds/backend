import { apiGet, apiPost, apiPut } from '../../client';
import {
  ensureArray,
  isObjectRecord,
  pickNullableString,
  pickNumber,
  pickString,
} from '../utils';

import type {
  SiteGlobalBlock,
  SiteGlobalBlockAffectedPage,
  SiteGlobalBlockDetailResponse,
  SiteGlobalBlockHistoryItem,
  SiteGlobalBlockHistoryResponse,
  SiteGlobalBlockListResponse,
  SiteGlobalBlockPublishJob,
  SiteGlobalBlockPublishResponse,
  SiteGlobalBlockUsage,
  SiteGlobalBlockWarning,
  SitePageStatus,
} from '@shared/types/management';

import { GLOBAL_BLOCK_SORT, GLOBAL_BLOCK_STATUSES, PAGE_STATUSES, REVIEW_STATUSES } from './constants';
import {
  normalizeGlobalBlock,
  normalizeGlobalBlockHistoryItem,
  normalizeGlobalBlockPublishJob,
  normalizeGlobalBlockUsage,
  normalizeGlobalBlockWarning,
  normalizeBlockPreviewResponse,
} from './normalizers';
import type {
  CreateSiteGlobalBlockPayload,
  FetchOptions,
  FetchSiteGlobalBlockHistoryParams,
  FetchSiteGlobalBlocksParams,
  PreviewSiteBlockParams,
  PublishSiteGlobalBlockPayload,
  SaveSiteGlobalBlockPayload,
  SiteBlockPreviewResponse,
} from './types';

export async function fetchSiteGlobalBlocks(
  params: FetchSiteGlobalBlocksParams = {},
  options: FetchOptions = {},
): Promise<SiteGlobalBlockListResponse> {
  const searchParams = new URLSearchParams();
  const page = Number.isFinite(params.page) && params.page ? Math.max(1, Math.trunc(params.page)) : 1;
  const pageSize =
    Number.isFinite(params.pageSize) && params.pageSize ? Math.max(1, Math.trunc(params.pageSize)) : 20;
  searchParams.set('page', String(page));
  searchParams.set('page_size', String(pageSize));
  if (params.section) {
    searchParams.set('section', params.section);
  }
  if (
    params.status &&
    GLOBAL_BLOCK_STATUSES.includes(params.status as typeof GLOBAL_BLOCK_STATUSES[number])
  ) {
    const status = params.status as typeof GLOBAL_BLOCK_STATUSES[number];
    searchParams.set('status', status);
  }
  if (params.locale) {
    searchParams.set('locale', params.locale);
  }
  if (params.query) {
    searchParams.set('q', params.query);
  }
  if (typeof params.hasDraft === 'boolean') {
    searchParams.set('has_draft', String(params.hasDraft));
  }
  if (typeof params.requiresPublisher === 'boolean') {
    searchParams.set('requires_publisher', String(params.requiresPublisher));
  }
  if (params.reviewStatus && REVIEW_STATUSES.has(params.reviewStatus)) {
    searchParams.set('review_status', params.reviewStatus);
  }
  if (params.sort && GLOBAL_BLOCK_SORT.has(params.sort)) {
    searchParams.set('sort', params.sort);
  }

  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/global-blocks?${searchParams.toString()}`,
    options,
  );
  const items = ensureArray(response?.items, normalizeGlobalBlock).filter(
    (entry): entry is SiteGlobalBlock => entry != null,
  );
  return {
    items,
    page: pickNumber(response?.page) ?? page,
    page_size: pickNumber(response?.page_size) ?? pageSize,
    total: pickNumber(response?.total) ?? items.length,
  };
}

export async function fetchSiteGlobalBlock(
  blockId: string,
  options: FetchOptions = {},
): Promise<SiteGlobalBlockDetailResponse> {
  if (!blockId) {
    throw new Error('site_global_block_missing_id');
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/global-blocks/${encodeURIComponent(blockId)}`,
    options,
  );
  const block = normalizeGlobalBlock(response?.block ?? response);
  if (!block) {
    throw new Error('site_global_block_invalid_response');
  }
  const usage = ensureArray(response?.usage, normalizeGlobalBlockUsage).filter(
    (entry): entry is SiteGlobalBlockUsage => entry != null,
  );
  const warnings = ensureArray(response?.warnings, normalizeGlobalBlockWarning).filter(
    (entry): entry is SiteGlobalBlockWarning => entry != null,
  );
  return { block, usage, warnings };
}

export async function createSiteGlobalBlock(
  payload: CreateSiteGlobalBlockPayload,
  options: FetchOptions = {},
): Promise<SiteGlobalBlock> {
  if (!payload?.key || !payload?.title || !payload?.section) {
    throw new Error('site_global_block_invalid_payload');
  }
  const body: Record<string, unknown> = {
    key: payload.key,
    title: payload.title,
    section: payload.section,
  };
  if (payload.locale != null) {
    body.locale = payload.locale;
  }
  if (payload.requires_publisher != null) {
    body.requires_publisher = Boolean(payload.requires_publisher);
  }
  if (payload.data) {
    body.data = payload.data;
  }
  if (payload.meta) {
    body.meta = payload.meta;
  }
  const response = await apiPost<Record<string, unknown>>('/v1/site/global-blocks', body, options);
  const block = normalizeGlobalBlock(response);
  if (!block) {
    throw new Error('site_global_block_invalid_response');
  }
  return block;
}

export async function saveSiteGlobalBlock(
  blockId: string,
  payload: SaveSiteGlobalBlockPayload,
  options: FetchOptions = {},
): Promise<SiteGlobalBlock> {
  if (!blockId) {
    throw new Error('site_global_block_missing_id');
  }
  const body: Record<string, unknown> = {};
  if (payload.version != null) {
    body.version = payload.version;
  }
  if (payload.data) {
    body.data = payload.data;
  }
  if (payload.meta) {
    body.meta = payload.meta;
  }
  if (payload.comment != null) {
    body.comment = payload.comment;
  }
  if (payload.review_status && REVIEW_STATUSES.has(payload.review_status)) {
    body.review_status = payload.review_status;
  }
  const response = await apiPut<Record<string, unknown>>(
    `/v1/site/global-blocks/${encodeURIComponent(blockId)}`,
    body,
    options,
  );
  const block = normalizeGlobalBlock(response);
  if (!block) {
    throw new Error('site_global_block_invalid_response');
  }
  return block;
}

export async function publishSiteGlobalBlock(
  blockId: string,
  payload: PublishSiteGlobalBlockPayload = {},
  options: FetchOptions = {},
): Promise<SiteGlobalBlockPublishResponse> {
  if (!blockId) {
    throw new Error('site_global_block_missing_id');
  }
  const body: Record<string, unknown> = {};
  if (payload.version != null) {
    body.version = payload.version;
  }
  if (payload.comment != null) {
    body.comment = payload.comment;
  }
  body.acknowledge_usage = payload.acknowledgeUsage ?? true;
  const response = await apiPost<Record<string, unknown>>(
    `/v1/site/global-blocks/${encodeURIComponent(blockId)}/publish`,
    body,
    options,
  );
  const block = normalizeGlobalBlock(response?.block ?? response);
  if (!block) {
    throw new Error('site_global_block_publish_invalid_response');
  }
  const usage = ensureArray(response?.usage, normalizeGlobalBlockUsage).filter(
    (entry): entry is SiteGlobalBlockUsage => entry != null,
  );
  const jobs = ensureArray(response?.jobs, normalizeGlobalBlockPublishJob).filter(
    (entry): entry is SiteGlobalBlockPublishJob => entry != null,
  );
  const affected = ensureArray(response?.affected_pages, (value): SiteGlobalBlockAffectedPage | null => {
    if (!isObjectRecord(value)) {
      return null;
    }
    const pageId = pickString(value.page_id);
    const slug = pickString(value.slug);
    const title = pickString(value.title);
    const statusRaw = pickString(value.status) ?? 'draft';
    const status = PAGE_STATUSES.includes(statusRaw as typeof PAGE_STATUSES[number])
      ? (statusRaw as typeof PAGE_STATUSES[number])
      : 'draft';
    if (!pageId || !slug || !title) {
      return null;
    }
    return {
      page_id: pageId,
      slug,
      title,
      status: status as SitePageStatus,
      republish_status: pickNullableString(value.republish_status) ?? null,
    };
  });
  const auditId = pickString(response?.audit_id) ?? '';
  const publishedVersion = pickNumber(response?.published_version) ?? block.published_version ?? null;
  const id = pickString(response?.id) ?? block.id;
  return {
    id,
    published_version: publishedVersion,
    affected_pages: affected,
    jobs,
    audit_id: auditId,
    block,
    usage,
  };
}

export async function fetchSiteGlobalBlockHistory(
  blockId: string,
  params: FetchSiteGlobalBlockHistoryParams = {},
  options: FetchOptions = {},
): Promise<SiteGlobalBlockHistoryResponse> {
  if (!blockId) {
    throw new Error('site_global_block_missing_id');
  }
  const limit = Number.isFinite(params.limit) && params.limit ? Math.max(1, Math.trunc(params.limit)) : 10;
  const offset =
    Number.isFinite(params.offset) && params.offset ? Math.max(0, Math.trunc(params.offset)) : 0;
  const searchParams = new URLSearchParams();
  searchParams.set('limit', String(limit));
  searchParams.set('offset', String(offset));
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/global-blocks/${encodeURIComponent(blockId)}/history?${searchParams.toString()}`,
    options,
  );
  const items = ensureArray(response?.items, normalizeGlobalBlockHistoryItem).filter(
    (entry): entry is SiteGlobalBlockHistoryItem => entry != null,
  );
  return {
    items,
    total: pickNumber(response?.total) ?? items.length,
    limit: pickNumber(response?.limit) ?? limit,
    offset: pickNumber(response?.offset) ?? offset,
  };
}

export async function fetchSiteGlobalBlockVersion(
  blockId: string,
  version: number,
  options: FetchOptions = {},
): Promise<SiteGlobalBlockHistoryItem | null> {
  if (!blockId || !Number.isFinite(version)) {
    return null;
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/global-blocks/${encodeURIComponent(blockId)}/history/${version}`,
    options,
  );
  return normalizeGlobalBlockHistoryItem(response);
}

export async function restoreSiteGlobalBlockVersion(
  blockId: string,
  version: number,
  options: FetchOptions = {},
): Promise<SiteGlobalBlockDetailResponse> {
  if (!blockId || !Number.isFinite(version)) {
    throw new Error('site_global_block_restore_invalid_params');
  }
  const response = await apiPost<Record<string, unknown>>(
    `/v1/site/global-blocks/${encodeURIComponent(blockId)}/history/${version}/restore`,
    {},
    options,
  );
  const block = normalizeGlobalBlock(response?.block ?? response);
  if (!block) {
    throw new Error('site_global_block_restore_invalid_response');
  }
  const usage = ensureArray(response?.usage, normalizeGlobalBlockUsage).filter(
    (entry): entry is SiteGlobalBlockUsage => entry != null,
  );
  const warnings = ensureArray(response?.warnings, normalizeGlobalBlockWarning).filter(
    (entry): entry is SiteGlobalBlockWarning => entry != null,
  );
  return { block, usage, warnings };
}

export async function previewSiteBlock(
  block: string,
  params: PreviewSiteBlockParams = {},
  options: FetchOptions = {},
): Promise<SiteBlockPreviewResponse> {
  const search = new URLSearchParams();
  if (params.locale) {
    search.append('locale', params.locale);
  }
  if (typeof params.limit === 'number') {
    search.append('limit', String(params.limit));
  }
  const query = search.toString();
  const path = `/v1/site/blocks/${encodeURIComponent(block)}/preview${query ? `?${query}` : ''}`;
  const response = await apiGet<Record<string, unknown>>(path, options);
  return normalizeBlockPreviewResponse(block, response);
}

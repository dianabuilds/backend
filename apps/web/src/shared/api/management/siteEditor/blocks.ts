import { apiGet, apiPost, apiPut } from '../../client';
import {
  ensureArray,
  isObjectRecord,
  pickNullableString,
  pickNumber,
  pickString,
} from '../utils';

import type {
  SiteBlock,
  SiteBlockAffectedPage,
  SiteBlockDetailResponse,
  SiteBlockHistoryItem,
  SiteBlockHistoryResponse,
  SiteBlockListResponse,
  SiteBlockPublishJob,
  SiteBlockPublishResponse,
  SiteBlockTemplate,
  SiteBlockUsage,
  SiteBlockWarning,
  SitePageStatus,
} from '@shared/types/management';

import { BLOCK_SORT, BLOCK_STATUSES, PAGE_STATUSES, REVIEW_STATUSES } from './constants';
import {
  normalizeBlock,
  normalizeBlockHistoryItem,
  normalizeBlockPublishJob,
  normalizeBlockTemplate,
  normalizeBlockUsage,
  normalizeBlockWarning,
  normalizeBlockPreviewResponse,
} from './normalizers';
import type {
  ArchiveSiteBlockPayload,
  CreateBlockTemplatePayload,
  CreateSiteBlockPayload,
  FetchBlockTemplatesParams,
  FetchOptions,
  FetchSiteBlockHistoryParams,
  FetchSiteBlocksParams,
  PreviewSiteBlockParams,
  PublishSiteBlockPayload,
  SaveSiteBlockPayload,
  SiteBlockPreviewResponse,
  SiteBlockTemplateDetail,
  SiteBlockTemplateList,
  UpdateBlockTemplatePayload,
} from './types';

export async function fetchSiteBlocks(
  params: FetchSiteBlocksParams = {},
  options: FetchOptions = {},
): Promise<SiteBlockListResponse> {
  const searchParams = new URLSearchParams();
  const page = Number.isFinite(params.page) && params.page ? Math.max(1, Math.trunc(params.page)) : 1;
  const pageSize =
    Number.isFinite(params.pageSize) && params.pageSize ? Math.max(1, Math.trunc(params.pageSize)) : 20;
  searchParams.set('page', String(page));
  searchParams.set('page_size', String(pageSize));
  if (params.section) {
    searchParams.set('section', params.section);
  }
  if (params.status && BLOCK_STATUSES.includes(params.status as typeof BLOCK_STATUSES[number])) {
    searchParams.set('status', params.status as typeof BLOCK_STATUSES[number]);
  }
  if (params.scope) {
    searchParams.set('scope', params.scope);
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
  if (typeof params.isTemplate === 'boolean') {
    searchParams.set('is_template', String(params.isTemplate));
  }
  if (params.originBlockId) {
    searchParams.set('origin_block_id', params.originBlockId);
  }
  if (params.sort && BLOCK_SORT.has(params.sort)) {
    searchParams.set('sort', params.sort);
  }
  if (typeof params.includeData === 'boolean') {
    searchParams.set('include_data', String(params.includeData));
  }

  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/blocks?${searchParams.toString()}`,
    options,
  );
  const items = ensureArray(response?.items, normalizeBlock).filter(
    (entry): entry is SiteBlock => entry != null,
  );
  return {
    items,
    page: pickNumber(response?.page) ?? page,
    page_size: pickNumber(response?.page_size) ?? pageSize,
    total: pickNumber(response?.total) ?? items.length,
  };
}

export async function fetchSiteBlock(
  blockId: string,
  options: FetchOptions = {},
): Promise<SiteBlockDetailResponse> {
  if (!blockId) {
    throw new Error('site_block_missing_id');
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/blocks/${encodeURIComponent(blockId)}`,
    options,
  );
  const block = normalizeBlock(response?.block ?? response);
  if (!block) {
    throw new Error('site_block_invalid_response');
  }
  const usage = ensureArray(response?.usage, normalizeBlockUsage).filter(
    (entry): entry is SiteBlockUsage => entry != null,
  );
  const warnings = ensureArray(response?.warnings, normalizeBlockWarning).filter(
    (entry): entry is SiteBlockWarning => entry != null,
  );
  return { block, usage, warnings };
}

export async function createSiteBlock(
  payload: CreateSiteBlockPayload,
  options: FetchOptions = {},
): Promise<SiteBlock> {
  if (!payload?.key || !payload?.title || !payload?.section) {
    throw new Error('site_block_invalid_payload');
  }
  const response = await apiPost<Record<string, unknown>>('/v1/site/blocks', payload, options);
  const block = normalizeBlock(response);
  if (!block) {
    throw new Error('site_block_create_invalid_response');
  }
  return block;
}

export async function saveSiteBlock(
  blockId: string,
  payload: SaveSiteBlockPayload,
  options: FetchOptions = {},
): Promise<SiteBlock> {
  if (!blockId) {
    throw new Error('site_block_missing_id');
  }
  const response = await apiPut<Record<string, unknown>>(
    `/v1/site/blocks/${encodeURIComponent(blockId)}`,
    payload,
    options,
  );
  const block = normalizeBlock(response);
  if (!block) {
    throw new Error('site_block_update_invalid_response');
  }
  return block;
}

export async function publishSiteBlock(
  blockId: string,
  payload: PublishSiteBlockPayload = {},
  options: FetchOptions = {},
): Promise<SiteBlockPublishResponse> {
  if (!blockId) {
    throw new Error('site_block_publish_missing_id');
  }
  const response = await apiPost<Record<string, unknown>>(
    `/v1/site/blocks/${encodeURIComponent(blockId)}/publish`,
    payload,
    options,
  );
  const block = normalizeBlock(response?.block ?? response);
  if (!block) {
    throw new Error('site_block_publish_invalid_response');
  }
  const usage = ensureArray(response?.usage, normalizeBlockUsage).filter(
    (entry): entry is SiteBlockUsage => entry != null,
  );
  const jobs = ensureArray(response?.jobs, normalizeBlockPublishJob).filter(
    (entry): entry is SiteBlockPublishJob => entry != null,
  );
  const affected = ensureArray(response?.affected_pages, (value): SiteBlockAffectedPage | null => {
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

export async function archiveSiteBlock(
  blockId: string,
  payload: ArchiveSiteBlockPayload = {},
  options: FetchOptions = {},
): Promise<SiteBlockDetailResponse> {
  if (!blockId) {
    throw new Error('site_block_archive_missing_id');
  }
  const response = await apiPost<Record<string, unknown>>(
    `/v1/site/blocks/${encodeURIComponent(blockId)}/archive`,
    payload,
    options,
  );
  const block = normalizeBlock(response?.block ?? response);
  if (!block) {
    throw new Error('site_block_archive_invalid_response');
  }
  const usage = ensureArray(response?.usage, normalizeBlockUsage).filter(
    (entry): entry is SiteBlockUsage => entry != null,
  );
  const warnings = ensureArray(response?.warnings, normalizeBlockWarning).filter(
    (entry): entry is SiteBlockWarning => entry != null,
  );
  return { block, usage, warnings };
}

export async function fetchSiteBlockHistory(
  blockId: string,
  params: FetchSiteBlockHistoryParams = {},
  options: FetchOptions = {},
): Promise<SiteBlockHistoryResponse> {
  if (!blockId) {
    throw new Error('site_block_missing_id');
  }
  const limit = Number.isFinite(params.limit) && params.limit ? Math.max(1, Math.trunc(params.limit)) : 10;
  const offset =
    Number.isFinite(params.offset) && params.offset ? Math.max(0, Math.trunc(params.offset)) : 0;
  const searchParams = new URLSearchParams();
  searchParams.set('limit', String(limit));
  searchParams.set('offset', String(offset));
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/blocks/${encodeURIComponent(blockId)}/history?${searchParams.toString()}`,
    options,
  );
  const items = ensureArray(response?.items, normalizeBlockHistoryItem).filter(
    (entry): entry is SiteBlockHistoryItem => entry != null,
  );
  return {
    items,
    total: pickNumber(response?.total) ?? items.length,
    limit: pickNumber(response?.limit) ?? limit,
    offset: pickNumber(response?.offset) ?? offset,
  };
}

export async function fetchSiteBlockVersion(
  blockId: string,
  version: number,
  options: FetchOptions = {},
): Promise<SiteBlockHistoryItem | null> {
  if (!blockId || !Number.isFinite(version)) {
    return null;
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/blocks/${encodeURIComponent(blockId)}/history/${version}`,
    options,
  );
  return normalizeBlockHistoryItem(response);
}

export async function restoreSiteBlockVersion(
  blockId: string,
  version: number,
  options: FetchOptions = {},
): Promise<SiteBlockDetailResponse> {
  if (!blockId || !Number.isFinite(version)) {
    throw new Error('site_block_restore_invalid_params');
  }
  const response = await apiPost<Record<string, unknown>>(
    `/v1/site/blocks/${encodeURIComponent(blockId)}/history/${version}/restore`,
    {},
    options,
  );
  const block = normalizeBlock(response?.block ?? response);
  if (!block) {
    throw new Error('site_block_restore_invalid_response');
  }
  const usage = ensureArray(response?.usage, normalizeBlockUsage).filter(
    (entry): entry is SiteBlockUsage => entry != null,
  );
  const warnings = ensureArray(response?.warnings, normalizeBlockWarning).filter(
    (entry): entry is SiteBlockWarning => entry != null,
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

export async function fetchBlockTemplates(
  params: FetchBlockTemplatesParams = {},
  options: FetchOptions = {},
): Promise<SiteBlockTemplateList> {
  const search = new URLSearchParams();
  if (Array.isArray(params.status)) {
    params.status.filter(Boolean).forEach((status) => search.append('status', status));
  } else if (params.status) {
    search.append('status', params.status);
  }
  if (params.section) {
    search.set('section', params.section);
  }
  if (params.query) {
    search.set('q', params.query);
  }
  if (params.includeData === false) {
    search.set('include_data', 'false');
  }
  const query = search.toString();
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/block-templates${query ? `?${query}` : ''}`,
    options,
  );
  const items = ensureArray(response?.items, normalizeBlockTemplate).filter(
    (entry): entry is SiteBlockTemplate => entry != null,
  );
  return {
    items,
    total: pickNumber(response?.total) ?? items.length,
  };
}

export async function fetchBlockTemplate(
  templateId: string,
  options: FetchOptions = {},
): Promise<SiteBlockTemplateDetail> {
  if (!templateId) {
    throw new Error('site_block_template_missing_id');
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/block-templates/${encodeURIComponent(templateId)}`,
    options,
  );
  const template = normalizeBlockTemplate(response);
  if (!template) {
    throw new Error('site_block_template_invalid_response');
  }
  return template;
}

export async function fetchBlockTemplateByKey(
  templateKey: string,
  options: FetchOptions = {},
): Promise<SiteBlockTemplateDetail> {
  if (!templateKey) {
    throw new Error('site_block_template_missing_key');
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/block-templates/by-key/${encodeURIComponent(templateKey)}`,
    options,
  );
  const template = normalizeBlockTemplate(response);
  if (!template) {
    throw new Error('site_block_template_invalid_response');
  }
  return template;
}

export async function createBlockTemplate(
  payload: CreateBlockTemplatePayload,
  options: FetchOptions = {},
): Promise<SiteBlockTemplateDetail> {
  if (!payload?.key || !payload?.title) {
    throw new Error('site_block_template_invalid_payload');
  }
  const response = await apiPost<Record<string, unknown>>(
    '/v1/site/block-templates',
    payload,
    options,
  );
  const template = normalizeBlockTemplate(response);
  if (!template) {
    throw new Error('site_block_template_create_invalid_response');
  }
  return template;
}

export async function updateBlockTemplate(
  templateId: string,
  payload: UpdateBlockTemplatePayload,
  options: FetchOptions = {},
): Promise<SiteBlockTemplateDetail> {
  if (!templateId) {
    throw new Error('site_block_template_missing_id');
  }
  const response = await apiPut<Record<string, unknown>>(
    `/v1/site/block-templates/${encodeURIComponent(templateId)}`,
    payload,
    options,
  );
  const template = normalizeBlockTemplate(response);
  if (!template) {
    throw new Error('site_block_template_update_invalid_response');
  }
  return template;
}

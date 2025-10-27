import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from '../../client';
import { ensureArray, pickNumber } from '../utils';

import type {
  SiteDraftValidationResult,
  SitePageDraft,
  SitePageDraftDiffResponse,
  SitePageHistoryResponse,
  SitePageListResponse,
  SitePagePreviewResponse,
  SitePageSummary,
  SitePageVersion,
} from '@shared/types/management';

import { PAGE_STATUSES, PAGE_TYPES, SORT_ORDERS } from './constants';
import {
  normalizeDiffEntry,
  normalizeDraft,
  normalizePage,
  normalizePreviewResponse,
  normalizeValidationResult,
  normalizePageVersion,
} from './normalizers';
import type {
  FetchOptions,
  CreateSitePagePayload,
  UpdateSitePagePayload,
  FetchSitePageHistoryParams,
  FetchSitePagesParams,
  PreviewSitePagePayload,
  PublishSitePagePayload,
  SaveSitePageDraftPayload,
} from './types';

export async function fetchSitePages(
  params: FetchSitePagesParams = {},
  options: FetchOptions = {},
): Promise<SitePageListResponse> {
  const searchParams = new URLSearchParams();
  const page = Number.isFinite(params.page) && params.page ? Math.max(1, Math.trunc(params.page)) : 1;
  const pageSize =
    Number.isFinite(params.pageSize) && params.pageSize ? Math.max(1, Math.trunc(params.pageSize)) : 20;

  searchParams.set('page', String(page));
  searchParams.set('page_size', String(pageSize));

  const query = params.query?.trim();
  if (query) {
    searchParams.set('q', query);
  }

  if (params.type && PAGE_TYPES.includes(params.type as typeof PAGE_TYPES[number])) {
    searchParams.set('type', params.type);
  }

  if (params.status && PAGE_STATUSES.includes(params.status as typeof PAGE_STATUSES[number])) {
    searchParams.set('status', params.status);
  }

  const locale = params.locale?.trim();
  if (locale) {
    searchParams.set('locale', locale);
  }

  if (typeof params.hasDraft === 'boolean') {
    searchParams.set('has_draft', String(params.hasDraft));
  }

  if (typeof params.pinned === 'boolean') {
    searchParams.set('pinned', String(params.pinned));
  }

  if (params.sort && SORT_ORDERS.has(params.sort)) {
    searchParams.set('sort', params.sort);
  }

  const response = await apiGet<Record<string, unknown>>(`/v1/site/pages?${searchParams.toString()}`, {
    signal: options.signal,
  });

  const items = ensureArray(response?.items, normalizePage);
  const normalizedPage = pickNumber(response?.page) ?? page;
  const normalizedPageSize = pickNumber(response?.page_size) ?? pageSize;
  const total = pickNumber(response?.total);

  return {
    items,
    page: normalizedPage,
    page_size: normalizedPageSize,
    total: total ?? null,
  };
}

export async function fetchSitePage(
  pageId: string,
  options: FetchOptions = {},
): Promise<SitePageSummary | null> {
  if (!pageId) {
    return null;
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}`,
    options,
  );
  return normalizePage(response);
}

export async function createSitePage(
  payload: CreateSitePagePayload,
  options: FetchOptions = {},
): Promise<SitePageSummary> {
  const slug = payload.slug?.trim();
  const title = payload.title?.trim();
  if (!slug || !title || !payload.type) {
    throw new Error('site_page_create_invalid_payload');
  }

  const body: Record<string, unknown> = {
    slug,
    title,
    type: payload.type,
  };

  if (payload.locale) {
    body.locale = payload.locale.trim();
  }
  if (payload.owner != null && payload.owner !== '') {
    body.owner = payload.owner;
  }
  if (typeof payload.pinned === 'boolean') {
    body.pinned = payload.pinned;
  }

  const response = await apiPost<Record<string, unknown>>('/v1/site/pages', body, options);
  const page = normalizePage(response);
  if (!page) {
    throw new Error('site_page_create_invalid_response');
  }
  return page;
}

export async function updateSitePage(
  pageId: string,
  payload: UpdateSitePagePayload,
  options: FetchOptions = {},
): Promise<SitePageSummary> {
  if (!pageId) {
    throw new Error('site_page_update_missing_id');
  }
  const body: Record<string, unknown> = {};
  if (payload.slug != null) {
    const normalized = typeof payload.slug === 'string' ? payload.slug.trim() : '';
    if (normalized) {
      body.slug = normalized.startsWith('/') ? normalized : `/${normalized}`;
    } else {
      body.slug = null;
    }
  }
  if (payload.title != null) {
    body.title = typeof payload.title === 'string' ? payload.title.trim() : null;
  }
  if (payload.locale != null) {
    body.locale = typeof payload.locale === 'string' ? payload.locale.trim() : null;
  }
  if (payload.owner !== undefined) {
    if (payload.owner === null) {
      body.owner = null;
    } else {
      const trimmedOwner = payload.owner.trim();
      body.owner = trimmedOwner.length > 0 ? trimmedOwner : null;
    }
  }
  if (typeof payload.pinned === 'boolean') {
    body.pinned = payload.pinned;
  } else if (payload.pinned === null) {
    body.pinned = null;
  }

  if (Object.keys(body).length === 0) {
    const current = await fetchSitePage(pageId, options);
    if (!current) {
      throw new Error('site_page_update_not_found');
    }
    return current;
  }

  const response = await apiPatch<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}`,
    body,
    options,
  );
  const normalized = normalizePage(response);
  if (!normalized) {
    throw new Error('site_page_update_invalid_response');
  }
  return normalized;
}

export async function deleteSitePage(pageId: string, options: FetchOptions = {}): Promise<void> {
  if (!pageId) {
    throw new Error('site_page_delete_missing_id');
  }
  await apiDelete(`/v1/site/pages/${encodeURIComponent(pageId)}`, options);
}

export async function fetchSitePageDraft(
  pageId: string,
  options: FetchOptions = {},
): Promise<SitePageDraft | null> {
  if (!pageId) {
    return null;
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}/draft`,
    options,
  );
  return normalizeDraft(response);
}

export async function saveSitePageDraft(
  pageId: string,
  payload: SaveSitePageDraftPayload,
  options: FetchOptions = {},
): Promise<SitePageDraft> {
  if (!pageId) {
    throw new Error('site_page_id_missing');
  }
  const body: Record<string, unknown> = {
    version: payload.version,
    data: payload.data ?? {},
    meta: payload.meta ?? {},
  };
  const reviewStatus = payload.review_status;
  if (reviewStatus) {
    body.review_status = reviewStatus;
  }
  if (payload.comment != null) {
    body.comment = payload.comment;
  }
  const response = await apiPut<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}/draft`,
    body,
    options,
  );
  const draft = normalizeDraft(response);
  if (!draft) {
    throw new Error('site_page_draft_invalid_response');
  }
  return draft;
}

export async function publishSitePage(
  pageId: string,
  payload: PublishSitePagePayload = {},
  options: FetchOptions = {},
): Promise<SitePageVersion> {
  if (!pageId) {
    throw new Error('site_page_missing_id');
  }
  const body: Record<string, unknown> = {};
  if (payload.comment != null) {
    body.comment = payload.comment;
  }
  if (Array.isArray(payload.diff) && payload.diff.length > 0) {
    body.diff = payload.diff;
  }
  const response = await apiPost<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}/publish`,
    body,
    options,
  );
  const version = normalizePageVersion(response);
  if (!version) {
    throw new Error('site_page_publish_invalid_response');
  }
  return version;
}

export async function fetchSitePageHistory(
  pageId: string,
  params: FetchSitePageHistoryParams = {},
  options: FetchOptions = {},
): Promise<SitePageHistoryResponse> {
  const limit = Number.isFinite(params.limit) && params.limit ? Math.max(1, Math.trunc(params.limit)) : 10;
  const offset =
    Number.isFinite(params.offset) && params.offset ? Math.max(0, Math.trunc(params.offset)) : 0;
  const searchParams = new URLSearchParams();
  searchParams.set('limit', String(limit));
  searchParams.set('offset', String(offset));

  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}/history?${searchParams.toString()}`,
    options,
  );
  const items = ensureArray(response?.items, normalizePageVersion);
  return {
    items,
    total: pickNumber(response?.total) ?? items.length,
    limit: pickNumber(response?.limit) ?? limit,
    offset: pickNumber(response?.offset) ?? offset,
  };
}

export async function fetchSitePageVersion(
  pageId: string,
  version: number,
  options: FetchOptions = {},
): Promise<SitePageVersion | null> {
  if (!pageId || !Number.isFinite(version)) {
    return null;
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}/history/${version}`,
    options,
  );
  return normalizePageVersion(response);
}

export async function validateSitePageDraft(
  pageId: string,
  payload: { data?: Record<string, unknown>; meta?: Record<string, unknown> } = {},
  options: FetchOptions = {},
): Promise<SiteDraftValidationResult> {
  if (!pageId) {
    throw new Error('site_page_validate_missing_id');
  }
  const body: Record<string, unknown> = {};
  if (payload.data) {
    body.data = payload.data;
  }
  if (payload.meta) {
    body.meta = payload.meta;
  }
  const response = await apiPost<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}/draft/validate`,
    body,
    options,
  );
  return normalizeValidationResult(response);
}

export async function diffSitePageDraft(
  pageId: string,
  options: FetchOptions = {},
): Promise<SitePageDraftDiffResponse> {
  if (!pageId) {
    throw new Error('site_page_diff_missing_id');
  }
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}/draft/diff`,
    options,
  );
  const diff = ensureArray(response?.diff, normalizeDiffEntry);
  return {
    draft_version: pickNumber(response?.draft_version) ?? 0,
    published_version: pickNumber(response?.published_version) ?? null,
    diff,
  };
}

export async function previewSitePage(
  pageId: string,
  payload: PreviewSitePagePayload = {},
  options: FetchOptions = {},
): Promise<SitePagePreviewResponse> {
  if (!pageId) {
    throw new Error('site_page_preview_missing_id');
  }
  const body: Record<string, unknown> = {};
  if (payload.data) {
    body.data = payload.data;
  }
  if (payload.meta) {
    body.meta = payload.meta;
  }
  if (Array.isArray(payload.layouts) && payload.layouts.length > 0) {
    body.layouts = payload.layouts.filter((layout) => typeof layout === 'string' && layout.trim().length > 0);
  }
  if (payload.version != null) {
    body.version = payload.version;
  }
  const response = await apiPost<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}/preview`,
    body,
    options,
  );
  return normalizePreviewResponse(response);
}

export async function restoreSitePageVersion(
  pageId: string,
  version: number,
  options: FetchOptions = {},
): Promise<SitePageDraft | null> {
  if (!pageId || !Number.isFinite(version)) {
    return null;
  }
  const response = await apiPost<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}/history/${version}/restore`,
    {},
    options,
  );
  return normalizeDraft(response);
}

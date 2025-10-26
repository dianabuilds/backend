import { apiGet } from '../../client';

import type {
  SiteGlobalBlockMetricsResponse,
  SitePageMetricsResponse,
} from '@shared/types/management';

import { normalizeBlockMetricsResponse, normalizePageMetricsResponse } from './normalizers';
import type {
  FetchOptions,
  FetchSiteGlobalBlockMetricsParams,
  FetchSitePageMetricsParams,
} from './types';

export async function fetchSitePageMetrics(
  pageId: string,
  params: FetchSitePageMetricsParams = {},
  options: FetchOptions = {},
): Promise<SitePageMetricsResponse> {
  if (!pageId) {
    throw new Error('site_page_metrics_missing_id');
  }
  const search = new URLSearchParams();
  const period = params.period ?? '7d';
  if (period) {
    search.set('period', period);
  }
  if (params.locale) {
    search.set('locale', params.locale);
  }
  const query = search.toString();
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/pages/${encodeURIComponent(pageId)}/metrics${query ? `?${query}` : ''}`,
    options,
  );
  return normalizePageMetricsResponse(response);
}

export async function fetchSiteGlobalBlockMetrics(
  blockId: string,
  params: FetchSiteGlobalBlockMetricsParams = {},
  options: FetchOptions = {},
): Promise<SiteGlobalBlockMetricsResponse> {
  if (!blockId) {
    throw new Error('site_global_block_metrics_missing_id');
  }
  const search = new URLSearchParams();
  const period = params.period ?? '7d';
  if (period) {
    search.set('period', period);
  }
  if (params.locale) {
    search.set('locale', params.locale);
  }
  const query = search.toString();
  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/global-blocks/${encodeURIComponent(blockId)}/metrics${query ? `?${query}` : ''}`,
    options,
  );
  return normalizeBlockMetricsResponse(response);
}

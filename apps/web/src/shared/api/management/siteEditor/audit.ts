import { apiGet } from '../../client';
import { ensureArray, pickNumber } from '../utils';

import type { SiteAuditListResponse } from '@shared/types/management';

import { normalizeAuditEntry } from './normalizers';
import type { FetchOptions, FetchSiteAuditParams } from './types';

export async function fetchSiteAudit(
  params: FetchSiteAuditParams = {},
  options: FetchOptions = {},
): Promise<SiteAuditListResponse> {
  const searchParams = new URLSearchParams();
  if (params.entityType) {
    searchParams.set('entity_type', params.entityType);
  }
  if (params.entityId) {
    searchParams.set('entity_id', params.entityId);
  }
  if (params.actor) {
    searchParams.set('actor', params.actor);
  }
  const limit = Number.isFinite(params.limit) && params.limit ? Math.max(1, Math.trunc(params.limit)) : 20;
  const offset = Number.isFinite(params.offset) && params.offset ? Math.max(0, Math.trunc(params.offset)) : 0;
  searchParams.set('limit', String(limit));
  searchParams.set('offset', String(offset));

  const response = await apiGet<Record<string, unknown>>(
    `/v1/site/audit?${searchParams.toString()}`,
    options,
  );
  const items = ensureArray(response?.items, normalizeAuditEntry);
  return {
    items,
    total: pickNumber(response?.total) ?? items.length,
    limit: pickNumber(response?.limit) ?? limit,
    offset: pickNumber(response?.offset) ?? offset,
  };
}

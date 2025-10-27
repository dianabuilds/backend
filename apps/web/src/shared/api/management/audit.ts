import { apiGet } from '../client';
import type {
  ManagementAuditEvent,
  ManagementAuditEventMeta,
  ManagementAuditFacets,
  ManagementAuditResponse,
  ManagementAuditTaxonomy,
  ManagementAuditUser,
} from '../../types/management';
import { ensureArray, isObjectRecord, pickNumber, pickString } from './utils';

export type FetchAuditEventsParams = {
  page?: number;
  pageSize?: number;
  search?: string;
  module?: string;
  action?: string;
  resourceType?: string;
  result?: string;
  actorId?: string;
  dateFrom?: string;
  dateTo?: string;
  signal?: AbortSignal;
};

function normalizeAuditEventMeta(raw: unknown): ManagementAuditEventMeta | null {
  if (!isObjectRecord(raw)) {
    return null;
  }
  const meta: ManagementAuditEventMeta = {};
  if (pickString(raw.module)) meta.module = pickString(raw.module);
  if (pickString(raw.verb)) meta.verb = pickString(raw.verb);
  if (pickString(raw.resource_label)) meta.resource_label = pickString(raw.resource_label);
  if (pickString(raw.result)) meta.result = pickString(raw.result);
  return Object.keys(meta).length > 0 ? meta : null;
}

function normalizeAuditEvent(raw: unknown): ManagementAuditEvent | null {
  if (!isObjectRecord(raw)) {
    return null;
  }
  const id = pickString(raw.id) ?? pickString(raw.event_id);
  if (!id) {
    return null;
  }
  return {
    id,
    created_at: pickString(raw.created_at) ?? null,
    actor_id: pickString(raw.actor_id) ?? null,
    action: pickString(raw.action) ?? null,
    resource_type: pickString(raw.resource_type) ?? null,
    resource_id: pickString(raw.resource_id) ?? null,
    reason: pickString(raw.reason) ?? null,
    ip: pickString(raw.ip) ?? null,
    user_agent: pickString(raw.user_agent) ?? null,
    before: raw.before,
    after: raw.after,
    extra: raw.extra,
    meta: normalizeAuditEventMeta(raw.meta),
  };
}

function normalizeCounters(raw: unknown): Record<string, number> {
  if (!isObjectRecord(raw)) {
    return {};
  }
  const result: Record<string, number> = {};
  Object.entries(raw).forEach(([key, value]) => {
    const numeric = pickNumber(value);
    if (numeric !== undefined) {
      result[String(key)] = numeric;
    }
  });
  return result;
}

function normalizeFacets(raw: unknown): ManagementAuditFacets | undefined {
  if (!isObjectRecord(raw)) {
    return undefined;
  }
  return {
    modules: normalizeCounters(raw.modules),
    resource_types: normalizeCounters(raw.resource_types),
    results: normalizeCounters(raw.results),
  };
}

function normalizeTaxonomy(raw: unknown): ManagementAuditTaxonomy | undefined {
  if (!isObjectRecord(raw)) {
    return undefined;
  }
  const actions = Array.isArray(raw.actions)
    ? raw.actions.map((item) => (typeof item === 'string' ? item : null)).filter((item): item is string => Boolean(item))
    : undefined;
  return {
    actions,
  };
}

export async function fetchAuditEvents({
  page = 1,
  pageSize = 10,
  search,
  module,
  action,
  resourceType,
  result,
  actorId,
  dateFrom,
  dateTo,
  signal,
}: FetchAuditEventsParams = {}): Promise<ManagementAuditResponse> {
  const params = new URLSearchParams();
  params.set('page', String(page));
  params.set('page_size', String(pageSize));
  if (search?.trim()) params.set('q', search.trim());
  if (module) params.set('module', module);
  if (action) params.set('action', action);
  if (resourceType) params.set('resource_type', resourceType);
  if (result) params.set('result', result);
  if (actorId) params.set('actor_id', actorId);
  if (dateFrom) params.set('from', dateFrom);
  if (dateTo) params.set('to', dateTo);

  const payload = await apiGet<unknown>(`/v1/audit?${params.toString()}`, { signal });
  const source = isObjectRecord(payload) ? payload : {};

  const items = ensureArray(source.items, normalizeAuditEvent).filter((event): event is ManagementAuditEvent => event !== null);
  const pageValue = pickNumber(source.page) ?? page;
  const pageSizeValue = pickNumber(source.page_size) ?? pageSize;
  const hasMore = Boolean(source.has_more);
  const nextPage = pickNumber(source.next_page) ?? null;

  return {
    items,
    page: pageValue,
    page_size: pageSizeValue,
    has_more: hasMore,
    next_page: nextPage,
    facets: normalizeFacets(source.facets),
    taxonomy: normalizeTaxonomy(source.taxonomy),
  };
}

export type FetchAuditUsersOptions = {
  limit?: number;
  signal?: AbortSignal;
};

export async function fetchAuditUsers(
  query: string,
  { limit = 10, signal }: FetchAuditUsersOptions = {},
): Promise<ManagementAuditUser[]> {
  const trimmed = query.trim();
  if (!trimmed) {
    return [];
  }
  const params = new URLSearchParams();
  params.set('q', trimmed);
  params.set('limit', String(limit));

  const payload = await apiGet<unknown[]>(`/v1/users/search?${params.toString()}`, { signal });
  return ensureArray(payload, (item) => {
    if (!isObjectRecord(item)) return null;
    const id = pickString(item.id);
    if (!id) return null;
    return {
      id,
      username: pickString(item.username) ?? null,
    };
  });
}

import { apiGet } from '../client';
import type {
  NodeLifecycleStatus,
  NodeModerationStatus,
  NodeSortKey,
  NodeSortOrder,
  NodesListResult,
} from '../../types/nodes';
import {
  ensureArray,
  firstNumberCandidate,
  isObjectRecord,
  normalizeNodeItem,
  pickBoolean,
  pickNullableString,
} from './utils';

export type FetchNodesListOptions = {
  q?: string;
  slug?: string;
  status?: NodeLifecycleStatus | 'all' | null;
  moderationStatus?: NodeModerationStatus | 'all' | null;
  tag?: string;
  authorId?: string;
  sort?: NodeSortKey;
  order?: NodeSortOrder;
  updatedFrom?: string;
  updatedTo?: string;
  limit?: number;
  offset?: number;
  signal?: AbortSignal;
};

const NODES_LIST_ENDPOINT = '/v1/admin/nodes/list';

function buildSearchParams({
  q,
  slug,
  status,
  moderationStatus,
  tag,
  authorId,
  sort,
  order,
  updatedFrom,
  updatedTo,
  limit,
  offset,
}: FetchNodesListOptions): URLSearchParams {
  const params = new URLSearchParams();
  const trimmedQuery = q?.trim();
  if (trimmedQuery) {
    params.set('q', trimmedQuery);
  }
  const trimmedSlug = slug?.trim();
  if (trimmedSlug) {
    params.set('slug', trimmedSlug);
  }
  if (typeof limit === 'number' && Number.isFinite(limit) && limit > 0) {
    params.set('limit', String(limit));
  }
  if (typeof offset === 'number' && Number.isFinite(offset) && offset >= 0) {
    params.set('offset', String(offset));
  }
  if (sort) {
    params.set('sort', sort);
  }
  if (order) {
    params.set('order', order);
  }
  if (status && status !== 'all') {
    params.set('status', status);
  }
  const normalizedModeration = moderationStatus?.toLowerCase?.();
  if (normalizedModeration && normalizedModeration !== 'all') {
    params.set('moderation_status', normalizedModeration);
  }
  const normalizedTag = tag?.trim();
  if (normalizedTag) {
    params.set('tag', normalizedTag);
  }
  const normalizedAuthor = authorId?.trim();
  if (normalizedAuthor) {
    params.set('author_id', normalizedAuthor);
  }
  const updatedFromValue = pickNullableString(updatedFrom);
  if (updatedFromValue) {
    params.set('updated_from', updatedFromValue);
  }
  const updatedToValue = pickNullableString(updatedTo);
  if (updatedToValue) {
    params.set('updated_to', updatedToValue);
  }
  return params;
}

function extractStatsSource(candidate: Record<string, unknown>): Record<string, unknown> | undefined {
  if (isObjectRecord(candidate.stats)) {
    return candidate.stats;
  }
  if (isObjectRecord(candidate.summary)) {
    return candidate.summary;
  }
  if (isObjectRecord(candidate.meta)) {
    const meta = candidate.meta as Record<string, unknown>;
    if (isObjectRecord(meta.stats)) {
      return meta.stats;
    }
    if (isObjectRecord(meta.summary)) {
      return meta.summary;
    }
  }
  if (isObjectRecord(candidate.data)) {
    const data = candidate.data as Record<string, unknown>;
    if (isObjectRecord(data.stats)) {
      return data.stats;
    }
    if (isObjectRecord(data.summary)) {
      return data.summary;
    }
  }
  return undefined;
}

function normalizeListPayload(payload: unknown, pageSize: number): NodesListResult {
  if (Array.isArray(payload)) {
    const items = ensureArray(payload, normalizeNodeItem);
    return {
      items,
      meta: {
        total: firstNumberCandidate(payload.length),
        published: null,
        drafts: null,
        pendingEmbeddings: null,
      },
      hasNext: items.length === pageSize,
    };
  }

  if (!isObjectRecord(payload)) {
    return {
      items: [],
      meta: {
        total: null,
        published: null,
        drafts: null,
        pendingEmbeddings: null,
      },
      hasNext: false,
    };
  }

  const data = isObjectRecord(payload.data) ? payload.data : undefined;
  const merged: Record<string, unknown> = data ? { ...payload, ...data } : { ...payload };

  if (data && !Array.isArray(merged.items) && Array.isArray(data.items)) {
    merged.items = data.items;
  }

  const items = ensureArray(merged.items, normalizeNodeItem);

  const statsSource =
    extractStatsSource(merged) ??
    extractStatsSource(payload) ??
    (data ? extractStatsSource(data) : undefined);

  const total = firstNumberCandidate(
    merged.total,
    payload.total,
    payload.count,
    payload.items_count,
    data?.total,
    data?.count,
    data?.items_count,
    statsSource?.total,
    statsSource?.count,
  );
  const published = firstNumberCandidate(
    statsSource?.published,
    statsSource?.published_count,
    statsSource?.published_total,
  );
  const drafts = firstNumberCandidate(
    statsSource?.drafts,
    statsSource?.draft_count,
    statsSource?.draft_total,
  );
  const pendingEmbeddings = firstNumberCandidate(
    statsSource?.pendingEmbeddings,
    statsSource?.pending_embeddings,
    statsSource?.embedding_pending,
    statsSource?.pending,
    statsSource?.pending_embeddings_total,
  );

  const hasNextExplicitCandidates = [
    merged.has_next,
    merged.hasNext,
    payload.has_next,
    payload.hasNext,
    data?.has_next,
    data?.hasNext,
  ];
  let hasNextExplicit: boolean | undefined;
  for (const candidate of hasNextExplicitCandidates) {
    const value = pickBoolean(candidate);
    if (value !== undefined) {
      hasNextExplicit = value;
      break;
    }
  }

  const effectivePageSize = pageSize > 0 ? pageSize : items.length || 20;

  return {
    items,
    meta: {
      total: total ?? null,
      published: published ?? null,
      drafts: drafts ?? null,
      pendingEmbeddings: pendingEmbeddings ?? null,
    },
    hasNext: hasNextExplicit ?? items.length >= effectivePageSize,
  };
}

export async function fetchNodesList(options: FetchNodesListOptions = {}): Promise<NodesListResult> {
  const limit = typeof options.limit === 'number' && Number.isFinite(options.limit) && options.limit > 0 ? options.limit : 20;
  const offset = typeof options.offset === 'number' && Number.isFinite(options.offset) && options.offset >= 0 ? options.offset : 0;
  const params = buildSearchParams({ ...options, limit, offset });
  const url = params.toString()
    ? `${NODES_LIST_ENDPOINT}?${params.toString()}`
    : NODES_LIST_ENDPOINT;
  const response = await apiGet<unknown>(url, { signal: options.signal });
  return normalizeListPayload(response, limit);
}

export const nodesListApi = {
  fetchNodesList,
};

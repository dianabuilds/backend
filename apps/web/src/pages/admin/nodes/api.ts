import { apiDelete, apiGet, apiPost } from '../../../shared/api/client';
import type {
  AdminCommentBanPayload,
  AdminCommentDeleteOptions,
  AdminCommentDisablePayload,
  AdminCommentLockPayload,
  AdminCommentStatusPayload,
  AdminNodeAnalytics,
  AdminNodeAnalyticsQuery,
  AdminNodeComment,
  AdminNodeCommentBan,
  AdminNodeCommentsQuery,
  AdminNodeCommentsResponse,
  AdminNodeEngagementSummary,
} from './types';

const DEFAULT_COMMENTS_LIMIT = 50;

function encodeId(id: string | number): string {
  return encodeURIComponent(String(id));
}

function buildCommentsSearchParams(params: AdminNodeCommentsQuery): URLSearchParams {
  const search = new URLSearchParams();
  if (params.view) search.set('view', params.view);
  if (params.parentId != null) search.set('parentId', String(params.parentId));
  if (Array.isArray(params.statuses)) {
    for (const status of params.statuses) {
      if (status) search.append('status', status);
    }
  }
  if (params.authorId) search.set('authorId', params.authorId);
  if (params.createdFrom) search.set('createdFrom', params.createdFrom);
  if (params.createdTo) search.set('createdTo', params.createdTo);
  if (params.search) search.set('search', params.search);
  if (typeof params.includeDeleted === 'boolean') search.set('includeDeleted', String(params.includeDeleted));
  if (typeof params.limit === 'number') search.set('limit', String(params.limit));
  if (typeof params.offset === 'number') search.set('offset', String(params.offset));
  if (params.order) search.set('order', params.order);
  return search;
}

function normalizeCommentsResponse(
  raw: Partial<AdminNodeCommentsResponse> | undefined,
  fallbackLimit: number,
): AdminNodeCommentsResponse {
  const items = Array.isArray(raw?.items) ? (raw.items as AdminNodeComment[]) : [];
  const total = typeof raw?.total === 'number' ? raw.total : raw?.summary?.total ?? items.length;
  return {
    items,
    summary: {
      total: typeof raw?.summary?.total === 'number' ? raw.summary!.total : total,
      by_status: raw?.summary?.by_status ?? {},
    },
    total,
    limit: typeof raw?.limit === 'number' ? raw.limit : fallbackLimit,
    offset: typeof raw?.offset === 'number' ? raw.offset : 0,
    has_more: Boolean(raw?.has_more),
    view: raw?.view,
    filters: raw?.filters,
  };
}

export async function fetchAdminNodeEngagement(nodeId: string): Promise<AdminNodeEngagementSummary> {
  return apiGet<AdminNodeEngagementSummary>(`/v1/admin/nodes/${encodeId(nodeId)}/engagement`);
}

export async function fetchAdminNodeComments(
  nodeId: string,
  query: AdminNodeCommentsQuery = {},
): Promise<AdminNodeCommentsResponse> {
  const params = buildCommentsSearchParams(query);
  const qs = params.toString();
  const url = `/v1/admin/nodes/${encodeId(nodeId)}/comments${qs ? `?${qs}` : ''}`;
  const response = await apiGet<Partial<AdminNodeCommentsResponse>>(url);
  return normalizeCommentsResponse(response, query.limit ?? DEFAULT_COMMENTS_LIMIT);
}

export async function updateAdminCommentStatus(commentId: string, payload: AdminCommentStatusPayload) {
  return apiPost(`/v1/admin/nodes/comments/${encodeId(commentId)}/status`, payload);
}

export async function deleteAdminComment(commentId: string, options: AdminCommentDeleteOptions = {}) {
  const params = new URLSearchParams();
  if (options.reason) params.set('reason', options.reason);
  if (options.hard) params.set('hard', 'true');
  const qs = params.toString();
  const url = `/v1/admin/nodes/comments/${encodeId(commentId)}${qs ? `?${qs}` : ''}`;
  return apiDelete(url);
}

export async function lockAdminComments(nodeId: string, payload: AdminCommentLockPayload) {
  return apiPost(`/v1/admin/nodes/${encodeId(nodeId)}/comments/lock`, payload);
}

export async function disableAdminComments(nodeId: string, payload: AdminCommentDisablePayload) {
  return apiPost(`/v1/admin/nodes/${encodeId(nodeId)}/comments/disable`, payload);
}

export async function fetchAdminCommentBans(nodeId: string): Promise<AdminNodeCommentBan[]> {
  return apiGet<AdminNodeCommentBan[]>(`/v1/admin/nodes/${encodeId(nodeId)}/comment-bans`);
}

export async function createAdminCommentBan(nodeId: string, payload: AdminCommentBanPayload) {
  return apiPost<AdminNodeCommentBan>(`/v1/admin/nodes/${encodeId(nodeId)}/comment-bans`, payload);
}

export async function deleteAdminCommentBan(nodeId: string, userId: string) {
  return apiDelete(`/v1/admin/nodes/${encodeId(nodeId)}/comment-bans/${encodeId(userId)}`);
}

export async function fetchAdminNodeAnalytics(nodeId: string, query: AdminNodeAnalyticsQuery = {}): Promise<AdminNodeAnalytics> {
  const params = new URLSearchParams();
  if (query.start) params.set('start', query.start);
  if (query.end) params.set('end', query.end);
  if (typeof query.limit === 'number') params.set('limit', String(query.limit));
  if (query.format) params.set('format', query.format);

  const qs = params.toString();
  const url = `/v1/admin/nodes/${encodeId(nodeId)}/analytics${qs ? `?${qs}` : ''}`;
  return apiGet<AdminNodeAnalytics>(url);
}

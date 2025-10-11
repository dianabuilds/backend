import { apiGetWithResponse } from './client';
import type {
  DevBlogDetail,
  DevBlogDetailResponse,
  DevBlogListParams,
  DevBlogListResponse,
  DevBlogSummary,
} from '../types/devBlog';

function toNullableString(value: unknown): string | null {
  if (value == null) return null;
  if (typeof value === 'string') return value;
  return String(value);
}

function normalizeAuthor(raw: unknown): DevBlogSummary['author'] {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  const id = toNullableString(source.id);
  const name = toNullableString(source.name ?? source.displayName ?? source.username);
  if (!id && !name) return null;
  return { id, name };
}

function normalizeTags(raw: unknown): string[] | null {
  if (!Array.isArray(raw)) return null;
  const normalized = raw
    .map((item) => toNullableString(item))
    .filter((tag): tag is string => Boolean(tag && tag.trim()))
    .map((tag) => tag.trim());
  if (!normalized.length) return null;
  const unique = Array.from(new Set(normalized));
  return unique;
}

function normalizeSummary(raw: unknown): DevBlogSummary {
  if (!raw || typeof raw !== 'object') {
    return {
      id: null,
      slug: '',
      title: null,
      summary: null,
      coverUrl: null,
      publishAt: null,
      updatedAt: null,
      author: null,
      tags: null,
    };
  }
  const source = raw as Record<string, unknown>;
  const slug = toNullableString(source.slug) ?? '';
  const idRaw = source.id;
  const id = typeof idRaw === 'number' ? idRaw : idRaw != null ? String(idRaw) : null;
  return {
    id,
    slug,
    title: toNullableString(source.title),
    summary: toNullableString(source.summary ?? source.excerpt ?? null),
    coverUrl: toNullableString(source.cover_url ?? source.coverUrl ?? null),
    publishAt: toNullableString(source.publish_at ?? source.publishAt ?? null),
    updatedAt: toNullableString(source.updated_at ?? source.updatedAt ?? null),
    author: normalizeAuthor(source.author),
    tags: normalizeTags(source.tags),
  };
}

function normalizeDetail(raw: unknown): DevBlogDetail {
  const summary = normalizeSummary(raw);
  const source = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {};
  return {
    ...summary,
    content: toNullableString(source.content ?? source.content_html ?? source.body ?? null),
    status: toNullableString(source.status ?? null),
    isPublic: typeof source.is_public === 'boolean' ? source.is_public : null,
    tags: normalizeTags(source.tags) ?? summary.tags,
  };
}

function normalizeListResponse(raw: unknown): DevBlogListResponse {
  const source = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {};
  const itemsRaw = Array.isArray(source.items) ? source.items : [];
  const items = itemsRaw.map(normalizeSummary);
  const totalRaw = source.total;
  const total = typeof totalRaw === 'number' ? totalRaw : Number(totalRaw) || items.length;
  const hasNext = Boolean(source.has_next ?? source.hasNext);
  const availableTagsRaw = source.available_tags ?? source.availableTags;
  const availableTags = normalizeTags(Array.isArray(availableTagsRaw) ? availableTagsRaw : null) ?? [];
  const dateRangeRaw = (source.date_range ?? source.dateRange) as
    | { start?: unknown; end?: unknown }
    | undefined;
  const dateRange = dateRangeRaw
    ? {
        start: toNullableString(dateRangeRaw.start ?? null),
        end: toNullableString(dateRangeRaw.end ?? null),
      }
    : null;
  const appliedTags = normalizeTags(source.applied_tags ?? source.appliedTags);
  return { items, total, hasNext, availableTags, dateRange, appliedTags };
}

function normalizeDetailResponse(raw: unknown): DevBlogDetailResponse {
  const source = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {};
  return {
    post: normalizeDetail(source.post),
    prev: source.prev ? normalizeSummary(source.prev) : null,
    next: source.next ? normalizeSummary(source.next) : null,
  };
}

export async function fetchDevBlogList(
  params: DevBlogListParams = {},
): Promise<{ data: DevBlogListResponse | null; status: number; error?: string }> {
  const limit = params.limit ?? 12;
  const page = params.page && params.page > 0 ? params.page : 1;
  const offset = (page - 1) * limit;
  const search = new URLSearchParams();
  search.set('limit', String(limit));
  search.set('offset', String(offset));
  for (const tag of params.tags ?? []) {
    const trimmed = typeof tag === 'string' ? tag.trim() : '';
    if (trimmed) {
      search.append('tag', trimmed);
    }
  }
  if (params.publishedFrom) {
    search.set('from', params.publishedFrom);
  }
  if (params.publishedTo) {
    search.set('to', params.publishedTo);
  }
  const endpoint = `/v1/nodes/dev-blog?${search.toString()}`;
  try {
    const { data, response } = await apiGetWithResponse<unknown>(endpoint, { omitCredentials: true });
    return { data: normalizeListResponse(data), status: response.status };
  } catch (error: any) {
    const status = typeof error?.status === 'number' ? error.status : 500;
    return { data: null, status, error: error?.message || 'Failed to load dev blog posts' };
  }
}

export async function fetchDevBlogPost(
  slug: string,
): Promise<{ data: DevBlogDetailResponse | null; status: number; error?: string }> {
  const normalized = slug?.trim();
  if (!normalized) {
    return { data: null, status: 400, error: 'Missing slug' };
  }
  const endpoint = `/v1/nodes/dev-blog/${encodeURIComponent(normalized)}`;
  try {
    const { data, response } = await apiGetWithResponse<unknown>(endpoint, { omitCredentials: true });
    return { data: normalizeDetailResponse(data), status: response.status };
  } catch (error: any) {
    const status = typeof error?.status === 'number' ? error.status : 500;
    return { data: null, status, error: error?.message || 'Failed to load dev blog post' };
  }
}

export type { DevBlogListResponse, DevBlogDetailResponse, DevBlogSummary, DevBlogDetail };


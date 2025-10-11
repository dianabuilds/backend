import { apiGetWithResponse } from './client';
import type { HomeBlockItem, HomeBlockPayload, HomeDataSource, HomeFallbackEntry, HomeResponse } from '../types/homePublic';

function toNullableString(value: unknown): string | null {
  if (value == null) return null;
  if (typeof value === 'string') return value;
  return String(value);
}

function normalizeAuthor(raw: unknown): HomeBlockItem['author'] {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  const id = toNullableString(source.id);
  const name = toNullableString(source.name ?? source.displayName ?? source.username);
  if (!id && !name) return null;
  return { id, name };
}

function normalizeItem(raw: unknown): HomeBlockItem {
  if (!raw || typeof raw !== 'object') return {};
  const source = raw as Record<string, unknown>;
  const idValue = source.id ?? source.node_id ?? source.slug ?? null;
  const id = typeof idValue === 'number' ? idValue : idValue != null ? String(idValue) : null;
  return {
    id,
    slug: toNullableString(source.slug),
    title: toNullableString(source.title),
    summary: toNullableString(source.summary ?? source.description ?? null),
    coverUrl: toNullableString(source.cover_url ?? source.coverUrl ?? null),
    publishAt: toNullableString(source.publish_at ?? source.publishAt ?? null),
    updatedAt: toNullableString(source.updated_at ?? source.updatedAt ?? null),
    author: normalizeAuthor(source.author),
  };
}

function normalizeDataSource(raw: unknown): HomeDataSource | null {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  const mode = typeof source.mode === 'string' ? source.mode : undefined;
  const entity = typeof source.entity === 'string' ? source.entity : undefined;
  const filter = source.filter && typeof source.filter === 'object' ? (source.filter as Record<string, unknown>) : undefined;
  let items: Array<string | number> | null = null;
  if (Array.isArray(source.items)) {
    items = source.items
      .map((value) => {
        if (value == null) return null;
        if (typeof value === 'number') return value;
        const text = String(value).trim();
        return text.length ? text : null;
      })
      .filter((value): value is string | number => value != null);
  }
  return {
    mode: mode === 'manual' || mode === 'auto' ? mode : undefined,
    entity: entity ?? null,
    filter: filter ?? null,
    items,
  };
}

function normalizeBlock(raw: unknown): HomeBlockPayload | null {
  if (!raw || typeof raw !== 'object') return null;
  const source = raw as Record<string, unknown>;
  const id = toNullableString(source.id);
  const type = toNullableString(source.type);
  if (!id || !type) return null;
  const items = Array.isArray(source.items) ? source.items.map(normalizeItem) : [];
  const slots = source.slots && typeof source.slots === 'object' ? (source.slots as Record<string, unknown>) : null;
  const layout = source.layout && typeof source.layout === 'object' ? (source.layout as Record<string, unknown>) : null;
  return {
    id,
    type,
    title: toNullableString(source.title),
    enabled: Boolean(source.enabled),
    slots,
    layout,
    items,
    dataSource: normalizeDataSource(source.dataSource ?? source.data_source),
  };
}

function normalizeFallback(raw: unknown): HomeFallbackEntry {
  if (!raw || typeof raw !== 'object') return {};
  return { ...(raw as Record<string, unknown>) };
}

function normalizeHomeResponse(raw: unknown): HomeResponse {
  const blocksRaw = Array.isArray((raw as any)?.blocks) ? (raw as any).blocks : [];
  const fallbacksRaw = Array.isArray((raw as any)?.fallbacks) ? (raw as any).fallbacks : [];
  const blocks = blocksRaw
    .map(normalizeBlock)
    .filter((block: HomeBlockPayload | null): block is HomeBlockPayload => block != null);
  return {
    slug: typeof (raw as any)?.slug === 'string' ? (raw as any).slug : 'main',
    version: typeof (raw as any)?.version === 'number' ? (raw as any).version : Number((raw as any)?.version) || 0,
    updatedAt: toNullableString((raw as any)?.updated_at ?? (raw as any)?.updatedAt ?? null),
    publishedAt: toNullableString((raw as any)?.published_at ?? (raw as any)?.publishedAt ?? null),
    generatedAt: toNullableString((raw as any)?.generated_at ?? (raw as any)?.generatedAt ?? null),
    blocks,
    meta: (raw as any)?.meta && typeof (raw as any).meta === 'object' ? ((raw as any).meta as Record<string, unknown>) : {},
    fallbacks: fallbacksRaw.map(normalizeFallback),
  };
}

export async function fetchPublicHome(slug?: string): Promise<{ data: HomeResponse | null; status: number; error?: string; etag: string | null }> {
  const endpoint = slug && slug !== 'main' ? `/v1/public/home?slug=${encodeURIComponent(slug)}` : '/v1/public/home';
  try {
    const { data, response } = await apiGetWithResponse<unknown>(endpoint, { omitCredentials: true });
    const etag = response.headers.get('ETag') ?? response.headers.get('etag');
    const normalized = normalizeHomeResponse(data);
    const payload: HomeResponse = { ...normalized, etag: etag ?? normalized.etag ?? null };
    return { data: payload, status: response.status, etag: etag ?? null };
  } catch (error: any) {
    const status = typeof error?.status === 'number' ? error.status : 500;
    return { data: null, status, error: error?.message || 'Failed to load home data', etag: null };
  }
}

export type { HomeResponse, HomeBlockPayload, HomeBlockItem };





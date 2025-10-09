import type { EmbeddingStatus, NodeItem } from '../../types/nodes';

export function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

export function pickString(value: unknown): string | undefined {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length ? trimmed : undefined;
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return String(value);
  }
  return undefined;
}

export function pickNullableString(value: unknown): string | null | undefined {
  if (value === null) return null;
  return pickString(value);
}

export function pickNumber(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return undefined;
}

export function pickBoolean(value: unknown): boolean | undefined {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    if (normalized === 'true') return true;
    if (normalized === 'false') return false;
  }
  return undefined;
}

export function ensureArray<T>(value: unknown, map: (item: unknown) => T | null | undefined): T[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const result: T[] = [];
  for (const item of value) {
    const mapped = map(item);
    if (mapped !== null && mapped !== undefined) {
      result.push(mapped);
    }
  }
  return result;
}

const NODE_EMBEDDING_STATUSES: EmbeddingStatus[] = ['ready', 'pending', 'disabled', 'error', 'unknown'];

function isEmbeddingStatus(value: string | null | undefined): value is EmbeddingStatus {
  return value != null && NODE_EMBEDDING_STATUSES.includes(value as EmbeddingStatus);
}

export function normalizeNodeItem(raw: unknown): NodeItem | null {
  if (!isObjectRecord(raw)) {
    return null;
  }
  const id = pickString(raw.id) ?? '';
  const slug = pickString(raw.slug) ?? (id ? `node-${id}` : null);
  const status = pickNullableString(raw.status) ?? null;
  const isPublicValue = pickBoolean(raw.is_public);
  const updatedAt = pickNullableString(raw.updated_at) ?? null;

  const embeddingStatusRaw = pickString(raw.embedding_status)?.toLowerCase() ?? null;
  let embeddingStatus: EmbeddingStatus | null = null;
  if (isEmbeddingStatus(embeddingStatusRaw)) {
    embeddingStatus = embeddingStatusRaw;
  }

  let embeddingReady = pickBoolean(raw.embedding_ready) ?? false;
  const embeddingArray = Array.isArray((raw as Record<string, unknown>).embedding)
    ? (raw as Record<string, unknown>).embedding as unknown[]
    : undefined;
  if (embeddingArray && embeddingArray.length > 0) {
    embeddingReady = true;
  }
  if (embeddingStatus === 'ready') {
    embeddingReady = true;
  } else if (embeddingStatus === 'disabled') {
    embeddingReady = false;
  } else if (!embeddingStatus && embeddingReady) {
    embeddingStatus = 'ready';
  }

  return {
    id,
    title: pickNullableString(raw.title) ?? undefined,
    slug,
    author_name: pickNullableString(raw.author_name) ?? null,
    author_id: pickNullableString(raw.author_id) ?? null,
    is_public: isPublicValue,
    status,
    updated_at: updatedAt,
    embedding_status: embeddingStatus,
    embedding_ready: embeddingReady,
  };
}

export function firstNumberCandidate(...values: Array<unknown>): number | null {
  for (const value of values) {
    const numeric = pickNumber(value);
    if (numeric !== undefined) {
      return numeric;
    }
  }
  return null;
}


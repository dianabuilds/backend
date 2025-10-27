import { normalizeHomeResponse } from '@shared/api/publicHome';
import type { HomeResponse } from '@shared/types/homePublic';
import type { PreviewRenderData, PreviewBlockSummary, PreviewFallbackSummary } from './previewTypes';

function normalizeString(value: unknown): string | null {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length ? trimmed : null;
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return String(value);
  }
  return null;
}

function resolveItemLabel(item: unknown): string | null {
  if (item == null) {
    return null;
  }
  if (typeof item === 'string' || typeof item === 'number') {
    return String(item);
  }
  if (typeof item === 'object') {
    const record = item as Record<string, unknown>;
    const candidate =
      normalizeString(record.title) ??
      normalizeString(record.name) ??
      normalizeString(record.slug) ??
      normalizeString(record.id);
    if (candidate) {
      return candidate;
    }
  }
  return null;
}

function parsePreviewBlocks(payload: Record<string, unknown>): PreviewBlockSummary[] {
  const rawBlocks = Array.isArray(payload.blocks) ? payload.blocks : [];
  return rawBlocks.map((entry, index) => {
    if (typeof entry !== 'object' || entry === null) {
      return {
        id: `block-${index + 1}`,
        type: 'unknown',
        items: [],
      };
    }
    const record = entry as Record<string, unknown>;
    const id = normalizeString(record.id) ?? `block-${index + 1}`;
    const type = normalizeString(record.type) ?? 'unknown';
    const title = normalizeString(record.title) ?? undefined;
    const rawItems = Array.isArray(record.items) ? record.items : [];
    const items: string[] = [];
    for (const rawItem of rawItems) {
      const label = resolveItemLabel(rawItem);
      if (label) {
        items.push(label);
      }
      if (items.length >= 6) {
        break;
      }
    }
    return {
      id,
      type,
      title,
      items,
    };
  });
}

function parseFallbacks(payload: Record<string, unknown>): PreviewFallbackSummary[] {
  const fallbacks = Array.isArray(payload.fallbacks) ? payload.fallbacks : [];
  const result: PreviewFallbackSummary[] = [];
  fallbacks.forEach((entry) => {
    if (typeof entry !== 'object' || entry === null) {
      return;
    }
    const record = entry as Record<string, unknown>;
    const id = normalizeString(record.id) ?? 'unknown';
    const reason = normalizeString(record.reason) ?? 'unknown';
    result.push({ id, reason });
  });
  return result;
}

export function extractRenderDataFromPayload(payload: Record<string, unknown>): PreviewRenderData {
  const blocks = parsePreviewBlocks(payload);
  const fallbacks = parseFallbacks(payload);
  const meta =
    typeof payload.meta === 'object' && payload.meta !== null
      ? (payload.meta as Record<string, unknown>)
      : {};

  return {
    version: typeof payload.version === 'number' ? payload.version : null,
    updatedAt: normalizeString(payload.updated_at),
    publishedAt: normalizeString(payload.published_at),
    generatedAt: normalizeString(payload.generated_at),
    title: normalizeString(meta.title) ?? null,
    blocks,
    fallbacks,
  };
}

export function normalizePreviewPayload(payload: Record<string, unknown>): HomeResponse {
  return normalizeHomeResponse(payload);
}

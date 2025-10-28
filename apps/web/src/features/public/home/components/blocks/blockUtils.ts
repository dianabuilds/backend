import dayjs from 'dayjs';
import type { HomeBlockItem, HomeBlockPayload } from '@shared/types/homePublic';

export function getItems(block: HomeBlockPayload): HomeBlockItem[] {
  return Array.isArray(block.items) ? block.items.filter(Boolean) : [];
}

function toPositiveInteger(value: unknown): number | null {
  if (value == null) return null;
  const numeric = typeof value === 'number' ? value : Number.parseInt(String(value), 10);
  if (!Number.isFinite(numeric)) return null;
  const normalized = Math.floor(numeric);
  return normalized > 0 ? normalized : null;
}

function readLimit(source: Record<string, unknown> | null | undefined): number | null {
  if (!source) return null;
  const record = source as Record<string, unknown>;
  return toPositiveInteger(record['limit']);
}

export function resolveLimit(block: HomeBlockPayload, fallback: number): number {
  const filterLimit = readLimit(block.dataSource?.filter ?? null);
  const layoutLimit = readLimit(block.layout ?? null);
  const slotsLimit = readLimit(block.slots ?? null);
  return filterLimit ?? layoutLimit ?? slotsLimit ?? fallback;
}

export function readStringSlot(source: Record<string, unknown> | null | undefined, key: string): string | null {
  if (!source) return null;
  const record = source as Record<string, unknown>;
  const value = record[key];
  return typeof value === 'string' ? value : null;
}

export function formatDate(value?: string | null): string | null {
  if (!value) return null;
  const parsed = dayjs(value);
  if (!parsed.isValid()) return null;
  return parsed.format('D MMMM YYYY');
}

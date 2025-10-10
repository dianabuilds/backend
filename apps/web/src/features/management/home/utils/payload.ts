import type { HomeConfigPayload } from '@shared/types/home';
import type { HomeDraftData } from '../types';

type PayloadRecord = Record<string, unknown>;

function cloneMeta(meta: HomeDraftData['meta']): PayloadRecord | undefined {
  if (!meta) {
    return undefined;
  }
  const entries = Object.entries(meta);
  if (!entries.length) {
    return undefined;
  }
  return entries.reduce<PayloadRecord>((acc, [key, value]) => {
    acc[key] = value;
    return acc;
  }, {});
}

export function buildHomeConfigPayload(slug: string, data: HomeDraftData): HomeConfigPayload {
  const payload: PayloadRecord = {
    blocks: Array.isArray(data.blocks) ? data.blocks : [],
  };
  const meta = cloneMeta(data.meta ?? null);
  if (meta) {
    payload.meta = meta;
  }

  return {
    slug,
    data: payload,
  };
}


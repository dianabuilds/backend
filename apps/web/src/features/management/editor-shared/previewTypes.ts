import type { HomeResponse } from '@shared/types/homePublic';

export type PreviewBlockSummary = {
  id: string;
  type: string;
  title?: string;
  items: string[];
};

export type PreviewFallbackSummary = {
  id: string;
  reason: string;
};

export type PreviewRenderData = {
  version: number | null;
  updatedAt: string | null;
  publishedAt: string | null;
  generatedAt: string | null;
  title: string | null;
  blocks: PreviewBlockSummary[];
  fallbacks: PreviewFallbackSummary[];
};

export type PreviewLayoutContent = {
  summary: PreviewRenderData;
  html?: string;
  payload?: HomeResponse;
};

export type PreviewLayoutsMap = Record<string, PreviewLayoutContent>;

export type PreviewMetaSnapshot = {
  version?: number | null;
  updatedAt?: string | null;
  publishedAt?: string | null;
  generatedAt?: string | null;
};

export type PreviewFetchResult = {
  layouts: PreviewLayoutsMap;
  defaultLayout?: string;
  meta?: PreviewMetaSnapshot;
};

import type { HomeBlockType } from '../../home/types';

export type DraftBlockDataSourceMode = 'manual' | 'auto';

export type DraftBlockDataSourceEntity = 'node' | 'quest' | 'dev_blog' | 'custom';

export type DraftBlockDataSource = {
  mode: DraftBlockDataSourceMode;
  entity?: DraftBlockDataSourceEntity;
  filter?: Record<string, unknown> | null;
  items?: Array<string | number> | null;
};

export type DraftBlock = {
  id: string;
  type: HomeBlockType;
  title?: string;
  enabled: boolean;
  slots?: Record<string, unknown> | null;
  layout?: Record<string, unknown> | null;
  dataSource?: DraftBlockDataSource | null;
  source?: 'manual' | 'site';
  siteBlockId?: string | null;
  siteBlockKey?: string | null;
  siteBlockSection?: string | null;
  siteBlockLocale?: string | null;
  siteBlockTitle?: string | null;
  siteBlockStatus?: string | null;
  siteBlockReviewStatus?: string | null;
  siteBlockRequiresPublisher?: boolean | null;
  siteBlockHasPendingPublish?: boolean | null;
  siteBlockHasDraft?: boolean | null;
  siteBlockUpdatedAt?: string | null;
  siteBlockUpdatedBy?: string | null;
};

export type DraftSharedState = {
  assignments: Record<string, string | null>;
};

export type DraftData = {
  blocks: DraftBlock[];
  meta?: Record<string, unknown> | null;
  shared?: DraftSharedState;
};

export type DraftSnapshot = {
  version: number | null;
  updatedAt: string | null;
  publishedAt: string | null;
};

export type DraftValidationFieldError = {
  path: string;
  message: string;
  keyword: string;
};

export type DraftValidationSummary = {
  valid: boolean;
  general: DraftValidationFieldError[];
  blocks: Record<string, DraftValidationFieldError[]>;
};

export type DraftPreviewPayload = Record<string, unknown>;

export type DraftPreviewMapperOptions = {
  layout?: string;
};

export interface SiteDraftAdapter {
  readonly allowedBlockTypes: ReadonlyArray<string>;
  createEmptyData(): DraftData;
  normalizeDraftData(
    raw: unknown,
    options?: {
      meta?: Record<string, unknown> | null;
      assignments?: Record<string, string | null> | null;
    },
  ): DraftData;
  buildDraftPayload(data: DraftData): {
    data: Record<string, unknown>;
    meta?: Record<string, unknown>;
  };
  mapPreviewResponse(
    response: unknown,
    options?: DraftPreviewMapperOptions,
  ): DraftPreviewPayload | null;
  validateDraft?(data: DraftData): DraftValidationSummary;
}

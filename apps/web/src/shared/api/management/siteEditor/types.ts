import type {
  SiteGlobalBlock,
  SiteGlobalBlockStatus,
  SiteGlobalBlockWarning,
  SiteMetricsPeriod,
  SitePageDraft,
  SitePageStatus,
  SitePageType,
} from '@shared/types/management';

export type FetchOptions = {
  signal?: AbortSignal;
};

export type FetchSitePagesParams = {
  page?: number;
  pageSize?: number;
  query?: string;
  type?: SitePageType | '';
  status?: SitePageStatus | '';
  locale?: string;
  hasDraft?: boolean | null;
  pinned?: boolean | null;
  sort?: 'updated_at_desc' | 'updated_at_asc' | 'title_asc' | 'title_desc' | 'pinned_desc' | 'pinned_asc';
};

export type FetchSitePageMetricsParams = {
  period?: SiteMetricsPeriod;
  locale?: string;
};

export type PublishSitePagePayload = {
  comment?: string | null;
  diff?: Array<Record<string, unknown>> | null;
};

export type CreateSitePagePayload = {
  slug: string;
  title: string;
  type: SitePageType;
  locale?: string;
  owner?: string | null;
  pinned?: boolean;
};

export type UpdateSitePagePayload = {
  slug?: string | null;
  title?: string | null;
  locale?: string | null;
  owner?: string | null;
  pinned?: boolean | null;
};

export type SaveSitePageDraftPayload = {
  version: number;
  data: Record<string, unknown>;
  meta?: Record<string, unknown>;
  comment?: string | null;
  review_status?: SitePageDraft['review_status'];
};

export type FetchSitePageHistoryParams = {
  limit?: number;
  offset?: number;
};

export type FetchSiteGlobalBlocksParams = {
  page?: number;
  pageSize?: number;
  section?: string;
  status?: SiteGlobalBlockStatus | '';
  locale?: string;
  query?: string;
  hasDraft?: boolean | null;
  requiresPublisher?: boolean | null;
  reviewStatus?: SiteGlobalBlock['review_status'] | '';
  sort?: 'updated_at_desc' | 'updated_at_asc' | 'title_asc' | 'usage_desc';
};

export type FetchSiteGlobalBlockMetricsParams = {
  period?: SiteMetricsPeriod;
  locale?: string;
};

export type CreateSiteGlobalBlockPayload = {
  key: string;
  title: string;
  section: string;
  locale?: string | null;
  requires_publisher?: boolean;
  data?: Record<string, unknown>;
  meta?: Record<string, unknown>;
};

export type SaveSiteGlobalBlockPayload = {
  version?: number | null;
  data?: Record<string, unknown>;
  meta?: Record<string, unknown>;
  comment?: string | null;
  review_status?: SiteGlobalBlock['review_status'];
};

export type PublishSiteGlobalBlockPayload = {
  version?: number | null;
  comment?: string | null;
  acknowledgeUsage?: boolean;
};

export type FetchSiteGlobalBlockHistoryParams = {
  limit?: number;
  offset?: number;
};

export type FetchSiteAuditParams = {
  entityType?: string;
  entityId?: string;
  actor?: string;
  limit?: number;
  offset?: number;
};

export type PreviewSiteBlockParams = {
  locale?: string;
  limit?: number;
};

export type PreviewSitePagePayload = {
  data?: Record<string, unknown>;
  meta?: Record<string, unknown>;
  layouts?: string[];
  version?: number;
};

export type SiteBlockPreviewItem = {
  id?: string | null;
  title: string;
  subtitle?: string | null;
  href?: string | null;
  badge?: string | null;
  provider?: string | null;
  score?: number | null;
  probability?: number | null;
};

export type SiteBlockPreviewResponse = {
  block: string;
  locale: string;
  items: SiteBlockPreviewItem[];
  source?: string | null;
  fetched_at?: string | null;
  fetchedAt?: string | null;
  meta?: Record<string, unknown>;
  warnings?: SiteGlobalBlockWarning[];
};

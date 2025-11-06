import type {
  SiteBlock,
  SiteBlockStatus,
  SiteBlockTemplate,
  SiteBlockTemplateListResponse,
  SiteBlockWarning,
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

export type ListSharedBindingsParams = {
  locale?: string | null;
  includeInactive?: boolean;
};

export type AssignSharedBindingPayload = {
  block_id: string;
  locale?: string | null;
};

export type DeleteSharedBindingParams = {
  locale?: string | null;
};

export type FetchSiteBlocksParams = {
  page?: number;
  pageSize?: number;
  section?: string;
  status?: SiteBlockStatus | '';
  scope?: SiteBlock['scope'] | '';
  locale?: string;
  query?: string;
  hasDraft?: boolean | null;
  requiresPublisher?: boolean | null;
  reviewStatus?: SiteBlock['review_status'] | '';
  sort?: 'updated_at_desc' | 'updated_at_asc' | 'title_asc' | 'usage_desc';
  includeData?: boolean;
  isTemplate?: boolean | null;
  originBlockId?: string | null;
};

export type FetchSiteBlockMetricsParams = {
  period?: SiteMetricsPeriod;
  locale?: string;
};

export type CreateSiteBlockPayload = {
  key: string;
  title: string;
  template_id?: string | null;
  template_key?: string | null;
  section: string;
  scope?: SiteBlock['scope'];
  default_locale?: string | null;
  available_locales?: string[] | null;
  requires_publisher?: boolean;
  data?: Record<string, unknown>;
  meta?: Record<string, unknown>;
  is_template?: boolean;
  origin_block_id?: string | null;
};

export type SaveSiteBlockPayload = {
  version?: number | null;
  data?: Record<string, unknown>;
  meta?: Record<string, unknown>;
  comment?: string | null;
  review_status?: SiteBlock['review_status'];
  title?: string | null;
  section?: string | null;
  default_locale?: string | null;
  available_locales?: string[] | null;
  requires_publisher?: boolean | null;
  is_template?: boolean | null;
  origin_block_id?: string | null;
};

export type PublishSiteBlockPayload = {
  version?: number | null;
  comment?: string | null;
  acknowledgeUsage?: boolean;
};

export type ArchiveSiteBlockPayload = {
  restore?: boolean;
};

export type FetchSiteBlockHistoryParams = {
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
  warnings?: SiteBlockWarning[];
};

export type FetchBlockTemplatesParams = {
  status?: string | string[];
  section?: string;
  query?: string;
  includeData?: boolean;
};

export type SiteBlockTemplateList = SiteBlockTemplateListResponse;

export type SiteBlockTemplateDetail = SiteBlockTemplate;

export type CreateBlockTemplatePayload = {
  key: string;
  title: string;
  section?: string;
  description?: string | null;
  status?: string;
  default_locale?: string | null;
  available_locales?: string[] | null;
  block_type?: string | null;
  category?: string | null;
  sources?: string[] | null;
  surfaces?: string[] | null;
  owners?: string[] | null;
  catalog_locales?: string[] | null;
  documentation_url?: string | null;
  keywords?: string[] | null;
  preview_kind?: string | null;
  status_note?: string | null;
  requires_publisher?: boolean;
  allow_shared_scope?: boolean;
  allow_page_scope?: boolean;
  shared_note?: string | null;
  key_prefix?: string | null;
  default_data?: Record<string, unknown>;
  default_meta?: Record<string, unknown>;
};

export type UpdateBlockTemplatePayload = Partial<CreateBlockTemplatePayload>;

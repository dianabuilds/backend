export type SitePageBlockItem = {
  id: string;
  title: string | null;
  summary: string | null;
  slug: string | null;
  href: string | null;
  publishAt: string | null;
  updatedAt: string | null;
  coverUrl: string | null;
  provider?: string | null;
  data?: Record<string, unknown> | null;
  extras?: Record<string, unknown> | null;
};

export type SitePageBlock = {
  id: string;
  type: string;
  enabled: boolean;
  title: string | null;
  subtitle: string | null;
  section: string | null;
  source: string | null;
  layout: Record<string, unknown> | null;
  slots: Record<string, unknown> | null;
  dataSource?: Record<string, unknown> | null;
  data: Record<string, unknown> | null;
  meta: Record<string, unknown> | null;
  items: SitePageBlockItem[];
  extras?: Record<string, unknown> | null;
};

export type SitePageFallbackEntry = Record<string, unknown>;

export type SiteBlockStatus = "draft" | "published" | "archived";
export type SiteBlockReviewStatus = "none" | "pending" | "approved" | "rejected";
export type SiteBlockScope = "shared" | "page" | string;

export type SiteBlock = {
  id: string;
  key: string | null;
  title: string | null;
  section: string;
  scope: SiteBlockScope;
  defaultLocale: string;
  availableLocales: string[];
  locale: string | null;
  status: SiteBlockStatus;
  reviewStatus: SiteBlockReviewStatus;
  requiresPublisher: boolean;
  publishedVersion: number | null;
  draftVersion: number | null;
  version: number;
  comment: string | null;
  data: Record<string, unknown>;
  meta: Record<string, unknown>;
  updatedAt: string | null;
  updatedBy: string | null;
  publishedAt: string | null;
  hasPendingPublish: boolean;
  sections: string[];
  extras?: Record<string, unknown> | null;
};

export type SiteBlockMap = Record<string, SiteBlock>;

export type SiteBlockRef = {
  blockId?: string | null;
  key: string;
  section: string | null;
  scope?: SiteBlockScope | null;
};

export type SiteBlockBinding = {
  blockId: string;
  pageId: string;
  key: string | null;
  title: string | null;
  section: string | null;
  locale: string;
  defaultLocale: string | null;
  availableLocales: string[] | null;
  position: number;
  active: boolean;
  hasDraft: boolean;
  lastPublishedAt: string | null;
  updatedAt: string | null;
  updatedBy: string | null;
  requiresPublisher: boolean;
  status: SiteBlockStatus | null;
  reviewStatus: SiteBlockReviewStatus | null;
  scope: SiteBlockScope | null;
  extras?: Record<string, unknown> | null;
};

export type SitePageResponse = {
  pageId: string | null;
  slug: string;
  locale: string | null;
  requestedLocale: string | null;
  fallbackLocale: string | null;
  availableLocales: string[];
  localizedSlugs: Record<string, string>;
  title: string | null;
  type: string | null;
  source: string | null;
  version: number;
  publishedAt: string | null;
  publishedBy: string | null;
  updatedAt: string | null;
  generatedAt: string | null;
  meta: Record<string, unknown>;
  payload: Record<string, unknown>;
  blocks: SitePageBlock[];
  fallbacks: SitePageFallbackEntry[];
  blocksMap: SiteBlockMap;
  blockRefs: SiteBlockRef[];
  blockBindings: SiteBlockBinding[];
};

export type NormalizeSitePageOptions = {
  fallbackSlug?: string;
};

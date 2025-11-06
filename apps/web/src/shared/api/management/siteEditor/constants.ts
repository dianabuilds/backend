import type { SiteBlockStatus, SitePageStatus, SitePageType } from '@shared/types/management';

export const PAGE_TYPES: SitePageType[] = ['landing', 'collection', 'article', 'system'];
export const PAGE_STATUSES: SitePageStatus[] = ['draft', 'published', 'archived'];
export const SORT_ORDERS = new Set(
  ['updated_at_desc', 'updated_at_asc', 'title_asc', 'title_desc', 'pinned_desc', 'pinned_asc'] as const,
);
export const REVIEW_STATUSES = new Set(['none', 'pending', 'approved', 'rejected']);
export const BLOCK_STATUSES: SiteBlockStatus[] = ['draft', 'published', 'archived'];
export const BLOCK_SORT = new Set(['updated_at_desc', 'updated_at_asc', 'title_asc', 'usage_desc'] as const);


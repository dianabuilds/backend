import type { SiteBlock, SiteBlockStatus } from '@shared/types/management';

export type FilterValue<T> = T | 'all';

export type FiltersState = {
  search: string;
  status: FilterValue<SiteBlockStatus>;
  scope: FilterValue<string>;
  locale: FilterValue<string>;
  owner: FilterValue<string>;
  requiresPublisher: FilterValue<'true' | 'false'>;
  reviewStatus: FilterValue<SiteBlock['review_status']>;
};

export type DetailTab =
  | 'overview'
  | 'settings'
  | 'preview'
  | 'history'
  | 'usage'
  | 'warnings';

import type { SitePageLocaleStatus } from '@shared/types/management';
import type { HomeBlock } from '../home/types';

export type LocaleDraftState = {
  locale: string;
  blocks: HomeBlock[];
  meta: Record<string, unknown> | null;
  status?: SitePageLocaleStatus | string | null;
  slug?: string | null;
  title?: string | null;
  description?: string | null;
};


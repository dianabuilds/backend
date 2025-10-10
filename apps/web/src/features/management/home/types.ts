import type { ValidationSummary } from './validation';
import type { HomeHistoryEntry } from '@shared/types/home';
export type HomeBlockType =
  | 'hero'
  | 'dev_blog_list'
  | 'quests_carousel'
  | 'nodes_carousel'
  | 'popular_carousel'
  | 'editorial_picks'
  | 'recommendations'
  | 'custom_carousel';

export type HomeBlockDataSourceMode = 'manual' | 'auto';

export type HomeBlockDataSourceEntity = 'node' | 'quest' | 'dev_blog' | 'custom';

export type HomeBlockDataSource = {
  mode: HomeBlockDataSourceMode;
  entity?: HomeBlockDataSourceEntity;
  filter?: Record<string, unknown> | null;
  items?: Array<string | number> | null;
};

export type HomeBlock = {
  id: string;
  type: HomeBlockType;
  title?: string;
  enabled: boolean;
  slots?: Record<string, unknown> | null;
  layout?: Record<string, unknown> | null;
  dataSource?: HomeBlockDataSource | null;
};

export type HomeDraftData = {
  blocks: HomeBlock[];
  meta?: Record<string, unknown> | null;
};

export type HomeDraftSnapshot = {
  version: number | null;
  updatedAt: string | null;
  publishedAt: string | null;
};

export type HomeEditorContextValue = {
  loading: boolean;
  data: HomeDraftData;
  setData: (updater: (prev: HomeDraftData) => HomeDraftData) => void;
  setBlocks: (blocks: HomeBlock[]) => void;
  selectBlock: (blockId: string | null) => void;
  selectedBlockId: string | null;
  dirty: boolean;
  saving: boolean;
  savingError: string | null;
  lastSavedAt: string | null;
  loadDraft: (opts?: { silent?: boolean }) => Promise<void>;
  saveDraft: (opts?: { silent?: boolean }) => Promise<void>;
  snapshot: HomeDraftSnapshot;
  slug: string;
  history: HomeHistoryEntry[];
  publishing: boolean;
  restoringVersion: number | null;
  publishDraft: (options?: { comment?: string }) => Promise<void>;
  restoreVersion: (version: number, options?: { comment?: string }) => Promise<void>;
  validation: ValidationSummary;
  revalidate: () => ValidationSummary;
};


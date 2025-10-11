export type HomeDataSource = {
  mode?: 'manual' | 'auto';
  entity?: string | null;
  items?: Array<string | number> | null;
  filter?: Record<string, unknown> | null;
};

export type HomeBlockItem = {
  id?: string | number | null;
  slug?: string | null;
  title?: string | null;
  summary?: string | null;
  coverUrl?: string | null;
  publishAt?: string | null;
  updatedAt?: string | null;
  author?: {
    id?: string | null;
    name?: string | null;
  } | null;
  [key: string]: unknown;
};

export type HomeBlockPayload = {
  id: string;
  type: string;
  title?: string | null;
  enabled: boolean;
  slots?: Record<string, unknown> | null;
  layout?: Record<string, unknown> | null;
  items?: HomeBlockItem[] | null;
  dataSource?: HomeDataSource | null;
};

export type HomeFallbackEntry = Record<string, unknown>;

export type HomeResponse = {
  slug: string;
  version: number;
  updatedAt: string | null;
  publishedAt: string | null;
  generatedAt: string | null;
  blocks: HomeBlockPayload[];
  meta: Record<string, unknown>;
  fallbacks: HomeFallbackEntry[];
  etag?: string | null;
};



export type EmbeddingStatus = 'ready' | 'pending' | 'disabled' | 'error' | 'unknown';

export type NodeItem = {
  id: string;
  title?: string | null;
  slug?: string | null;
  author_name?: string | null;
  author_id?: string | null;
  is_public?: boolean;
  status?: string | null;
  updated_at?: string | null;
  embedding_status?: EmbeddingStatus | null;
  embedding_ready?: boolean;
};

export type NodeLifecycleStatus =
  | 'draft'
  | 'published'
  | 'scheduled'
  | 'scheduled_unpublish'
  | 'archived'
  | 'deleted';

export type NodeStatusFilter = 'all' | NodeLifecycleStatus;

export type NodeSortKey = 'updated_at' | 'title' | 'author' | 'status';

export type NodeSortOrder = 'asc' | 'desc';

export type NodesListMeta = {
  total: number | null;
  published: number | null;
  drafts: number | null;
  pendingEmbeddings: number | null;
};

export type NodesListResult = {
  items: NodeItem[];
  meta: NodesListMeta;
  hasNext: boolean;
};

export type NodeUserOption = {
  id: string;
  username: string;
};

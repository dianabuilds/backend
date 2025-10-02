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

export type NodeStatus = 'all' | 'draft' | 'published' | 'scheduled' | 'scheduled_unpublish' | 'archived' | 'deleted';

export type SortKey = 'updated_at' | 'title' | 'author' | 'status';
export type SortOrder = 'asc' | 'desc';

export type UserOption = { id: string; username: string };

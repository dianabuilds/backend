export type AdminNodeEngagementSummary = {
  id: string;
  slug?: string | null;
  title?: string | null;
  status?: string | null;
  is_public?: boolean | null;
  author_id?: string | null;
  views_count?: number | null;
  reactions?: Record<string, number> | null;
  comments?: AdminNodeEngagementCommentSummary | null;
  created_at?: string | null;
  updated_at?: string | null;
  links?: {
    moderation?: string | null;
    comments?: string | null;
    analytics?: string | null;
    bans?: string | null;
  } | null;
};

export type AdminNodeEngagementCommentSummary = {
  total?: number | null;
  by_status?: Record<string, number> | null;
  disabled?: boolean | null;
  locked?: boolean | null;
  locked_by?: string | null;
  locked_at?: string | null;
  last_comment_created_at?: string | null;
  last_comment_updated_at?: string | null;
  bans_count?: number | null;
};

export type AdminNodeCommentHistoryEntry = {
  status?: string | null;
  actor_id?: string | null;
  reason?: string | null;
  at?: string | null;
};

export type AdminNodeComment = {
  id: string;
  node_id: number | string;
  author_id?: string | null;
  parent_comment_id?: number | string | null;
  depth: number;
  content: string;
  status: string;
  metadata: Record<string, unknown>;
  history?: AdminNodeCommentHistoryEntry[];
  created_at?: string | null;
  updated_at?: string | null;
  children_count?: number | null;
};

export type AdminNodeCommentsSummary = {
  total: number;
  by_status: Record<string, number>;
};

export type AdminNodeCommentsResponse = {
  items: AdminNodeComment[];
  summary: AdminNodeCommentsSummary;
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
  view?: AdminNodeCommentView;
  filters?: {
    statuses?: string[];
    author_id?: string | null;
    created_from?: string | null;
    created_to?: string | null;
    search?: string | null;
    include_deleted?: boolean | null;
  };
};

export type AdminNodeCommentView = 'roots' | 'children' | 'all' | 'thread';

export type AdminNodeCommentsQuery = {
  view?: AdminNodeCommentView;
  parentId?: string | number;
  statuses?: string[];
  authorId?: string;
  createdFrom?: string;
  createdTo?: string;
  search?: string;
  includeDeleted?: boolean;
  limit?: number;
  offset?: number;
  order?: 'asc' | 'desc';
};

export type AdminNodeCommentBan = {
  node_id: number | string;
  target_user_id: string;
  set_by: string;
  reason?: string | null;
  created_at?: string | null;
};

export type AdminNodeAnalyticsBucket = {
  bucket_date: string;
  views: number;
};

export type AdminNodeAnalytics = {
  id: string;
  range: {
    start?: string | null;
    end?: string | null;
  };
  views: {
    total: number;
    buckets: AdminNodeAnalyticsBucket[];
    last_updated_at?: string | null;
  };
  reactions: {
    totals: Record<string, number>;
    last_reaction_at?: string | null;
  };
  comments: {
    total: number;
    by_status: Record<string, number>;
    last_created_at?: string | null;
  };
  delay?: {
    seconds: number;
    calculated_at?: string | null;
    latest_at?: string | null;
  } | null;
};

export type AdminNodeAnalyticsQuery = {
  start?: string;
  end?: string;
  limit?: number;
  format?: 'json' | 'csv';
};

export type AdminCommentStatusPayload = {
  status: string;
  reason?: string;
};

export type AdminCommentDeleteOptions = {
  hard?: boolean;
  reason?: string;
};

export type AdminCommentLockPayload = {
  locked: boolean;
  reason?: string;
};

export type AdminCommentDisablePayload = {
  disabled: boolean;
  reason?: string;
};

export type AdminCommentBanPayload = {
  target_user_id: string;
  reason?: string;
};

export type HomeConfigStatus = 'draft' | 'published';

export type HomeConfigSnapshot = {
  id: string;
  slug: string;
  version: number;
  status: HomeConfigStatus;
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  published_at: string | null;
  created_by: string | null;
  updated_by: string | null;
  draft_of: string | null;
};

export type HomeConfigPayload = {
  slug?: string;
  data?: Record<string, unknown> | null;
  comment?: string | null;
};

export type HomeHistoryEntry = {
  configId: string;
  version: number;
  action: string;
  actor: string | null;
  actorTeam: string | null;
  comment: string | null;
  createdAt: string;
  publishedAt: string | null;
  isCurrent: boolean;
};

export type HomeAdminPayload = {
  slug: string;
  draft: HomeConfigSnapshot | null;
  published: HomeConfigSnapshot | null;
  history: HomeHistoryEntry[];
};

export type HomePublishResult = {
  slug: string;
  published: HomeConfigSnapshot;
};

export type HomePreviewResult = {
  slug: string;
  payload: Record<string, unknown>;
};

export type HomeRestoreResult = {
  slug: string;
  draft: HomeConfigSnapshot;
};

export type HomeErrorPayload = {
  code?: string;
  detail?: unknown;
  details?: unknown;
  error?: string;
  message?: unknown;
};


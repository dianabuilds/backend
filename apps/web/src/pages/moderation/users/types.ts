export type StatusFilterValue = 'all' | 'active' | 'banned' | 'pending' | 'review';

export type RoleFilterValue = 'any' | 'user' | 'support' | 'moderator' | 'admin';

export type RiskFilterValue = 'any' | 'low' | 'medium' | 'high';

export type SortKey = 'registered_at' | 'last_seen_at' | 'complaints_count' | 'sanction_count';

export type SortOrder = 'asc' | 'desc';

export type SortState = { key: SortKey; order: SortOrder };

export type DrawerTabKey = 'overview' | 'roles' | 'sanctions' | 'notes' | 'activity';

export type ModerationRole = 'user' | 'support' | 'moderator' | 'admin';

export type RiskLevel = 'low' | 'medium' | 'high' | 'unknown';

export type BadgeTone = 'success' | 'error' | 'warning' | 'neutral' | 'info';

export type SanctionRecord = {
  id: string;
  type: string;
  status: string;
  reason?: string | null;
  issued_by?: string | null;
  issued_at?: string | null;
  starts_at?: string | null;
  ends_at?: string | null;
  revoked_at?: string | null;
  revoked_by?: string | null;
  meta?: Record<string, unknown>;
};

export type ModeratorNote = {
  id: string;
  text: string;
  author_id?: string | null;
  author_name?: string | null;
  created_at?: string | null;
  pinned?: boolean;
  meta?: Record<string, unknown>;
};

export type ModerationReport = {
  id: string;
  object_type?: string;
  object_id?: string;
  reporter_id?: string;
  category?: string;
  text?: string | null;
  status?: string;
  created_at?: string | null;
  resolved_at?: string | null;
  decision?: string | null;
  meta?: Record<string, unknown>;
};

export type ModerationTicket = {
  id: string;
  title?: string;
  priority?: string;
  author_id?: string;
  assignee_id?: string | null;
  status?: string;
  created_at?: string | null;
  updated_at?: string | null;
  last_message_at?: string | null;
  unread_count?: number;
  meta?: Record<string, unknown>;
};

export type ModerationCaseSummary = {
  id?: string;
  type?: string;
  status?: string;
  priority?: string;
  opened_at?: string | null;
  meta?: Record<string, unknown>;
};

export type ModerationUserSummary = {
  id: string;
  username: string;
  email: string | null;
  roles: string[];
  status: string;
  registered_at: string | null;
  last_seen_at: string | null;
  complaints_count: number;
  notes_count: number;
  sanction_count: number;
  active_sanctions: SanctionRecord[];
  last_sanction: SanctionRecord | null;
  meta: Record<string, unknown>;
};

export type ModerationUserDetail = ModerationUserSummary & {
  sanctions: SanctionRecord[];
  reports: ModerationReport[];
  tickets: ModerationTicket[];
  notes: ModeratorNote[];
  cases?: ModerationCaseSummary[];
};

export type ModerationUsersResponse = {
  items?: Array<Record<string, unknown>>;
  total?: number;
  next_cursor?: string | null;
  meta?: Record<string, unknown>;
};

export type FilterState = {
  status: StatusFilterValue;
  role: RoleFilterValue;
  risk: RiskFilterValue;
  registrationFrom: string;
  registrationTo: string;
};

export type ListState = {
  items: ModerationUserSummary[];
  loading: boolean;
  error: string | null;
  nextCursor: string | null;
  totalItems?: number;
  meta?: Record<string, unknown>;
};

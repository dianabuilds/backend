import type { ApexOptions } from 'apexcharts';
export type ModerationRole = 'user' | 'support' | 'moderator' | 'admin';

export type ModerationRiskLevel = 'low' | 'medium' | 'high' | 'unknown';

export type ModerationBadgeTone = 'success' | 'error' | 'warning' | 'neutral' | 'info';

export type ModerationSanctionRecord = {
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
  target_type?: string | null;
  target_id?: string | null;
  moderator?: string | null;
  evidence?: unknown[];
  meta: Record<string, unknown>;
};

export type ModerationNote = {
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
  active_sanctions: ModerationSanctionRecord[];
  last_sanction: ModerationSanctionRecord | null;
  meta: Record<string, unknown>;
};

export type ModerationUserDetail = ModerationUserSummary & {
  sanctions: ModerationSanctionRecord[];
  reports: ModerationReport[];
  tickets: ModerationTicket[];
  notes: ModerationNote[];
  cases?: ModerationCaseSummary[];
};

export type ModerationUsersList = {
  items: ModerationUserSummary[];
  nextCursor: string | null;
  total?: number;
  meta?: Record<string, unknown>;
};

export type ModerationAIRule = {
  id: string;
  category: string;
  enabled: boolean;
  description: string | null;
  default_action: string | null;
  threshold: number | null;
  updated_by: string | null;
  updated_at: string | null;
  metrics?: Record<string, unknown>;
  meta?: Record<string, unknown>;
};

export type ModerationAIRulesList = {
  items: ModerationAIRule[];
  total?: number;
  hasNext: boolean;
};

export type ModerationOverviewCardAction = {
  label: string;
  to?: string;
  href?: string;
  kind?: 'primary' | 'secondary' | 'danger' | 'ghost';
};

export type ModerationOverviewCard = {
  id: string;
  title: string;
  value?: string;
  subtitle?: string;
  delta?: string;
  trend?: 'up' | 'down' | 'steady';
  description?: string;
  status?: string | null;
  meta?: Record<string, unknown>;
  roleVisibility?: string[];
  actions: ModerationOverviewCardAction[];
};

export type ModerationOverviewChart = {
  id: string;
  title: string;
  description?: string;
  type?: 'line' | 'bar' | 'pie' | string;
  series?: unknown;
  options?: ApexOptions;
  height?: number;
};

export type ModerationOverview = {
  complaints: Record<string, number>;
  tickets: Record<string, number>;
  contentQueues: Record<string, number>;
  lastSanctions: ModerationSanctionRecord[];
  cards: ModerationOverviewCard[];
  charts: ModerationOverviewChart[];
};

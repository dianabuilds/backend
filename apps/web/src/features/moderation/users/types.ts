import type {
  ModerationRole as SharedModerationRole,
  ModerationUserDetail as SharedModerationUserDetail,
  ModerationUserSummary as SharedModerationUserSummary,
  ModerationSanctionRecord,
  ModerationNote,
  ModerationReport,
  ModerationTicket,
  ModerationCaseSummary,
} from '@shared/types/moderation';

export type StatusFilterValue = 'all' | 'active' | 'banned' | 'pending' | 'review';

export type RoleFilterValue = 'any' | SharedModerationRole;

export type RiskFilterValue = 'any' | 'low' | 'medium' | 'high';

export type SortKey = 'registered_at' | 'last_seen_at' | 'complaints_count' | 'sanction_count';

export type SortOrder = 'asc' | 'desc';

export type SortState = { key: SortKey; order: SortOrder };

export type DrawerTabKey = 'overview' | 'roles' | 'sanctions' | 'notes' | 'activity';

export type ModerationRole = SharedModerationRole;

export type ModerationUserSummary = SharedModerationUserSummary;

export type ModerationUserDetail = SharedModerationUserDetail;

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

export type ModerationSanction = ModerationSanctionRecord;
export type ModerationNoteRecord = ModerationNote;
export type ModerationUserReport = ModerationReport;
export type ModerationUserTicket = ModerationTicket;
export type ModerationUserCase = ModerationCaseSummary;

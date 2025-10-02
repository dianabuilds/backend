export type CaseNote = {
  id?: string;
  text: string;
  visibility?: 'internal' | 'external' | string | null;
  pinned?: boolean | null;
  created_at?: string | null;
  author_id?: string | null;
  author_name?: string | null;
  direction?: 'inbound' | 'outbound' | string | null;
  channel?: string | null;
  status?: string | null;
  meta?: Record<string, any> | null;
  attachments?: Array<{ id?: string; type?: string; url?: string; name?: string }>;
};

export type CaseEvent = {
  id?: string;
  type?: string;
  title?: string | null;
  description?: string | null;
  actor?: string | null;
  field?: string | null;
  from?: any;
  to?: any;
  created_at?: string | null;
};

export type CaseLink = {
  label: string;
  href: string;
  type?: string | null;
};

export type ModerationCaseSummary = {
  id: string;
  title?: string | null;
  status?: string | null;
  type?: string | null;
  queue?: string | null;
  severity?: string | null;
  priority?: string | null;
  assignee_id?: string | null;
  assignee_label?: string | null;
  subject_id?: string | null;
  subject_type?: string | null;
  subject_label?: string | null;
  updated_at?: string | null;
  created_at?: string | null;
  tags?: string[] | null;
  [key: string]: any;
};

export type ModerationCaseDetail = ModerationCaseSummary & {
  description?: string | null;
  metadata?: Record<string, any> | null;
  notes?: CaseNote[];
  events?: CaseEvent[];
  links?: CaseLink[];
};

export type CasesListResponse = {
  items?: ModerationCaseSummary[];
  total?: number;
  page?: number;
  size?: number;
};

export type CaseFiltersState = {
  query: string;
  statuses: string[];
  types: string[];
  queues: string[];
  severities: string[];
  priorities: string[];
  assignee: string;
  tags: string[];
};

import {
  BadgeTone,
  ModerationCaseSummary,
  ModerationReport,
  ModerationRole,
  ModerationTicket,
  ModerationUserDetail,
  ModerationUserSummary,
  ModeratorNote,
  RiskLevel,
  SanctionRecord,
} from './types';

const dateTimeFormatter = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

export function ensureArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

export function toTitleCase(value: string): string {
  return value
    .split(/[\s_]+/)
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(' ');
}

export function formatDateTime(value?: string | null): string {
  if (!value) return 'N/A';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return typeof value === 'string' ? value : 'N/A';
  const formatted = dateTimeFormatter.format(dt);
  return formatted.replace(/\u202f/gu, ' ').replace(/\u00a0/gu, ' ');
}

export function formatRelativeTime(value?: string | null): string {
  if (!value) return 'N/A';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return typeof value === 'string' ? value : 'N/A';
  const diffMs = Date.now() - dt.getTime();
  const diffMinutes = Math.round(diffMs / 60000);
  if (diffMinutes < 1) return 'just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.round(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDateTime(value);
}

export function statusToBadgeTone(status?: string | null): BadgeTone {
  const normalized = (status || '').toLowerCase();
  if (['active', 'ok', 'approved'].includes(normalized)) return 'success';
  if (['banned', 'blocked', 'suspended'].includes(normalized)) return 'error';
  if (['pending', 'review', 'flagged'].includes(normalized)) return 'warning';
  if (['escalated'].includes(normalized)) return 'info';
  return 'neutral';
}

export function capitalizeRole(role: string): string {
  const lower = role.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

export function normalizeSanction(raw: Record<string, unknown>): SanctionRecord {
  return {
    id: String(raw?.id ?? `${raw?.type ?? 'sanction'}-${raw?.issued_at ?? Date.now()}`),
    type: String(raw?.type ?? 'sanction'),
    status: String(raw?.status ?? 'active'),
    reason: (raw?.reason as string | null) ?? null,
    issued_by: (raw?.issued_by as string | null) ?? null,
    issued_at: (raw?.issued_at as string | null) ?? null,
    starts_at: (raw?.starts_at as string | null) ?? null,
    ends_at: (raw?.ends_at as string | null) ?? null,
    revoked_at: (raw?.revoked_at as string | null) ?? null,
    revoked_by: (raw?.revoked_by as string | null) ?? null,
    meta: typeof raw?.meta === 'object' && raw?.meta !== null ? (raw.meta as Record<string, unknown>) : {},
  };
}

export function normalizeNote(raw: Record<string, unknown>, index: number): ModeratorNote {
  return {
    id: String(raw?.id ?? `note-${index}`),
    text: String(raw?.text ?? ''),
    author_id: (raw?.author_id as string | null) ?? null,
    author_name: (raw?.author_name as string | null) ?? null,
    created_at: (raw?.created_at as string | null) ?? null,
    pinned: Boolean(raw?.pinned),
    meta: typeof raw?.meta === 'object' && raw?.meta !== null ? (raw.meta as Record<string, unknown>) : {},
  };
}

export function normalizeReport(raw: Record<string, unknown>, index: number): ModerationReport {
  return {
    id: String(raw?.id ?? `report-${index}`),
    object_type: (raw?.object_type as string | undefined) ?? undefined,
    object_id: (raw?.object_id as string | undefined) ?? undefined,
    reporter_id: (raw?.reporter_id as string | undefined) ?? undefined,
    category: (raw?.category as string | undefined) ?? undefined,
    text: (raw?.text as string | null) ?? null,
    status: (raw?.status as string | undefined) ?? undefined,
    created_at: (raw?.created_at as string | null) ?? null,
    resolved_at: (raw?.resolved_at as string | null) ?? null,
    decision: (raw?.decision as string | null) ?? null,
    meta: typeof raw?.meta === 'object' && raw?.meta !== null ? (raw.meta as Record<string, unknown>) : {},
  };
}

export function normalizeTicket(raw: Record<string, unknown>, index: number): ModerationTicket {
  return {
    id: String(raw?.id ?? `ticket-${index}`),
    title: (raw?.title as string | undefined) ?? undefined,
    priority: (raw?.priority as string | undefined) ?? undefined,
    author_id: (raw?.author_id as string | undefined) ?? undefined,
    assignee_id: (raw?.assignee_id as string | null) ?? null,
    status: (raw?.status as string | undefined) ?? undefined,
    created_at: (raw?.created_at as string | null) ?? null,
    updated_at: (raw?.updated_at as string | null) ?? null,
    last_message_at: (raw?.last_message_at as string | null) ?? null,
    unread_count: Number.isFinite(raw?.unread_count) ? Number(raw?.unread_count) : undefined,
    meta: typeof raw?.meta === 'object' && raw?.meta !== null ? (raw.meta as Record<string, unknown>) : {},
  };
}

export function normalizeCase(raw: Record<string, unknown>, index: number): ModerationCaseSummary {
  return {
    id: raw?.id ? String(raw.id) : `case-${index}`,
    type: raw?.type ? String(raw.type) : undefined,
    status: raw?.status ? String(raw.status) : undefined,
    priority: raw?.priority ? String(raw.priority) : undefined,
    opened_at: (raw?.opened_at as string | null) ?? null,
    meta: typeof raw?.meta === 'object' && raw?.meta !== null ? (raw.meta as Record<string, unknown>) : {},
  };
}

export function normalizeUserSummary(raw: Record<string, unknown>): ModerationUserSummary {
  const baseRoles = ensureArray<string>(raw?.roles ?? raw?.role);
  return {
    id: String(raw?.id ?? ''),
    username: raw?.username ? String(raw.username) : raw?.email ? String(raw.email) : String(raw?.id ?? 'Unknown user'),
    email: typeof raw?.email === 'string' ? raw.email : null,
    roles: baseRoles.map(String),
    status: raw?.status ? String(raw.status) : 'active',
    registered_at: (raw?.registered_at as string | null) ?? (raw?.registeredAt as string | null) ?? null,
    last_seen_at: (raw?.last_seen_at as string | null) ?? (raw?.lastSeenAt as string | null) ?? null,
    complaints_count: Number.isFinite(raw?.complaints_count)
      ? Number(raw?.complaints_count)
      : Number.isFinite(raw?.complaintsCount)
      ? Number(raw?.complaintsCount)
      : 0,
    notes_count: Number.isFinite(raw?.notes_count)
      ? Number(raw?.notes_count)
      : Number.isFinite(raw?.notesCount)
      ? Number(raw?.notesCount)
      : 0,
    sanction_count: Number.isFinite(raw?.sanction_count)
      ? Number(raw?.sanction_count)
      : Number.isFinite(raw?.sanctionCount)
      ? Number(raw?.sanctionCount)
      : 0,
    active_sanctions: ensureArray<Record<string, unknown>>(raw?.active_sanctions ?? raw?.activeSanctions).map(normalizeSanction),
    last_sanction: raw?.last_sanction ? normalizeSanction(raw.last_sanction as Record<string, unknown>) : null,
    meta: typeof raw?.meta === 'object' && raw?.meta !== null ? (raw.meta as Record<string, unknown>) : {},
  };
}

export function normalizeUserDetail(raw: Record<string, unknown>): ModerationUserDetail {
  const summary = normalizeUserSummary(raw);
  const sanctions = ensureArray<Record<string, unknown>>(raw?.sanctions).map(normalizeSanction);
  const reports = ensureArray<Record<string, unknown>>(raw?.reports).map((item, index) => normalizeReport(item, index));
  const tickets = ensureArray<Record<string, unknown>>(raw?.tickets).map((item, index) => normalizeTicket(item, index));
  const notes = ensureArray<Record<string, unknown>>(raw?.notes).map((item, index) => normalizeNote(item, index));
  const cases = ensureArray<Record<string, unknown>>(raw?.cases ?? raw?.open_cases ?? raw?.pending_cases).map((item, index) =>
    normalizeCase(item, index),
  );
  return {
    ...summary,
    sanctions,
    reports,
    tickets,
    notes,
    cases,
  };
}

export function resolvePreferredRole(roles: string[]): ModerationRole {
  const normalized = roles.map((role) => role.toLowerCase()) as ModerationRole[];
  if (normalized.includes('admin')) return 'admin';
  if (normalized.includes('moderator')) return 'moderator';
  if (normalized.includes('support')) return 'support';
  return 'user';
}

export function resolveRiskLevel(user: ModerationUserSummary): RiskLevel {
  const meta = (user.meta ?? {}) as Record<string, unknown>;
  const directSource = meta['risk_label'] ?? meta['risk'] ?? meta['riskLevel'] ?? '';
  const direct = String(directSource).toLowerCase();
  if (direct === 'high' || direct === 'medium' || direct === 'low') return direct as RiskLevel;
  const numericSource = meta['risk_score'] ?? meta['riskScore'] ?? meta['score'];
  const numeric = Number(numericSource);
  if (Number.isFinite(numeric)) {
    if (numeric >= 0.75) return 'high';
    if (numeric >= 0.4) return 'medium';
    return 'low';
  }
  if (user.sanction_count > 3 || user.complaints_count > 15) return 'high';
  if (user.sanction_count > 0 || user.complaints_count > 0) return 'medium';
  return 'low';
}

export function riskBadgeProps(level: RiskLevel): { label: string; color: BadgeTone } {
  switch (level) {
    case 'high':
      return { label: 'High', color: 'error' };
    case 'medium':
      return { label: 'Medium', color: 'warning' };
    case 'low':
      return { label: 'Low', color: 'success' };
    default:
      return { label: 'Unknown', color: 'neutral' };
  }
}



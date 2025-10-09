import type {
  ModerationCaseSummary,
  ModerationNote,
  ModerationReport,
  ModerationSanctionRecord,
  ModerationTicket,
  ModerationUserDetail,
  ModerationUserSummary,
} from '../../types/moderation';

export function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

export function pickString(value: unknown): string | undefined {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length ? trimmed : undefined;
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return String(value);
  }
  return undefined;
}

export function pickNullableString(value: unknown): string | null | undefined {
  if (value === null) return null;
  return pickString(value);
}

export function pickNumber(value: unknown): number | undefined {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    if (!Number.isNaN(parsed)) {
      return parsed;
    }
  }
  return undefined;
}

export function pickBoolean(value: unknown): boolean | undefined {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    if (normalized === 'true') return true;
    if (normalized === 'false') return false;
  }
  return undefined;
}

export function ensureArray<T>(value: unknown, map: (item: unknown, index: number) => T | null | undefined): T[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const result: T[] = [];
  value.forEach((item, index) => {
    const mapped = map(item, index);
    if (mapped !== null && mapped !== undefined) {
      result.push(mapped);
    }
  });
  return result;
}

export function normalizeSanction(raw: unknown, fallbackId?: string): ModerationSanctionRecord {
  const source = isObjectRecord(raw) ? raw : {};
  return {
    id: pickString(source.id) ?? fallbackId ?? `${pickString(source.type) ?? 'sanction'}-${pickString(source.issued_at) ?? Date.now()}`,
    type: pickString(source.type) ?? 'sanction',
    status: pickString(source.status) ?? 'active',
    reason: pickNullableString(source.reason) ?? null,
    issued_by: pickNullableString(source.issued_by) ?? null,
    issued_at: pickNullableString(source.issued_at) ?? null,
    starts_at: pickNullableString(source.starts_at) ?? null,
    ends_at: pickNullableString(source.ends_at) ?? null,
    revoked_at: pickNullableString(source.revoked_at) ?? null,
    revoked_by: pickNullableString(source.revoked_by) ?? null,
    target_type: pickNullableString(source.target_type) ?? null,
    target_id: pickNullableString(source.target_id) ?? null,
    moderator: pickNullableString(source.moderator) ?? pickNullableString(source.moderator_name) ?? pickNullableString(source.issued_by) ?? null,
    meta: isObjectRecord(source.meta) ? source.meta : {},
  };
}

export function normalizeNote(raw: unknown, index: number): ModerationNote {
  const source = isObjectRecord(raw) ? raw : {};
  return {
    id: pickString(source.id) ?? `note-${index}`,
    text: pickString(source.text) ?? '',
    author_id: pickNullableString(source.author_id) ?? null,
    author_name: pickNullableString(source.author_name) ?? null,
    created_at: pickNullableString(source.created_at) ?? null,
    pinned: pickBoolean(source.pinned) ?? false,
    meta: isObjectRecord(source.meta) ? source.meta : {},
  };
}

export function normalizeReport(raw: unknown, index: number): ModerationReport {
  const source = isObjectRecord(raw) ? raw : {};
  return {
    id: pickString(source.id) ?? `report-${index}`,
    object_type: pickString(source.object_type) ?? undefined,
    object_id: pickString(source.object_id) ?? undefined,
    reporter_id: pickString(source.reporter_id) ?? undefined,
    category: pickString(source.category) ?? undefined,
    text: pickNullableString(source.text) ?? null,
    status: pickString(source.status) ?? undefined,
    created_at: pickNullableString(source.created_at) ?? null,
    resolved_at: pickNullableString(source.resolved_at) ?? null,
    decision: pickNullableString(source.decision) ?? null,
    meta: isObjectRecord(source.meta) ? source.meta : {},
  };
}

export function normalizeTicket(raw: unknown, index: number): ModerationTicket {
  const source = isObjectRecord(raw) ? raw : {};
  return {
    id: pickString(source.id) ?? `ticket-${index}`,
    title: pickString(source.title) ?? undefined,
    priority: pickString(source.priority) ?? undefined,
    author_id: pickString(source.author_id) ?? undefined,
    assignee_id: pickNullableString(source.assignee_id) ?? null,
    status: pickString(source.status) ?? undefined,
    created_at: pickNullableString(source.created_at) ?? null,
    updated_at: pickNullableString(source.updated_at) ?? null,
    last_message_at: pickNullableString(source.last_message_at) ?? null,
    unread_count: pickNumber(source.unread_count),
    meta: isObjectRecord(source.meta) ? source.meta : {},
  };
}

export function normalizeCase(raw: unknown, index: number): ModerationCaseSummary {
  const source = isObjectRecord(raw) ? raw : {};
  return {
    id: pickString(source.id) ?? `case-${index}`,
    type: pickString(source.type) ?? undefined,
    status: pickString(source.status) ?? undefined,
    priority: pickString(source.priority) ?? undefined,
    opened_at: pickNullableString(source.opened_at) ?? null,
    meta: isObjectRecord(source.meta) ? source.meta : {},
  };
}

export function normalizeUserSummary(raw: unknown): ModerationUserSummary {
  const source = isObjectRecord(raw) ? raw : {};
  const rolesSource = source.roles ?? source.role ?? [];
  const roles = ensureArray(rolesSource, (item) => pickString(item)?.toLowerCase());
  const username = pickString(source.username) ?? pickString(source.email) ?? pickString(source.id) ?? 'Unknown user';

  const complaints = pickNumber(source.complaints_count) ?? pickNumber(source.complaintsCount) ?? 0;
  const notes = pickNumber(source.notes_count) ?? pickNumber(source.notesCount) ?? 0;
  const sanctions = pickNumber(source.sanction_count) ?? pickNumber(source.sanctionCount) ?? 0;

  return {
    id: pickString(source.id) ?? '',
    username,
    email: pickNullableString(source.email) ?? null,
    roles,
    status: pickString(source.status) ?? 'active',
    registered_at: pickNullableString(source.registered_at) ?? pickNullableString(source.registeredAt) ?? null,
    last_seen_at: pickNullableString(source.last_seen_at) ?? pickNullableString(source.lastSeenAt) ?? null,
    complaints_count: complaints,
    notes_count: notes,
    sanction_count: sanctions,
    active_sanctions: ensureArray(source.active_sanctions ?? source.activeSanctions, (item, index) => normalizeSanction(item, `active-sanction-${index}`)),
    last_sanction: source.last_sanction ? normalizeSanction(source.last_sanction) : null,
    meta: isObjectRecord(source.meta) ? source.meta : {},
  };
}

export function normalizeUserDetail(raw: unknown): ModerationUserDetail {
  const source = isObjectRecord(raw) ? raw : {};
  const summary = normalizeUserSummary(source);
  return {
    ...summary,
    sanctions: ensureArray(source.sanctions, (item, index) => normalizeSanction(item, `sanction-${index}`)),
    reports: ensureArray(source.reports, (item, index) => normalizeReport(item, index)),
    tickets: ensureArray(source.tickets, (item, index) => normalizeTicket(item, index)),
    notes: ensureArray(source.notes, (item, index) => normalizeNote(item, index)),
    cases: ensureArray(source.cases ?? source.open_cases ?? source.pending_cases, (item, index) => normalizeCase(item, index)),
  };
}

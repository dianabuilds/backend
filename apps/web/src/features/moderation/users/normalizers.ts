import type { ModerationRole, ModerationUserSummary } from './types';

const dateTimeFormatter = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

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
  if (Number.isNaN(dt.getTime())) return value;
  const formatted = dateTimeFormatter.format(dt);
  return formatted.replace(/\u202f/gu, ' ').replace(/\u00a0/gu, ' ');
}

export function formatRelativeTime(value?: string | null): string {
  if (!value) return 'N/A';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
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

export function statusToBadgeTone(status?: string | null): 'success' | 'error' | 'warning' | 'neutral' | 'info' {
  const normalized = (status || '').toLowerCase();
  if (['active', 'ok', 'approved'].includes(normalized)) return 'success';
  if (['banned', 'blocked', 'suspended'].includes(normalized)) return 'error';
  if (['pending', 'review', 'flagged'].includes(normalized)) return 'warning';
  if (normalized === 'escalated') return 'info';
  return 'neutral';
}
export function resolvePreferredRole(roles: string[]): ModerationRole {
  const normalized = roles.map((role) => role.toLowerCase()) as ModerationRole[];
  if (normalized.includes('admin')) return 'admin';
  if (normalized.includes('moderator')) return 'moderator';
  if (normalized.includes('support')) return 'support';
  return 'user';
}

export function resolveRiskLevel(user: ModerationUserSummary): 'low' | 'medium' | 'high' | 'unknown' {
  const meta = (user.meta ?? {}) as Record<string, unknown>;
  const directSource = meta['risk_label'] ?? meta['risk'] ?? meta['riskLevel'] ?? '';
  const direct = String(directSource).toLowerCase();
  if (direct === 'high' || direct === 'medium' || direct === 'low') return direct as 'high' | 'medium' | 'low';
  const numericSource = meta['risk_score'] ?? meta['riskScore'] ?? meta['score'];
  const numeric = typeof numericSource === 'number' ? numericSource : Number(numericSource);
  if (Number.isFinite(numeric)) {
    if (numeric >= 0.75) return 'high';
    if (numeric >= 0.4) return 'medium';
    return 'low';
  }
  if (user.sanction_count > 3 || user.complaints_count > 15) return 'high';
  if (user.sanction_count > 0 || user.complaints_count > 0) return 'medium';
  return 'low';
}

export function riskBadgeProps(level: ReturnType<typeof resolveRiskLevel>): { label: string; color: 'success' | 'error' | 'warning' | 'neutral' | 'info' } {
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

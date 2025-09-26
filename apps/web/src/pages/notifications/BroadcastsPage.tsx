import React from 'react';
import { Badge, Button, Drawer, Input, Pagination, Select, Spinner, Table, Textarea } from '@ui';
import { ContentLayout } from '../content/ContentLayout';
import { NotificationSurface, notificationTableHeadCellClass, notificationTableRowClass } from './NotificationSurface';
import { apiGet, apiPost, apiPut } from '../../shared/api/client';
import { useAuth } from '../../shared/auth';
import { extractErrorMessage } from '../../shared/utils/errors';

type AudienceType = 'all_users' | 'segment' | 'explicit_users';
type BroadcastStatus = 'draft' | 'scheduled' | 'sending' | 'sent' | 'failed' | 'cancelled';

type BroadcastAudience = {
  type: AudienceType;
  filters?: Record<string, unknown> | null;
  user_ids?: string[] | null;
};

type Broadcast = {
  id: string;
  title: string;
  body: string | null;
  template_id: string | null;
  audience: BroadcastAudience;
  status: BroadcastStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
  scheduled_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  total: number;
  sent: number;
  failed: number;
};

type BroadcastListResponse = {
  items?: Broadcast[];
  total?: number;
  offset?: number;
  limit?: number;
  has_next?: boolean;
  status_counts?: Record<string, number>;
  recipients?: number;
};

type TemplateSummary = {
  id: string;
  slug: string;
  name: string;
  description?: string | null;
  subject?: string | null;
  body: string;
  locale?: string | null;
};

const STATUS_THEME: Record<BroadcastStatus, string> = {
  draft: 'bg-slate-100 text-slate-700',
  scheduled: 'bg-indigo-50 text-indigo-700',
  sending: 'bg-sky-50 text-sky-700',
  sent: 'bg-emerald-50 text-emerald-700',
  failed: 'bg-rose-50 text-rose-700',
  cancelled: 'bg-amber-50 text-amber-700',
};

const STATUS_LABELS: Record<BroadcastStatus, string> = {
  draft: 'Draft',
  scheduled: 'Scheduled',
  sending: 'Sending',
  sent: 'Sent',
  failed: 'Failed',
  cancelled: 'Cancelled',
};

const STATUS_FILTER_OPTIONS: Array<{ value: 'all' | BroadcastStatus; label: string }> = [
  { value: 'all', label: 'All statuses' },
  { value: 'draft', label: STATUS_LABELS.draft },
  { value: 'scheduled', label: STATUS_LABELS.scheduled },
  { value: 'sending', label: STATUS_LABELS.sending },
  { value: 'sent', label: STATUS_LABELS.sent },
  { value: 'failed', label: STATUS_LABELS.failed },
  { value: 'cancelled', label: STATUS_LABELS.cancelled },
];

const PAGE_SIZE_OPTIONS = [10, 20, 50];
const EMPTY_STATUS_COUNTS: Record<BroadcastStatus, number> = {
  draft: 0,
  scheduled: 0,
  sending: 0,
  sent: 0,
  failed: 0,
  cancelled: 0,
};


const AUDIENCE_LABELS: Record<AudienceType, string> = {
  all_users: 'All users',
  segment: 'Segment',
  explicit_users: 'Explicit users',
};

const SEGMENT_FILTER_KEYS = [
  { key: 'role', label: 'Role' },
  { key: 'plan', label: 'Plan' },
  { key: 'locale', label: 'Locale' },
  { key: 'region', label: 'Region' },
];

function formatDateTime(value?: string | null): string {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value ?? '-';
  return date.toLocaleString();
}

function toInputDateValue(value: string | null): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (n: number) => n.toString().padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(
    date.getMinutes(),
  )}`;
}

function toIsoUtc(value: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

function createEmptySegmentFilters(): Record<string, string> {
  return { role: '', plan: '', locale: '', region: '' };
}

function previewBody(text: string | null | undefined, max = 80): string {
  if (!text) return '';
  const clean = text.replace(/\s+/g, ' ').trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, Math.max(0, max - 3))}...`;
}

export default function NotificationsBroadcastsPage(): React.ReactElement {
  const { user } = useAuth();
  const [broadcasts, setBroadcasts] = React.useState<Broadcast[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [saving, setSaving] = React.useState(false);
  const [editing, setEditing] = React.useState<Broadcast | null>(null);
  const [title, setTitle] = React.useState('');
  const [body, setBody] = React.useState('');
  const [templateId, setTemplateId] = React.useState('');
  const [audienceType, setAudienceType] = React.useState<AudienceType>('all_users');
  const [segmentFilters, setSegmentFilters] = React.useState<Record<string, string>>(() => createEmptySegmentFilters());
  const [segmentCustom, setSegmentCustom] = React.useState('');
  const [explicitIdsInput, setExplicitIdsInput] = React.useState('');
  const [scheduleMode, setScheduleMode] = React.useState<'none' | 'schedule'>('none');
  const [scheduledAtInput, setScheduledAtInput] = React.useState('');
  const [templates, setTemplates] = React.useState<TemplateSummary[]>([]);
  const [templatesLoading, setTemplatesLoading] = React.useState(false);
  const [rowBusy, setRowBusy] = React.useState<Record<string, 'send' | 'cancel'>>({});
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [hasNext, setHasNext] = React.useState(false);
  const [statusFilter, setStatusFilter] = React.useState<'all' | BroadcastStatus>('all');
  const [search, setSearch] = React.useState('');
  const [debouncedSearch, setDebouncedSearch] = React.useState('');
  const [statusCounts, setStatusCounts] = React.useState<Record<BroadcastStatus, number>>(() => ({
    ...EMPTY_STATUS_COUNTS,
  }));
  const [totalBroadcasts, setTotalBroadcasts] = React.useState(0);
  const [recipientTotal, setRecipientTotal] = React.useState(0);


  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    const offset = Math.max(0, (page - 1) * pageSize);
    const params = new URLSearchParams({
      limit: String(pageSize),
      offset: String(offset),
    });
    if (statusFilter !== 'all') {
      params.append('status', statusFilter);
    }
    if (debouncedSearch) {
      params.set('q', debouncedSearch);
    }
    try {
      const res = await apiGet<BroadcastListResponse>(`/v1/notifications/admin/broadcasts?${params.toString()}`);
      const rows = Array.isArray(res?.items) ? res.items : [];
      setBroadcasts(rows);
      const total = typeof res?.total === 'number' ? res.total : rows.length;
      setTotalBroadcasts(total);
      const computedHasNext = res?.has_next ?? offset + rows.length < total;
      setHasNext(Boolean(computedHasNext));
      const metaCounts = res?.status_counts ?? {};
      setStatusCounts({
        draft: metaCounts.draft ?? 0,
        scheduled: metaCounts.scheduled ?? 0,
        sending: metaCounts.sending ?? 0,
        sent: metaCounts.sent ?? 0,
        failed: metaCounts.failed ?? 0,
        cancelled: metaCounts.cancelled ?? 0,
      });
      const metaRecipients =
        typeof res?.recipients === 'number'
          ? res.recipients
          : rows.reduce((sum, item) => sum + (Number.isFinite(item.total) ? item.total : 0), 0);
      setRecipientTotal(metaRecipients);
    } catch (err) {
      setError(extractErrorMessage(err, 'Failed to load broadcasts'));
      setBroadcasts([]);
      setHasNext(false);
      setStatusCounts({ ...EMPTY_STATUS_COUNTS });
      setTotalBroadcasts(0);
      setRecipientTotal(0);
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, page, pageSize, statusFilter]);

  const loadTemplates = React.useCallback(async () => {
    setTemplatesLoading(true);
    try {
      const res = await apiGet<{ items?: TemplateSummary[] }>('/v1/notifications/admin/templates');
      setTemplates(Array.isArray(res?.items) ? res.items : []);
    } catch {
      setTemplates([]);
    } finally {
      setTemplatesLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadTemplates();
  }, [loadTemplates]);


  React.useEffect(() => {
    const handle = window.setTimeout(() => {
      setDebouncedSearch(search.trim());
    }, 300);
    return () => window.clearTimeout(handle);
  }, [search]);

  React.useEffect(() => {
    setPage((current) => (current === 1 ? current : 1));
  }, [debouncedSearch]);
  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  const templateMap = React.useMemo(() => new Map(templates.map((tpl) => [tpl.id, tpl])), [templates]);

  const summary = React.useMemo(() => ({
    totals: statusCounts,
    total: totalBroadcasts,
    recipients: recipientTotal,
  }), [recipientTotal, statusCounts, totalBroadcasts]);

  const openDrawer = React.useCallback((broadcast?: Broadcast | null) => {
    if (broadcast) {
      setEditing(broadcast);
      setTitle(broadcast.title);
      setBody(broadcast.body ?? '');
      setTemplateId(broadcast.template_id ?? '');
      const audience = broadcast.audience || { type: 'all_users' };
      setAudienceType(audience.type);
      if (audience.type === 'segment') {
        const filters = (audience.filters ?? {}) as Record<string, unknown>;
        const nextFilters = createEmptySegmentFilters();
        for (const key of Object.keys(nextFilters)) {
          const value = filters[key];
          nextFilters[key] = value == null ? '' : String(value);
        }
        const extras: Record<string, unknown> = {};
        Object.entries(filters).forEach(([key, value]) => {
          if (!(key in nextFilters)) {
            extras[key] = value;
          }
        });
        setSegmentFilters(nextFilters);
        setSegmentCustom(Object.keys(extras).length ? JSON.stringify(extras, null, 2) : '');
      } else {
        setSegmentFilters(createEmptySegmentFilters());
        setSegmentCustom('');
      }
      if (audience.type === 'explicit_users') {
        setExplicitIdsInput((audience.user_ids ?? []).join('\n'));
      } else {
        setExplicitIdsInput('');
      }
      if (broadcast.scheduled_at) {
        setScheduleMode('schedule');
        setScheduledAtInput(toInputDateValue(broadcast.scheduled_at));
      } else {
        setScheduleMode('none');
        setScheduledAtInput('');
      }
    } else {
      setEditing(null);
      setTitle('');
      setBody('');
      setTemplateId('');
      setAudienceType('all_users');
      setSegmentFilters(createEmptySegmentFilters());
      setSegmentCustom('');
      setExplicitIdsInput('');
      setScheduleMode('none');
      setScheduledAtInput('');
    }
    setFormError(null);
    setDrawerOpen(true);
  }, []);

  const closeDrawer = React.useCallback(() => {
    setDrawerOpen(false);
    setEditing(null);
  }, []);

  React.useEffect(() => {
    if (scheduleMode === 'none') {
      setScheduledAtInput('');
    }
  }, [scheduleMode]);

  const handleRefresh = React.useCallback(() => {
    void refresh();
  }, [refresh]);

  const handleSendNow = React.useCallback(
    async (broadcastId: string) => {
      setRowBusy((prev) => ({ ...prev, [broadcastId]: 'send' }));
      try {
        await apiPost(`/v1/notifications/admin/broadcasts/${broadcastId}/actions/send-now`, {});
        await refresh();
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to queue immediate send'));
      } finally {
        setRowBusy((prev) => {
          const next = { ...prev };
          delete next[broadcastId];
          return next;
        });
      }
    },
    [refresh],
  );

  const handleCancel = React.useCallback(
    async (broadcastId: string) => {
      const ok = window.confirm('Cancel this scheduled broadcast?');
      if (!ok) return;
      setRowBusy((prev) => ({ ...prev, [broadcastId]: 'cancel' }));
      try {
        await apiPost(`/v1/notifications/admin/broadcasts/${broadcastId}/actions/cancel`, {});
        await refresh();
      } catch (err) {
        setError(extractErrorMessage(err, 'Failed to cancel broadcast'));
      } finally {
        setRowBusy((prev) => {
          const next = { ...prev };
          delete next[broadcastId];
          return next;
        });
      }
    },
    [refresh],
  );

  const submit = React.useCallback(async () => {
    setFormError(null);
    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setFormError('Title is required.');
      return;
    }
    const hasBody = body.trim().length > 0;
    const hasTemplate = Boolean(templateId);
    if (!hasBody && !hasTemplate) {
      setFormError('Add message body or select a template.');
      return;
    }

    const audiencePayload: BroadcastAudience = { type: audienceType };
    if (audienceType === 'segment') {
      const filters: Record<string, unknown> = {};
      Object.entries(segmentFilters).forEach(([key, value]) => {
        const trimmed = value.trim();
        if (trimmed) filters[key] = trimmed;
      });
      if (segmentCustom.trim()) {
        try {
          const parsed = JSON.parse(segmentCustom);
          if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
            setFormError('Segment advanced filters must be a JSON object.');
            return;
          }
          Object.assign(filters, parsed as Record<string, unknown>);
        } catch {
          setFormError('Segment advanced filters must be valid JSON.');
          return;
        }
      }
      if (Object.keys(filters).length === 0) {
        setFormError('Add at least one segment filter.');
        return;
      }
      audiencePayload.filters = filters;
    } else if (audienceType === 'explicit_users') {
      const ids = explicitIdsInput
        .split(/[\s,;]+/)
        .map((value) => value.trim())
        .filter(Boolean);
      const unique = Array.from(new Set(ids));
      if (unique.length === 0) {
        setFormError('Provide at least one user ID.');
        return;
      }
      audiencePayload.user_ids = unique;
    }

    let scheduledAt: string | null = null;
    if (scheduleMode === 'schedule') {
      if (!scheduledAtInput.trim()) {
        setFormError('Pick a schedule date and time.');
        return;
      }
      const iso = toIsoUtc(scheduledAtInput);
      if (!iso) {
        setFormError('Schedule timestamp is invalid.');
        return;
      }
      scheduledAt = iso;
    }

    const payloadBase = {
      title: trimmedTitle,
      body: hasBody ? body : null,
      template_id: hasTemplate ? templateId : null,
      audience: audiencePayload,
      scheduled_at: scheduleMode === 'schedule' ? scheduledAt : null,
    };

    setSaving(true);
    try {
      if (editing) {
        await apiPut(`/v1/notifications/admin/broadcasts/${editing.id}`, payloadBase);
      } else {
        const createdBy = user?.id ?? 'admin';
        await apiPost('/v1/notifications/admin/broadcasts', {
          ...payloadBase,
          created_by: createdBy,
        });
      }
      setDrawerOpen(false);
      setEditing(null);
      await refresh();
    } catch (err) {
      const fallback = editing ? 'Failed to update broadcast' : 'Failed to create broadcast';
      setFormError(extractErrorMessage(err, fallback));
    } finally {
      setSaving(false);
    }
  }, [
    audienceType,
    body,
    editing,
    explicitIdsInput,
    refresh,
    scheduleMode,
    scheduledAtInput,
    segmentCustom,
    segmentFilters,
    templateId,
    title,
    user,
  ]);

  return (
    <ContentLayout
      context="notifications"
      title="Broadcasts"
      description="Plan announcements, hand off targeting to the platform, and keep delivery in sync with your operators."
    >
      <div className="space-y-6">
        <NotificationSurface className="p-6 space-y-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <div className="text-xs font-semibold uppercase tracking-widest text-primary-600">Notifications</div>
              <h1 className="text-2xl font-semibold text-gray-900">Broadcasts</h1>
              <p className="max-w-2xl text-sm text-gray-600">
                Coordinate product-wide announcements, target specific cohorts, and let orchestration handle the timing.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outlined" color="neutral" onClick={handleRefresh} disabled={loading}>
                Refresh
              </Button>
              <Button onClick={() => openDrawer(null)}>New broadcast</Button>
            </div>
          </div>

          {error && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
          )}
          <div className="flex flex-col gap-3 rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm md:flex-row md:items-end md:justify-between">
            <div className="flex flex-1 flex-wrap items-center gap-3">
              <Input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search broadcasts..."
                className="w-full min-w-[200px] max-w-sm"
                disabled={loading}
              />
              <Select
                value={statusFilter}
                onChange={(event) => {
                  setStatusFilter(event.target.value as 'all' | BroadcastStatus);
                  setPage(1);
                }}
                className="h-10 w-44 text-sm"
              >
                {STATUS_FILTER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
              <span>
                Showing {broadcasts.length} of {totalBroadcasts} broadcasts
                {debouncedSearch ? ` matching "${debouncedSearch}"` : ''}.
              </span>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
              <div className="text-xs uppercase tracking-wide text-gray-500">Total broadcasts</div>
              <div className="mt-2 text-2xl font-semibold text-gray-900">{summary.total}</div>
              <div className="text-xs text-gray-500">Recipients targeted (total): {summary.recipients}</div>
            </div>
            <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
              <div className="text-xs uppercase tracking-wide text-gray-500">Drafts</div>
              <div className="mt-2 text-2xl font-semibold text-gray-900">{summary.totals.draft}</div>
            </div>
            <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
              <div className="text-xs uppercase tracking-wide text-gray-500">Scheduled</div>
              <div className="mt-2 text-2xl font-semibold text-gray-900">{summary.totals.scheduled}</div>
            </div>
            <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
              <div className="text-xs uppercase tracking-wide text-gray-500">Sent</div>
              <div className="mt-2 text-2xl font-semibold text-gray-900">{summary.totals.sent}</div>
              <div className="text-xs text-gray-500">Failed : {summary.totals.failed}</div>
            </div>
          </div>

          <div className="hide-scrollbar overflow-x-auto">
            <Table.Table className="min-w-[1000px] text-left rtl:text-right">
              <Table.THead>
                <Table.TR>
                  <Table.TH className={`${notificationTableHeadCellClass} w-[32%]`}>Broadcast</Table.TH>
                  <Table.TH className={`${notificationTableHeadCellClass} w-[20%]`}>Audience</Table.TH>
                  <Table.TH className={`${notificationTableHeadCellClass} w-[16%]`}>Delivery</Table.TH>
                  <Table.TH className={`${notificationTableHeadCellClass} w-[20%]`}>Timeline</Table.TH>
                  <Table.TH className={`${notificationTableHeadCellClass} w-[12%] text-right`}>Actions</Table.TH>
                </Table.TR>
              </Table.THead>
              <Table.TBody>
                {loading && (
                  <Table.TR className={notificationTableRowClass}>
                    <Table.TD colSpan={5} className="px-6 py-10 text-center">
                      <div className="flex items-center justify-center gap-2 text-sm text-indigo-600">
                        <Spinner size="sm" />
                        <span>Loading broadcasts...</span>
                      </div>
                    </Table.TD>
                  </Table.TR>
                )}
                {!loading && broadcasts.length === 0 && (
                  <Table.TR className={notificationTableRowClass}>
                    <Table.TD colSpan={5} className="px-6 py-12 text-center text-sm text-gray-500">
                      No broadcasts yet. Create a draft to get started.
                    </Table.TD>
                  </Table.TR>
                )}
                {!loading &&
                  broadcasts.map((broadcast) => {
                    const statusClass = STATUS_THEME[broadcast.status] ?? STATUS_THEME.draft;
                    const tpl = broadcast.template_id ? templateMap.get(broadcast.template_id) : undefined;
                    const audienceValue = broadcast.audience?.type ?? 'all_users';
                    const audienceLabel = AUDIENCE_LABELS[audienceValue as AudienceType] ?? 'Audience';
                    const isMutable = broadcast.status === 'draft' || broadcast.status === 'scheduled';
                    const isScheduled = broadcast.status === 'scheduled';
                    const rowState = rowBusy[broadcast.id];

                    return (
                      <Table.TR key={broadcast.id} className={notificationTableRowClass}>
                        <Table.TD className="px-6 py-4 align-top">
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-sm font-semibold text-gray-900 dark:text-dark-50">
                                {broadcast.title}
                              </span>
                              <span
                                className={`inline-flex w-fit items-center rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${statusClass}`}
                              >
                                {broadcast.status}
                              </span>
                            </div>
                            {tpl ? (
                              <div className="text-xs text-gray-500 dark:text-dark-200">
                                Template: {tpl.name} ({tpl.slug})
                              </div>
                            ) : null}
                            {broadcast.body && (
                              <div className="text-xs text-gray-500 dark:text-dark-300">
                                Preview: {previewBody(broadcast.body)}
                              </div>
                            )}
                            <div className="text-xs text-gray-400">
                              Created {formatDateTime(broadcast.created_at)} by {broadcast.created_by}
                            </div>
                          </div>
                        </Table.TD>
                        <Table.TD className="px-6 py-4 align-top">
                          <div className="space-y-2 text-xs text-gray-600 dark:text-dark-200">
                            <Badge variant="soft" color="neutral">
                              {audienceLabel}
                            </Badge>
                            {broadcast.audience?.type === 'segment' && broadcast.audience?.filters ? (
                              <div className="rounded-lg bg-white/80 p-2 text-[11px] text-gray-500 shadow-inner">
                                {Object.entries(broadcast.audience.filters).map(([key, value]) => (
                                  <div key={key} className="truncate">
                                    {key}: {String(value)}
                                  </div>
                                ))}
                              </div>
                            ) : null}
                            {broadcast.audience?.type === 'explicit_users' && broadcast.audience?.user_ids ? (
                              <div className="text-[11px] text-gray-500">
                                {broadcast.audience.user_ids.length} recipient(s)
                              </div>
                            ) : null}
                          </div>
                        </Table.TD>
                        <Table.TD className="px-6 py-4 align-top">
                          <div className="text-sm text-gray-700 dark:text-dark-100">
                            Sent {broadcast.sent}/{broadcast.total}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-dark-300">Failed: {broadcast.failed}</div>
                        </Table.TD>
                        <Table.TD className="px-6 py-4 align-top">
                          <div className="text-xs text-gray-500 dark:text-dark-300">
                            Scheduled: {formatDateTime(broadcast.scheduled_at)}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-dark-300">
                            Started: {formatDateTime(broadcast.started_at)}
                          </div>
                          <div className="text-xs text-gray-500 dark:text-dark-300">
                            Finished: {formatDateTime(broadcast.finished_at)}
                          </div>
                        </Table.TD>
                        <Table.TD className="px-6 py-4 align-top text-right">
                          <div className="flex justify-end gap-2">
                            {isMutable && (
                              <Button size="sm" variant="ghost" onClick={() => openDrawer(broadcast)}>
                                Edit
                              </Button>
                            )}
                            {isMutable && (
                              <Button
                                size="sm"
                                variant="outlined"
                                onClick={() => handleSendNow(broadcast.id)}
                                disabled={rowState === 'send'}
                              >
                                {rowState === 'send' ? 'Sending...' : 'Send now'}
                              </Button>
                            )}
                            {isScheduled && (
                              <Button
                                size="sm"
                                variant="ghost"
                                color="neutral"
                                onClick={() => handleCancel(broadcast.id)}
                                disabled={rowState === 'cancel'}
                              >
                                {rowState === 'cancel' ? 'Cancelling...' : 'Cancel'}
                              </Button>
                            )}
                          </div>
                        </Table.TD>
                      </Table.TR>
                    );
                  })}
              </Table.TBody>
            </Table.Table>
          </div>

          <div className="flex flex-col gap-3 border-t border-white/50 pt-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2 text-sm text-indigo-600">
              <span>Rows per page</span>
              <Select
                value={String(pageSize)}
                onChange={(event) => {
                  setPageSize(Number(event.target.value));
                  setPage(1);
                }}
                className="h-9 w-24 text-xs"
              >
                {PAGE_SIZE_OPTIONS.map((size) => (
                  <option key={size} value={size}>
                    {size}
                  </option>
                ))}
              </Select>
            </div>
            <Pagination page={page} hasNext={hasNext} onChange={setPage} />
          </div>
        </NotificationSurface>

        <Drawer
          open={drawerOpen}
          onClose={closeDrawer}
          title={editing ? 'Edit broadcast' : 'New broadcast'}
          widthClass="w-full max-w-2xl"
          footer={
            <div className="flex justify-end gap-2">
              <Button variant="outlined" color="neutral" onClick={closeDrawer} disabled={saving}>
                Cancel
              </Button>
              <Button onClick={submit} disabled={saving}>
                {saving ? 'Saving...' : editing ? 'Update broadcast' : 'Create broadcast'}
              </Button>
            </div>
          }
        >
          <div className="space-y-5 p-6">
            {formError && (
              <div className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{formError}</div>
            )}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Title</label>
              <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Security bulletin" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Template</label>
              <Select value={templateId} onChange={(event) => setTemplateId(event.target.value)}>
                <option value="">No template</option>
                {templates.map((tpl) => (
                  <option key={tpl.id} value={tpl.id}>
                    {tpl.name} ({tpl.slug})
                  </option>
                ))}
              </Select>
              {templatesLoading && <div className="text-xs text-gray-500">Loading templates...</div>}
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Message body</label>
              <Textarea
                rows={6}
                value={body}
                onChange={(event) => setBody(event.target.value)}
                placeholder="What should people read?"
              />
              <p className="text-xs text-gray-500">
                Leave empty if your template already contains the full content.
              </p>
            </div>
            <div className="space-y-3">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Audience</label>
              <Select value={audienceType} onChange={(event) => setAudienceType(event.target.value as AudienceType)}>
                <option value="all_users">All users</option>
                <option value="segment">Segment</option>
                <option value="explicit_users">Explicit users</option>
              </Select>
              {audienceType === 'segment' && (
                <div className="space-y-3 rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
                  <div className="grid gap-3 sm:grid-cols-2">
                    {SEGMENT_FILTER_KEYS.map(({ key, label }) => (
                      <div key={key} className="space-y-1">
                        <label className="text-xs font-medium text-gray-500">{label}</label>
                        <Input
                          value={segmentFilters[key] ?? ''}
                          onChange={(event) =>
                            setSegmentFilters((prev) => ({
                              ...prev,
                              [key]: event.target.value,
                            }))
                          }
                          placeholder={label}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-gray-500">Advanced JSON (optional)</label>
                    <Textarea
                      rows={3}
                      value={segmentCustom}
                      onChange={(event) => setSegmentCustom(event.target.value)}
                      placeholder='{"region": "emea"}'
                    />
                    <p className="text-xs text-gray-500">
                      Use JSON to add filters beyond the quick fields above.
                    </p>
                  </div>
                </div>
              )}
              {audienceType === 'explicit_users' && (
                <div className="space-y-2">
                  <Textarea
                    rows={4}
                    value={explicitIdsInput}
                    onChange={(event) => setExplicitIdsInput(event.target.value)}
                    placeholder="user-123"
                  />
                  <p className="text-xs text-gray-500">One user ID per line, comma, or space.</p>
                </div>
              )}
            </div>
            <div className="space-y-2 border-t border-white/60 pt-4 dark:border-dark-600/50">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Scheduling</label>
              <div className="grid gap-3 sm:grid-cols-[180px_1fr]">
                <Select value={scheduleMode} onChange={(event) => setScheduleMode(event.target.value as 'none' | 'schedule')}>
                  <option value="none">Draft (no schedule)</option>
                  <option value="schedule">Schedule for later</option>
                </Select>
                {scheduleMode === 'schedule' && (
                  <div className="space-y-1">
                    <Input
                      type="datetime-local"
                      value={scheduledAtInput}
                      onChange={(event) => setScheduledAtInput(event.target.value)}
                    />
                    <p className="text-xs text-gray-500">Converted to UTC on save.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </Drawer>
      </div>
    </ContentLayout>
  );
}


















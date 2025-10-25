import React from 'react';
import {
  Badge,
  Button,
  Drawer,
  Input,
  Select,
  Spinner,
  Skeleton,
  Table,
  TablePagination,
  Textarea,
  useToast,
} from '@ui';
import { PageHero } from '@ui';
import type { PageHeroMetric } from '@ui/patterns/PageHero';
import { NotificationSurface, notificationTableHeadCellClass, notificationTableRowClass } from '../../common/NotificationSurface';
import {
  useNotificationBroadcastActions,
} from '../../common/hooks/useNotificationBroadcastActions';
import { useNotificationBroadcasts } from '../../common/hooks/useNotificationBroadcasts';
import { useNotificationsQuery } from '../../common/hooks/useNotificationsQuery';
import { fetchNotificationTemplates } from '@shared/api/notifications';
import { formatDateTime } from '@shared/utils/format';
import { useConfirmDialog } from '@shared/hooks/useConfirmDialog';
import { useAuth } from '@shared/auth';
import type {
  NotificationBroadcast,
  NotificationBroadcastAudience,
  NotificationBroadcastCreatePayload,
  NotificationBroadcastStatus,
  NotificationBroadcastUpdatePayload,
  NotificationTemplate,
} from '@shared/types/notifications';

const STATUS_FILTERS: Array<{ value: 'all' | NotificationBroadcastStatus; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'draft', label: 'Drafts' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'sending', label: 'Sending' },
  { value: 'sent', label: 'Sent' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
];

const STATUS_META: Record<NotificationBroadcastStatus, { label: string; color: 'neutral' | 'info' | 'success' | 'warning' | 'error' }> = {
  draft: { label: 'Draft', color: 'neutral' },
  scheduled: { label: 'Scheduled', color: 'warning' },
  sending: { label: 'Sending', color: 'info' },
  sent: { label: 'Sent', color: 'success' },
  failed: { label: 'Failed', color: 'error' },
  cancelled: { label: 'Cancelled', color: 'neutral' },
};

const AUDIENCE_LABELS: Record<NotificationBroadcastAudience['type'], string> = {
  all_users: 'All users',
  segment: 'Segment',
  explicit_users: 'Selected users',
};

const PAGE_SIZE_OPTIONS = [10, 20, 50];

const DEFAULT_FORM: BroadcastFormState = {
  title: '',
  templateId: '',
  body: '',
  audienceType: 'all_users',
  segmentFilters: '',
  explicitUserIds: '',
  scheduleEnabled: false,
  scheduledAt: '',
};

type BroadcastFormState = {
  title: string;
  templateId: string;
  body: string;
  audienceType: NotificationBroadcastAudience['type'];
  segmentFilters: string;
  explicitUserIds: string;
  scheduleEnabled: boolean;
  scheduledAt: string;
};

const DATE_INPUT_LENGTH = 16; // yyyy-MM-ddTHH:mm

function toDateTimeLocalInput(value: string | null): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const tzOffset = date.getTimezoneOffset();
  const localDate = new Date(date.getTime() - tzOffset * 60000);
  return localDate.toISOString().slice(0, DATE_INPUT_LENGTH);
}

function toIsoString(value: string): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

function formatStatus(status: NotificationBroadcastStatus): React.ReactNode {
  const meta = STATUS_META[status];
  return (
    <Badge color={meta.color} variant="soft" className="capitalize">
      {meta.label}
    </Badge>
  );
}

function formatAudience(audience: NotificationBroadcastAudience): string {
  const typeLabel = AUDIENCE_LABELS[audience.type] ?? audience.type;
  if (audience.type === 'segment') {
    const filters = audience.filters ? Object.keys(audience.filters).length : 0;
    return filters ? `${typeLabel} (${filters} filters)` : typeLabel;
  }
  if (audience.type === 'explicit_users') {
    const count = audience.user_ids?.length ?? 0;
    return count ? `${typeLabel} (${count})` : typeLabel;
  }
  return typeLabel;
}

function parseExplicitIds(value: string): string[] {
  return value
    .split(/[\n,;\s]+/)
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0);
}

function parseSegmentFilters(value: string): Record<string, unknown> | null {
  const trimmed = value.trim();
  if (!trimmed) return {};
  try {
    const parsed = JSON.parse(trimmed);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error('Segment filters must be an object.');
    }
    return parsed as Record<string, unknown>;
  } catch {
    throw new Error('Segment filters must be valid JSON.');
  }
}

function formatProgress(total: number, sent: number, failed: number): string {
  if (!total) return '—';
  const delivered = Math.max(0, Math.min(total, sent));
  if (failed) {
    return `${delivered}/${total} delivered (${failed} failed)`;
  }
  return `${delivered}/${total} delivered`;
}

type BroadcastHeroPayload = {
  actions?: React.ReactNode;
  metrics?: PageHeroMetric[];
};

type BroadcastFiltersProps = {
  statusFilter: 'all' | NotificationBroadcastStatus;
  statusOptions: Array<{ value: 'all' | NotificationBroadcastStatus; label: string; count: number }>;
  onStatusChange: (value: 'all' | NotificationBroadcastStatus) => void;
  searchQuery: string;
  onSearchChange: (value: string) => void;
  loadingCounts: boolean;
};

function BroadcastFilters({
  statusFilter,
  statusOptions,
  onStatusChange,
  searchQuery,
  onSearchChange,
  loadingCounts,
}: BroadcastFiltersProps): JSX.Element {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="custom-scrollbar -mx-1 flex w-full items-center gap-2 overflow-x-auto px-1 pb-1 lg:pb-0">
        {statusOptions.map(({ value, label, count }) => (
          <Button
            key={value}
            size="sm"
            variant={statusFilter === value ? 'filled' : 'ghost'}
            color={statusFilter === value ? 'primary' : 'neutral'}
            onClick={() => onStatusChange(value)}
            className="flex-shrink-0"
          >
            {label}
            <Badge color="neutral" variant="soft" className="ml-2">
              {loadingCounts ? '—' : count.toLocaleString('ru-RU')}
            </Badge>
          </Button>
        ))}
      </div>
      <Input
        value={searchQuery}
        onChange={(event) => onSearchChange(event.target.value)}
        placeholder="Search broadcasts"
        className="w-full max-w-full sm:max-w-xs lg:max-w-sm"
        data-testid="broadcasts-search"
      />
    </div>
  );
}

type NotificationsBroadcastsViewProps = {
  onHeroData?: (payload: BroadcastHeroPayload | null) => void;
};

export default function NotificationsBroadcastsView({
  onHeroData,
}: NotificationsBroadcastsViewProps): React.ReactElement {
  const { pushToast } = useToast();
  const { user } = useAuth();
  const { confirm, confirmationElement } = useConfirmDialog();

  const [statusFilter, setStatusFilter] = React.useState<'all' | NotificationBroadcastStatus>('all');
  const [searchQuery, setSearchQuery] = React.useState('');

  const {
    broadcasts,
    page,
    setPage,
    pageSize,
    setPageSize,
    hasNext,
    loading,
    error,
    setError,
    refresh,
    statusCounts,
    total,
    recipients,
  } = useNotificationBroadcasts({ status: statusFilter, search: searchQuery });

  const {
    saving,
    busy,
    error: actionError,
    createBroadcast,
    updateBroadcast,
    sendNow,
    cancel,
    clearError: clearActionError,
  } = useNotificationBroadcastActions();

  const { data: templates, loading: templatesLoading } = useNotificationsQuery<NotificationTemplate[]>({
    fetcher: (signal) => fetchNotificationTemplates({ signal }),
    auto: true,
  });

  const [drawerMode, setDrawerMode] = React.useState<'create' | 'edit' | null>(null);
  const [formState, setFormState] = React.useState<BroadcastFormState>(DEFAULT_FORM);
  const [formError, setFormError] = React.useState<string | null>(null);
  const [editingBroadcast, setEditingBroadcast] = React.useState<NotificationBroadcast | null>(null);

  const mergedError = actionError || error;
  const showSkeletonMetrics = loading && broadcasts.length === 0 && total === 0;

  const skeletonDraftValue = React.useMemo(() => <Skeleton className="h-5 w-16 rounded-md" />, []);
  const skeletonScheduledValue = React.useMemo(() => <Skeleton className="h-5 w-20 rounded-md" />, []);
  const skeletonRecipientsValue = React.useMemo(() => <Skeleton className="h-5 w-24 rounded-md" />, []);

  const handleDismissError = React.useCallback(() => {
    clearActionError();
    setError(null);
  }, [clearActionError, setError]);

  const openCreateDrawer = React.useCallback(() => {
    setDrawerMode('create');
    setEditingBroadcast(null);
    setFormState(DEFAULT_FORM);
    setFormError(null);
  }, []);

  const openEditDrawer = React.useCallback((broadcast: NotificationBroadcast) => {
    setEditingBroadcast(broadcast);
    setDrawerMode('edit');
    setFormError(null);
    setFormState({
      title: broadcast.title,
      templateId: broadcast.template_id ?? '',
      body: broadcast.body ?? '',
      audienceType: broadcast.audience?.type ?? 'all_users',
      segmentFilters: broadcast.audience?.type === 'segment' && broadcast.audience.filters
        ? JSON.stringify(broadcast.audience.filters, null, 2)
        : '',
      explicitUserIds: broadcast.audience?.type === 'explicit_users' && broadcast.audience.user_ids
        ? broadcast.audience.user_ids.join('\n')
        : '',
      scheduleEnabled: Boolean(broadcast.scheduled_at),
      scheduledAt: toDateTimeLocalInput(broadcast.scheduled_at),
    });
  }, []);

  const closeDrawer = React.useCallback(() => {
    setDrawerMode(null);
    setEditingBroadcast(null);
    setFormState(DEFAULT_FORM);
    setFormError(null);
  }, []);

  const handleSubmit = React.useCallback(async () => {
    if (!drawerMode) return;
    const title = formState.title.trim();
    if (!title) {
      setFormError('Title is required.');
      return;
    }

    if (formState.scheduleEnabled && !formState.scheduledAt) {
      setFormError('Set the scheduled date and time.');
      return;
    }

    let audience: NotificationBroadcastAudience | null = null;
    try {
      if (formState.audienceType === 'all_users') {
        audience = { type: 'all_users', filters: null, user_ids: null };
      } else if (formState.audienceType === 'segment') {
        audience = {
          type: 'segment',
          filters: parseSegmentFilters(formState.segmentFilters),
          user_ids: null,
        };
      } else {
        const ids = parseExplicitIds(formState.explicitUserIds);
        if (!ids.length) {
          throw new Error('Add at least one user id.');
        }
        audience = { type: 'explicit_users', user_ids: ids, filters: null };
      }
    } catch (err: any) {
      setFormError(err.message ?? 'Failed to build audience.');
      return;
    }

    const scheduledAtIso = formState.scheduleEnabled ? toIsoString(formState.scheduledAt) : null;
    if (formState.scheduleEnabled && !scheduledAtIso) {
      setFormError('Provide a valid schedule datetime.');
      return;
    }

    if (!audience) {
      setFormError('Failed to build audience.');
      return;
    }

    const audiencePayload: NotificationBroadcastUpdatePayload['audience'] = {
      type: audience.type,
      filters: audience.filters,
      user_ids: audience.user_ids,
    };

    const basePayload: NotificationBroadcastUpdatePayload = {
      title,
      body: formState.body.trim() ? formState.body.trim() : null,
      template_id: formState.templateId || null,
      audience: audiencePayload,
      scheduled_at: scheduledAtIso,
    };

    try {
      if (drawerMode === 'create') {
        const createdBy = user?.id ?? user?.username ?? 'system';
        const createPayload: NotificationBroadcastCreatePayload = {
          ...basePayload,
          created_by: createdBy,
        };
        await createBroadcast(createPayload, {
          onSuccess: () => {
            pushToast({ intent: 'success', description: 'Broadcast created.' });
            void refresh();
            closeDrawer();
          },
        });
      } else if (editingBroadcast) {
        await updateBroadcast(editingBroadcast.id, basePayload, {
          onSuccess: () => {
            pushToast({ intent: 'success', description: 'Broadcast updated.' });
            void refresh();
            closeDrawer();
          },
        });
      }
    } catch (err: unknown) {
      setFormError((err as Error)?.message ?? 'Failed to save broadcast.');
    }
  }, [createBroadcast, drawerMode, editingBroadcast, formState, pushToast, refresh, updateBroadcast, user?.id, user?.username, closeDrawer]);

  const handleSendNow = React.useCallback(
    async (broadcast: NotificationBroadcast) => {
      const approved = await confirm({
        title: 'Send broadcast now?',
        description: `Trigger immediate delivery for "${broadcast.title}"?`,
        confirmLabel: 'Send now',
        cancelLabel: 'Cancel',
      });
      if (!approved) return;
      await sendNow(broadcast.id, {
        onSuccess: () => {
          pushToast({ intent: 'success', description: 'Broadcast queued for delivery.' });
          void refresh();
        },
      });
    },
    [confirm, pushToast, refresh, sendNow],
  );

  const handleCancel = React.useCallback(
    async (broadcast: NotificationBroadcast) => {
      const approved = await confirm({
        title: 'Cancel broadcast?',
        description: `Cancel scheduled delivery for "${broadcast.title}"?`,
        confirmLabel: 'Cancel broadcast',
        cancelLabel: 'Keep',
        destructive: true,
      });
      if (!approved) return;
      await cancel(broadcast.id, {
        onSuccess: () => {
          pushToast({ intent: 'info', description: 'Broadcast cancelled.' });
          void refresh();
        },
      });
    },
    [cancel, confirm, pushToast, refresh],
  );

  const actionBusy = React.useMemo(() => busy, [busy]);

  const statusOptions = React.useMemo(
    () =>
      STATUS_FILTERS.map(({ value, label }) => ({
        value,
        label,
        count: value === 'all' ? total : statusCounts[value] ?? 0,
      })),
    [statusCounts, total],
  );

  const heroMetrics = React.useMemo<PageHeroMetric[]>(() => {
    if (showSkeletonMetrics) {
      return [
        { id: 'broadcasts-drafts', label: 'Drafts', value: skeletonDraftValue },
        { id: 'broadcasts-scheduled', label: 'Scheduled', value: skeletonScheduledValue },
        { id: 'broadcasts-recipients', label: 'Recipients queued', value: skeletonRecipientsValue },
      ];
    }
    const drafts = statusCounts.draft ?? 0;
    const scheduled = statusCounts.scheduled ?? 0;
    return [
      { id: 'broadcasts-drafts', label: 'Drafts', value: drafts.toLocaleString('ru-RU') },
      { id: 'broadcasts-scheduled', label: 'Scheduled', value: scheduled.toLocaleString('ru-RU') },
      { id: 'broadcasts-recipients', label: 'Recipients queued', value: recipients.toLocaleString('ru-RU') || '—' },
    ];
  }, [
    recipients,
    showSkeletonMetrics,
    skeletonDraftValue,
    skeletonRecipientsValue,
    skeletonScheduledValue,
    statusCounts.draft,
    statusCounts.scheduled,
  ]);

  const heroActions = React.useMemo(
    () => (
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="outlined" size="sm" onClick={() => void refresh()} disabled={loading || saving}>
          Refresh
        </Button>
        <Button size="sm" color="primary" onClick={openCreateDrawer} disabled={saving}>
          New broadcast
        </Button>
      </div>
    ),
    [loading, openCreateDrawer, refresh, saving],
  );

  const handleStatusChange = React.useCallback(
    (value: 'all' | NotificationBroadcastStatus) => {
      setStatusFilter(value);
      setPage(1);
    },
    [setPage],
  );

  const handleSearchChange = React.useCallback(
    (value: string) => {
      setSearchQuery(value);
      setPage(1);
    },
    [setPage],
  );

  const heroPayload = React.useMemo<BroadcastHeroPayload>(
    () => ({
      actions: heroActions,
      metrics: heroMetrics,
    }),
    [heroActions, heroMetrics],
  );

  React.useEffect(() => {
    if (!onHeroData) return;
    onHeroData(heroPayload);
  }, [heroPayload, onHeroData]);

  React.useEffect(
    () => () => {
      if (onHeroData) {
        onHeroData(null);
      }
    },
    [onHeroData],
  );

  const renderLocalHero = !onHeroData;

  return (
    <div className="space-y-6" data-testid="notifications-broadcasts-view">
      {renderLocalHero ? (
        <PageHero
          title="Broadcasts"
          description="Plan announcements, hand off targeting to the platform, and keep delivery in sync with operators."
          eyebrow="Notifications"
          metrics={heroMetrics}
          actions={heroActions}
          variant="compact"
          tone="light"
        />
      ) : null}

      <NotificationSurface className="space-y-5 p-4 sm:p-6">
        <div className="rounded-3xl border border-white/60 bg-white/95 p-4 shadow-sm dark:border-dark-600/60 dark:bg-dark-700/70">
          <BroadcastFilters
            statusFilter={statusFilter}
            statusOptions={statusOptions}
            onStatusChange={handleStatusChange}
            searchQuery={searchQuery}
            onSearchChange={handleSearchChange}
            loadingCounts={showSkeletonMetrics}
          />
        </div>

        {mergedError ? (
          <div className="rounded-xl border border-rose-200/70 bg-rose-50/80 px-4 py-3 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100">
            <div className="flex items-center justify-between gap-4">
              <span>{mergedError}</span>
              <Button size="sm" variant="ghost" onClick={handleDismissError}>
                Dismiss
              </Button>
            </div>
          </div>
        ) : null}

        <div className="hidden overflow-hidden rounded-3xl border border-white/50 bg-white/80 dark:border-dark-600/60 dark:bg-dark-700/60 sm:block">
          <Table.Table className="min-w-[760px] text-left text-sm">
            <Table.THead>
              <Table.TR>
                <Table.TH className={`${notificationTableHeadCellClass} w-[26%]`}>Broadcast</Table.TH>
                <Table.TH className={`${notificationTableHeadCellClass} w-[22%]`}>Audience</Table.TH>
                <Table.TH className={`${notificationTableHeadCellClass} w-[12%] text-center`}>Status</Table.TH>
                <Table.TH className={`${notificationTableHeadCellClass} w-[18%]`}>Schedule</Table.TH>
                <Table.TH className={`${notificationTableHeadCellClass} w-[14%] text-center`}>Progress</Table.TH>
                <Table.TH className={`${notificationTableHeadCellClass} w-[8%] text-right`}>Actions</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {loading && !broadcasts.length ? (
                <Table.TR>
                  <Table.TD colSpan={6} className="py-10 text-center text-sm text-gray-500">
                    <Spinner />
                  </Table.TD>
                </Table.TR>
              ) : broadcasts.length ? (
                broadcasts.map((broadcast) => {
                  const progress = formatProgress(broadcast.total, broadcast.sent, broadcast.failed);
                  const canSendNow = broadcast.status === 'draft' || broadcast.status === 'scheduled';
                  const canCancel = broadcast.status === 'scheduled' || broadcast.status === 'sending';
                  const busyState = actionBusy[broadcast.id];
                  return (
                    <Table.TR key={broadcast.id} className={notificationTableRowClass}>
                      <Table.TD className="px-5 py-4 align-top">
                        <div className="space-y-1">
                          <div className="font-semibold text-gray-900 dark:text-white">{broadcast.title}</div>
                          {broadcast.template_id ? (
                            <div className="text-xs text-gray-500 dark:text-dark-200">Template: {broadcast.template_id}</div>
                          ) : null}
                          {broadcast.body ? (
                            <div className="text-xs text-gray-500 dark:text-dark-200 line-clamp-2">{broadcast.body}</div>
                          ) : null}
                        </div>
                      </Table.TD>
                      <Table.TD className="px-5 py-4 align-top">
                        <div className="text-sm text-gray-700 dark:text-dark-100">{formatAudience(broadcast.audience)}</div>
                        <div className="mt-1 text-xs text-gray-500 dark:text-dark-300">Created by {broadcast.created_by ?? 'system'}</div>
                      </Table.TD>
                      <Table.TD className="px-5 py-4 text-center align-top">{formatStatus(broadcast.status)}</Table.TD>
                      <Table.TD className="px-5 py-4 align-top text-sm text-gray-600 dark:text-dark-200">
                        <div>Created: {formatDateTime(broadcast.created_at, { withSeconds: true, fallback: '—' })}</div>
                        <div>Updated: {formatDateTime(broadcast.updated_at, { withSeconds: true, fallback: '—' })}</div>
                        <div>Scheduled: {formatDateTime(broadcast.scheduled_at ?? undefined, { withSeconds: true, fallback: '—' })}</div>
                      </Table.TD>
                      <Table.TD className="px-5 py-4 text-center align-top text-sm text-gray-700 dark:text-dark-100">
                        {progress}
                      </Table.TD>
                      <Table.TD className="px-5 py-4 align-top">
                        <div className="flex justify-end gap-2">
                          <Button size="sm" variant="ghost" onClick={() => openEditDrawer(broadcast)}>
                            Edit
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            color="primary"
                            onClick={() => void handleSendNow(broadcast)}
                            disabled={!canSendNow || Boolean(busyState) || saving}
                          >
                            {busyState === 'send' ? <Spinner size="sm" /> : 'Send now'}
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            color="error"
                            onClick={() => void handleCancel(broadcast)}
                            disabled={!canCancel || Boolean(busyState) || saving}
                          >
                            {busyState === 'cancel' ? <Spinner size="sm" /> : 'Cancel'}
                          </Button>
                        </div>
                      </Table.TD>
                    </Table.TR>
                  );
                })
              ) : (
                <Table.TR>
                  <Table.TD colSpan={6} className="py-10 text-center text-sm text-gray-500 dark:text-dark-200">
                    No broadcasts yet.
                  </Table.TD>
                </Table.TR>
              )}
            </Table.TBody>
          </Table.Table>
        </div>

        <div className="space-y-3 sm:hidden">
          {loading && !broadcasts.length ? (
            <div className="flex justify-center py-10">
              <Spinner />
            </div>
          ) : broadcasts.length ? (
            broadcasts.map((broadcast) => {
              const progress = formatProgress(broadcast.total, broadcast.sent, broadcast.failed);
              const canSendNow = broadcast.status === 'draft' || broadcast.status === 'scheduled';
              const canCancel = broadcast.status === 'scheduled' || broadcast.status === 'sending';
              const busyState = actionBusy[broadcast.id];
              return (
                <div
                  key={`${broadcast.id}-mobile`}
                  className="rounded-2xl border border-white/60 bg-white/95 p-4 shadow-sm dark:border-dark-600/60 dark:bg-dark-700/70"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-2">
                      <div className="text-sm font-semibold text-gray-900 dark:text-white">{broadcast.title}</div>
                      {broadcast.body ? (
                        <div className="text-xs text-gray-500 dark:text-dark-200 line-clamp-3">{broadcast.body}</div>
                      ) : null}
                      <div className="space-y-1 text-[11px] uppercase tracking-wide text-gray-400 dark:text-dark-300">
                        <div>Created: {formatDateTime(broadcast.created_at, { withSeconds: true, fallback: '—' })}</div>
                        <div>Updated: {formatDateTime(broadcast.updated_at, { withSeconds: true, fallback: '—' })}</div>
                        <div>Scheduled: {formatDateTime(broadcast.scheduled_at ?? undefined, { withSeconds: true, fallback: '—' })}</div>
                      </div>
                    </div>
                    <div className="shrink-0">{formatStatus(broadcast.status)}</div>
                  </div>
                  <div className="mt-3 space-y-2 text-xs text-gray-600 dark:text-dark-200">
                    <div className="flex items-start justify-between gap-2">
                      <span className="font-medium text-gray-700 dark:text-dark-100">Audience</span>
                      <span className="text-right text-gray-600 dark:text-dark-100">{formatAudience(broadcast.audience)}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-dark-100">
                      <span>Progress</span>
                      <span>{progress}</span>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap items-center justify-end gap-2">
                    <Button size="sm" variant="ghost" onClick={() => openEditDrawer(broadcast)}>
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      color="primary"
                      onClick={() => void handleSendNow(broadcast)}
                      disabled={!canSendNow || Boolean(busyState) || saving}
                    >
                      {busyState === 'send' ? <Spinner size="sm" /> : 'Send now'}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      color="error"
                      onClick={() => void handleCancel(broadcast)}
                      disabled={!canCancel || Boolean(busyState) || saving}
                    >
                      {busyState === 'cancel' ? <Spinner size="sm" /> : 'Cancel'}
                    </Button>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-300 bg-white/70 px-4 py-6 text-center text-sm text-gray-500 dark:border-dark-500 dark:bg-dark-700/40 dark:text-dark-200">
              No broadcasts yet.
            </div>
          )}
        </div>

        <div className="px-1 pb-1 pt-1 sm:px-3 sm:pt-3">
          <TablePagination
            page={page}
            pageSize={pageSize}
            currentCount={broadcasts.length}
            totalItems={total}
            hasNext={hasNext}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
            pageSizeOptions={PAGE_SIZE_OPTIONS}
          />
        </div>
      </NotificationSurface>

      <Drawer
        open={Boolean(drawerMode)}
        onClose={closeDrawer}
        title={drawerMode === 'edit' ? 'Edit broadcast' : 'Create broadcast'}
        widthClass="w-[720px]"
        footer={(
          <div className="flex items-center justify-between gap-2">
            {formError ? <span className="text-sm text-rose-500">{formError}</span> : <span />}
            <div className="flex items-center gap-2">
              <Button variant="ghost" onClick={closeDrawer} disabled={saving}>
                Cancel
              </Button>
              <Button onClick={() => void handleSubmit()} disabled={saving}>
                {saving ? <Spinner size="sm" /> : drawerMode === 'edit' ? 'Save changes' : 'Create broadcast'}
              </Button>
            </div>
          </div>
        )}
      >
        <div className="space-y-4 px-4 py-5">
          <Input
            label="Title"
            value={formState.title}
            onChange={(event) => setFormState((prev) => ({ ...prev, title: event.target.value }))}
            placeholder="Weekly update"
          />

          <Select
            label="Template"
            value={formState.templateId}
            onChange={(event) => setFormState((prev) => ({ ...prev, templateId: event.target.value }))}
          >
            <option value="">— Without template —</option>
            {(templates ?? []).map((template) => (
              <option key={template.id} value={template.id}>
                {template.name} ({template.slug})
              </option>
            ))}
          </Select>
          {templatesLoading ? <div className="text-xs text-gray-500">Loading templates…</div> : null}

          <Textarea
            label="Body"
            rows={5}
            value={formState.body}
            onChange={(event) => setFormState((prev) => ({ ...prev, body: event.target.value }))}
            placeholder="Optional message body"
          />

          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Audience</label>
            <Select
              value={formState.audienceType}
              onChange={(event) =>
                setFormState((prev) => ({ ...prev, audienceType: event.target.value as NotificationBroadcastAudience['type'] }))
              }
            >
              <option value="all_users">All users</option>
              <option value="segment">Segment filters</option>
              <option value="explicit_users">Explicit user ids</option>
            </Select>
            {formState.audienceType === 'segment' ? (
              <Textarea
                rows={6}
                value={formState.segmentFilters}
                onChange={(event) => setFormState((prev) => ({ ...prev, segmentFilters: event.target.value }))}
                placeholder='{"plan": "pro", "region": "emea"}'
              />
            ) : null}
            {formState.audienceType === 'explicit_users' ? (
              <Textarea
                rows={4}
                value={formState.explicitUserIds}
                onChange={(event) => setFormState((prev) => ({ ...prev, explicitUserIds: event.target.value }))}
                placeholder={'user-123\nuser-456'}
              />
            ) : null}
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">Schedule</label>
            <div className="flex items-center gap-3">
              <Button
                size="sm"
                variant={formState.scheduleEnabled ? 'ghost' : 'filled'}
                color={formState.scheduleEnabled ? 'neutral' : 'primary'}
                onClick={() =>
                  setFormState((prev) => ({
                    ...prev,
                    scheduleEnabled: false,
                    scheduledAt: '',
                  }))
                }
              >
                Send immediately
              </Button>
              <Button
                size="sm"
                variant={formState.scheduleEnabled ? 'filled' : 'ghost'}
                color={formState.scheduleEnabled ? 'primary' : 'neutral'}
                onClick={() => setFormState((prev) => ({ ...prev, scheduleEnabled: true }))}
              >
                Schedule later
              </Button>
            </div>
            {formState.scheduleEnabled ? (
              <Input
                type="datetime-local"
                value={formState.scheduledAt}
                onChange={(event) => setFormState((prev) => ({ ...prev, scheduledAt: event.target.value }))}
              />
            ) : null}
          </div>
        </div>
      </Drawer>
      {confirmationElement}
    </div>
  );
}

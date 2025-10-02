import React from 'react';
import { Badge, Button, Drawer, Input, Pagination, Select, Spinner, Table, Textarea, useToast } from '@ui';
import { ContentLayout } from '../content/ContentLayout';
import { NotificationSurface, notificationTableHeadCellClass, notificationTableRowClass } from './NotificationSurface';
import { apiGet, apiPost, apiPut } from '../../shared/api/client';
import { useAuth } from '../../shared/auth';
import { extractErrorMessage } from '../../shared/utils/errors';
import { translate, translateWithVars } from '../../shared/i18n/locale';
import type { Locale } from '../../shared/i18n/locale';
import { usePaginatedQuery } from '../../shared/hooks/usePaginatedQuery';
import { useConfirmDialog } from '../../shared/hooks/useConfirmDialog';

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

type BroadcastListResult = {
  response: BroadcastListResponse | null;
  items: Broadcast[];
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

const STATUS_LABELS: Record<BroadcastStatus, Record<Locale, string>> = {
  draft: { en: 'Draft', ru: 'Черновик' },
  scheduled: { en: 'Scheduled', ru: 'Запланировано' },
  sending: { en: 'Sending', ru: 'Отправляется' },
  sent: { en: 'Sent', ru: 'Отправлено' },
  failed: { en: 'Failed', ru: 'Ошибки' },
  cancelled: { en: 'Cancelled', ru: 'Отменено' },
};

const STATUS_FILTER_LABELS: Record<'all' | BroadcastStatus, Record<Locale, string>> = {
  all: { en: 'All statuses', ru: 'Все статусы' },
  draft: { en: 'Drafts', ru: 'Черновики' },
  scheduled: { en: 'Scheduled', ru: 'Запланировано' },
  sending: { en: 'Sending', ru: 'Отправляются' },
  sent: { en: 'Sent', ru: 'Отправлено' },
  failed: { en: 'Failed', ru: 'Ошибки' },
  cancelled: { en: 'Cancelled', ru: 'Отменено' },
};

const STATUS_FILTER_ORDER: Array<'all' | BroadcastStatus> = ['all', 'draft', 'scheduled', 'sending', 'sent', 'failed', 'cancelled'];

const PAGE_SIZE_OPTIONS = [10, 20, 50];
const EMPTY_STATUS_COUNTS: Record<BroadcastStatus, number> = {
  draft: 0,
  scheduled: 0,
  sending: 0,
  sent: 0,
  failed: 0,
  cancelled: 0,
};

const AUDIENCE_LABELS: Record<AudienceType, Record<Locale, string>> = {
  all_users: { en: 'All users', ru: 'Все пользователи' },
  segment: { en: 'Segment', ru: 'Сегмент' },
  explicit_users: { en: 'Explicit users', ru: 'Выбранные пользователи' },
};

const SEGMENT_FILTER_KEYS: Array<{ key: string; label: Record<Locale, string> }> = [
  { key: 'role', label: { en: 'Role', ru: 'Роль' } },
  { key: 'plan', label: { en: 'Plan', ru: 'Тариф' } },
  { key: 'locale', label: { en: 'Locale', ru: 'Язык' } },
  { key: 'region', label: { en: 'Region', ru: 'Регион' } },
];

const BROADCAST_COPY = {
  layout: {
    contextLabel: { en: 'Notifications', ru: 'Уведомления' },
    title: { en: 'Broadcasts', ru: 'Рассылки' },
    description: {
      en: 'Plan announcements, hand off targeting to the platform, and keep delivery in sync with your operators.',
      ru: 'Планируйте объявления, передавайте таргетинг платформе и поддерживайте синхронизацию доставки с операторами.',
    },
    refresh: { en: 'Refresh', ru: 'Обновить' },
    create: { en: 'New broadcast', ru: 'Новая рассылка' },
  },
  filters: {
    searchPlaceholder: { en: 'Search broadcasts…', ru: 'Поиск рассылок…' },
    showing: { en: 'Showing {{current}} of {{total}} broadcasts', ru: 'Показано {{current}} из {{total}} рассылок' },
    matching: { en: 'matching “{{query}}”', ru: 'по запросу «{{query}}»' },
    rowsPerPage: { en: 'Rows per page', ru: 'Строк на странице' },
  },
  summary: {
    total: { en: 'Total broadcasts', ru: 'Всего рассылок' },
    recipients: { en: 'Recipients targeted (total): {{count}}', ru: 'Получателей всего: {{count}}' },
    drafts: { en: 'Drafts', ru: 'Черновики' },
    scheduled: { en: 'Scheduled', ru: 'Запланировано' },
    sent: { en: 'Sent', ru: 'Отправлено' },
    failed: { en: 'Failed: {{count}}', ru: 'Ошибки: {{count}}' },
  },
  table: {
    header: {
      broadcast: { en: 'Broadcast', ru: 'Рассылка' },
      audience: { en: 'Audience', ru: 'Аудитория' },
      delivery: { en: 'Delivery', ru: 'Доставка' },
      timeline: { en: 'Timeline', ru: 'Сроки' },
      actions: { en: 'Actions', ru: 'Действия' },
    },
    loading: { en: 'Loading broadcasts…', ru: 'Загрузка рассылок…' },
    empty: { en: 'No broadcasts yet. Create a draft to get started.', ru: 'Пока нет рассылок. Создайте черновик, чтобы начать.' },
    templatePrefix: { en: 'Template:', ru: 'Шаблон:' },
    previewPrefix: { en: 'Preview:', ru: 'Предпросмотр:' },
    createdBy: { en: 'Created {{date}} by {{author}}', ru: 'Создано {{date}} автором {{author}}' },
    recipients: { en: '{{count}} recipient(s)', ru: '{{count}} получателей' },
    sentRatio: { en: 'Sent {{sent}}/{{total}}', ru: 'Отправлено {{sent}}/{{total}}' },
    failed: { en: 'Failed: {{count}}', ru: 'Ошибки: {{count}}' },
    scheduled: { en: 'Scheduled: {{value}}', ru: 'Запланировано: {{value}}' },
    started: { en: 'Started: {{value}}', ru: 'Начато: {{value}}' },
    finished: { en: 'Finished: {{value}}', ru: 'Завершено: {{value}}' },
    edit: { en: 'Edit', ru: 'Редактировать' },
    sendNow: { en: 'Send now', ru: 'Отправить сейчас' },
    sending: { en: 'Sending…', ru: 'Отправка…' },
    cancel: { en: 'Cancel', ru: 'Отменить' },
    cancelling: { en: 'Cancelling…', ru: 'Отмена…' },
  },
  drawer: {
    newTitle: { en: 'New broadcast', ru: 'Новая рассылка' },
    editTitle: { en: 'Edit broadcast', ru: 'Редактировать рассылку' },
    cancel: { en: 'Cancel', ru: 'Отмена' },
    saving: { en: 'Saving…', ru: 'Сохранение…' },
    create: { en: 'Create broadcast', ru: 'Создать рассылку' },
    update: { en: 'Update broadcast', ru: 'Обновить рассылку' },
    titleLabel: { en: 'Title', ru: 'Заголовок' },
    titlePlaceholder: { en: 'Security bulletin', ru: 'Информационный бюллетень' },
    templateLabel: { en: 'Template', ru: 'Шаблон' },
    templateEmpty: { en: 'No template', ru: 'Без шаблона' },
    templateLoading: { en: 'Loading templates…', ru: 'Загрузка шаблонов…' },
    bodyLabel: { en: 'Message body', ru: 'Текст сообщения' },
    bodyPlaceholder: { en: 'What should people read?', ru: 'Что нужно сообщить пользователям?' },
    bodyHint: {
      en: 'Leave empty if your template already contains the full content.',
      ru: 'Оставьте пустым, если шаблон уже содержит весь текст.',
    },
    audienceLabel: { en: 'Audience', ru: 'Аудитория' },
    segmentAdvancedLabel: { en: 'Advanced JSON (optional)', ru: 'Дополнительный JSON (необязательно)' },
    segmentAdvancedHint: {
      en: 'Use JSON to add filters beyond the quick fields above.',
      ru: 'Используйте JSON, чтобы добавить фильтры помимо полей выше.',
    },
    explicitHint: { en: 'One user ID per line, comma, or space.', ru: 'Один ID пользователя в строке, через запятую или пробел.' },
    schedulingLabel: { en: 'Scheduling', ru: 'Расписание' },
    schedulingNone: { en: 'Draft (no schedule)', ru: 'Черновик (без расписания)' },
    schedulingLater: { en: 'Schedule for later', ru: 'Запланировать на потом' },
    schedulingHint: { en: 'Converted to UTC on save.', ru: 'При сохранении переводится в UTC.' },
  },
  messages: {
    loadError: { en: 'Failed to load broadcasts', ru: 'Не удалось загрузить рассылки' },
    templatesLoadError: { en: 'Failed to load templates', ru: 'Не удалось загрузить шаблоны' },
    sendNowError: { en: 'Failed to queue immediate send', ru: 'Не удалось поставить рассылку на немедленную отправку' },
    cancelError: { en: 'Failed to cancel broadcast', ru: 'Не удалось отменить рассылку' },
    createError: { en: 'Failed to create broadcast', ru: 'Не удалось создать рассылку' },
    updateError: { en: 'Failed to update broadcast', ru: 'Не удалось обновить рассылку' },
    validation: {
      titleRequired: { en: 'Title is required.', ru: 'Укажите заголовок.' },
      bodyOrTemplate: { en: 'Add message body or select a template.', ru: 'Добавьте текст или выберите шаблон.' },
      segmentObject: { en: 'Segment advanced filters must be a JSON object.', ru: 'Дополнительные фильтры сегмента должны быть JSON-объектом.' },
      segmentJson: { en: 'Segment advanced filters must be valid JSON.', ru: 'Дополнительные фильтры сегмента должны быть корректным JSON.' },
      segmentEmpty: { en: 'Add at least one segment filter.', ru: 'Добавьте хотя бы один фильтр сегмента.' },
      explicitEmpty: { en: 'Provide at least one user ID.', ru: 'Укажите хотя бы один ID пользователя.' },
      scheduleRequired: { en: 'Pick a schedule date and time.', ru: 'Выберите дату и время отправки.' },
      scheduleInvalid: { en: 'Schedule timestamp is invalid.', ru: 'Недействительное время отправки.' },
    },
  },
  confirm: {
    cancel: {
      title: { en: 'Cancel broadcast', ru: 'Отменить рассылку' },
      description: { en: 'Cancel this scheduled broadcast?', ru: 'Отменить эту запланированную рассылку?' },
      confirm: { en: 'Cancel broadcast', ru: 'Отменить рассылку' },
      dismiss: { en: 'Keep scheduled', ru: 'Оставить в расписании' },
    },
  },
  toasts: {
    sendQueued: { en: 'Immediate send queued.', ru: 'Мгновенная отправка поставлена в очередь.' },
    cancelSuccess: { en: 'Broadcast cancelled.', ru: 'Рассылка отменена.' },
    createSuccess: { en: 'Broadcast created.', ru: 'Рассылка создана.' },
    updateSuccess: { en: 'Broadcast updated.', ru: 'Рассылка обновлена.' },
  },
};
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
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
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
  const { pushToast } = useToast();
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
  const { confirm, confirmationElement } = useConfirmDialog();
  const [statusFilter, setStatusFilter] = React.useState<'all' | BroadcastStatus>('all');
  const [search, setSearch] = React.useState('');
  const normalizedSearch = React.useMemo(() => search.trim(), [search]);
  const [statusCounts, setStatusCounts] = React.useState<Record<BroadcastStatus, number>>(() => ({
    ...EMPTY_STATUS_COUNTS,
  }));
  const [totalBroadcasts, setTotalBroadcasts] = React.useState(0);
  const [recipientTotal, setRecipientTotal] = React.useState(0);

  const {
    items: broadcasts,
    page,
    setPage,
    pageSize,
    setPageSize,
    hasNext,
    loading,
    error,
    setError,
    refresh,
  } = usePaginatedQuery<Broadcast, BroadcastListResult>({
    initialPageSize: 20,
    dependencies: [statusFilter, normalizedSearch],
    debounceMs: 300,
    fetcher: async ({ page: currentPage, pageSize: currentPageSize, signal }) => {
      const params = new URLSearchParams({
        limit: String(currentPageSize),
        offset: String(Math.max(0, (currentPage - 1) * currentPageSize)),
      });
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      if (normalizedSearch) {
        params.set('q', normalizedSearch);
      }
      const response = await apiGet<BroadcastListResponse>(`/v1/notifications/admin/broadcasts?${params.toString()}`, { signal });
      const rows = Array.isArray(response?.items) ? response.items : [];
      return { response: response ?? null, items: rows };
    },
    mapResponse: (result, { page: currentPage, pageSize: currentPageSize }) => {
      const response = result.response ?? {};
      const items = result.items;
      const offset = typeof response.offset === 'number' ? response.offset : (currentPage - 1) * currentPageSize;
      const total = typeof response.total === 'number' ? response.total : offset + items.length;
      setTotalBroadcasts(typeof response.total === 'number' ? response.total : total);
      const counts = response.status_counts ?? {};
      setStatusCounts({
        draft: counts.draft ?? 0,
        scheduled: counts.scheduled ?? 0,
        sending: counts.sending ?? 0,
        sent: counts.sent ?? 0,
        failed: counts.failed ?? 0,
        cancelled: counts.cancelled ?? 0,
      });
      const recipients =
        typeof response.recipients === 'number'
          ? response.recipients
          : items.reduce((sum, item) => sum + (Number.isFinite(item.total) ? item.total : 0), 0);
      setRecipientTotal(recipients);
      const hasNextFlag =
        typeof response.has_next === 'boolean'
          ? response.has_next
          : offset + items.length < total;
      return {
        items,
        hasNext: hasNextFlag,
        total: typeof response.total === 'number' ? response.total : undefined,
      };
    },
    onError: (err) => extractErrorMessage(err, translate(BROADCAST_COPY.messages.loadError)),
  });
  React.useEffect(() => {
    setPage(1);
  }, [statusFilter, normalizedSearch, setPage]);

  const loadTemplates = React.useCallback(async () => {
    setTemplatesLoading(true);
    try {
      const res = await apiGet<{ items?: TemplateSummary[] }>('/v1/notifications/admin/templates');
      setTemplates(Array.isArray(res?.items) ? res.items : []);
    } catch (err) {
      setTemplates([]);
      const message = extractErrorMessage(err, translate(BROADCAST_COPY.messages.templatesLoadError));
      pushToast({ intent: 'error', description: message });
    } finally {
      setTemplatesLoading(false);
    }
  }, [pushToast]);

  React.useEffect(() => {
    void loadTemplates();
  }, [loadTemplates]);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  const templateMap = React.useMemo(() => new Map(templates.map((tpl) => [tpl.id, tpl])), [templates]);

  const summary = React.useMemo(
    () => ({
      totals: statusCounts,
      total: totalBroadcasts,
      recipients: recipientTotal,
    }),
    [recipientTotal, statusCounts, totalBroadcasts],
  );

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
        pushToast({ intent: 'success', description: translate(BROADCAST_COPY.toasts.sendQueued) });
        await refresh();
      } catch (err) {
        const message = extractErrorMessage(err, translate(BROADCAST_COPY.messages.sendNowError));
        setError(message);
        pushToast({ intent: 'error', description: message });
      } finally {
        setRowBusy((prev) => {
          const next = { ...prev };
          delete next[broadcastId];
          return next;
        });
      }
    },
    [pushToast, refresh, setError],
  );

  const handleCancel = React.useCallback(
    async (broadcastId: string) => {
      const confirmed = await confirm({
        title: translate(BROADCAST_COPY.confirm.cancel.title),
        description: translate(BROADCAST_COPY.confirm.cancel.description),
        confirmLabel: translate(BROADCAST_COPY.confirm.cancel.confirm),
        cancelLabel: translate(BROADCAST_COPY.confirm.cancel.dismiss),
        destructive: true,
      });
      if (!confirmed) return;
      setRowBusy((prev) => ({ ...prev, [broadcastId]: 'cancel' }));
      try {
        await apiPost(`/v1/notifications/admin/broadcasts/${broadcastId}/actions/cancel`, {});
        pushToast({ intent: 'success', description: translate(BROADCAST_COPY.toasts.cancelSuccess) });
        await refresh();
      } catch (err) {
        const message = extractErrorMessage(err, translate(BROADCAST_COPY.messages.cancelError));
        setError(message);
        pushToast({ intent: 'error', description: message });
      } finally {
        setRowBusy((prev) => {
          const next = { ...prev };
          delete next[broadcastId];
          return next;
        });
      }
    },
    [confirm, pushToast, refresh, setError],
  );

  const submit = React.useCallback(async () => {
    setFormError(null);
    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setFormError(translate(BROADCAST_COPY.messages.validation.titleRequired));
      return;
    }
    const hasBody = body.trim().length > 0;
    const hasTemplate = Boolean(templateId);
    if (!hasBody && !hasTemplate) {
      setFormError(translate(BROADCAST_COPY.messages.validation.bodyOrTemplate));
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
            setFormError(translate(BROADCAST_COPY.messages.validation.segmentObject));
            return;
          }
          Object.assign(filters, parsed as Record<string, unknown>);
        } catch {
          setFormError(translate(BROADCAST_COPY.messages.validation.segmentJson));
          return;
        }
      }
      if (Object.keys(filters).length === 0) {
        setFormError(translate(BROADCAST_COPY.messages.validation.segmentEmpty));
        return;
      }
      audiencePayload.filters = filters;
    } else if (audienceType === 'explicit_users') {
      const ids = explicitIdsInput
        .split(/\s+|,|;+/)
        .map((value) => value.trim())
        .filter(Boolean);
      const unique = Array.from(new Set(ids));
      if (unique.length === 0) {
        setFormError(translate(BROADCAST_COPY.messages.validation.explicitEmpty));
        return;
      }
      audiencePayload.user_ids = unique;
    }

    let scheduledAt: string | null = null;
    if (scheduleMode === 'schedule') {
      if (!scheduledAtInput.trim()) {
        setFormError(translate(BROADCAST_COPY.messages.validation.scheduleRequired));
        return;
      }
      const iso = toIsoUtc(scheduledAtInput);
      if (!iso) {
        setFormError(translate(BROADCAST_COPY.messages.validation.scheduleInvalid));
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
        pushToast({ intent: 'success', description: translate(BROADCAST_COPY.toasts.updateSuccess) });
      } else {
        const createdBy = user?.id ?? 'admin';
        await apiPost('/v1/notifications/admin/broadcasts', {
          ...payloadBase,
          created_by: createdBy,
        });
        pushToast({ intent: 'success', description: translate(BROADCAST_COPY.toasts.createSuccess) });
      }
      setDrawerOpen(false);
      setEditing(null);
      await refresh();
    } catch (err) {
      const fallback = editing ? BROADCAST_COPY.messages.updateError : BROADCAST_COPY.messages.createError;
      const message = extractErrorMessage(err, translate(fallback));
      setFormError(message);
      pushToast({ intent: 'error', description: message });
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
    pushToast,
  ]);

  const statusOptions = STATUS_FILTER_ORDER.map((value) => ({
    value,
    label: translate(STATUS_FILTER_LABELS[value]),
  }));

  const showingBase = translateWithVars(BROADCAST_COPY.filters.showing, {
    current: broadcasts.length,
    total: totalBroadcasts,
  });
  const showingText = normalizedSearch
    ? `${showingBase} ${translateWithVars(BROADCAST_COPY.filters.matching, { query: normalizedSearch })}.`
    : `${showingBase}.`;
  return (
    <>
      <ContentLayout
        context="notifications"
        title={translate(BROADCAST_COPY.layout.title)}
        description={translate(BROADCAST_COPY.layout.description)}
      >
        <div className="space-y-6">
          <NotificationSurface className="space-y-6 p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="space-y-2">
                <div className="text-xs font-semibold uppercase tracking-widest text-primary-600">
                  {translate(BROADCAST_COPY.layout.contextLabel)}
                </div>
                <h1 className="text-2xl font-semibold text-gray-900">
                  {translate(BROADCAST_COPY.layout.title)}
                </h1>
                <p className="max-w-2xl text-sm text-gray-600">
                  {translate(BROADCAST_COPY.layout.description)}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Button variant="outlined" color="neutral" onClick={handleRefresh} disabled={loading}>
                  {translate(BROADCAST_COPY.layout.refresh)}
                </Button>
                <Button onClick={() => openDrawer(null)}>{translate(BROADCAST_COPY.layout.create)}</Button>
              </div>
            </div>

            {error && (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            )}

            <div className="flex flex-col gap-3 rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm md:flex-row md:items-end md:justify-between">
              <div className="flex flex-1 flex-wrap items-center gap-3">
                <Input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder={translate(BROADCAST_COPY.filters.searchPlaceholder)}
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
                  {statusOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </Select>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
                <span>{showingText}</span>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
                <div className="text-xs uppercase tracking-wide text-gray-500">
                  {translate(BROADCAST_COPY.summary.total)}
                </div>
                <div className="mt-2 text-2xl font-semibold text-gray-900">{summary.total}</div>
                <div className="text-xs text-gray-500">
                  {translateWithVars(BROADCAST_COPY.summary.recipients, { count: summary.recipients })}
                </div>
              </div>
              <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
                <div className="text-xs uppercase tracking-wide text-gray-500">
                  {translate(BROADCAST_COPY.summary.drafts)}
                </div>
                <div className="mt-2 text-2xl font-semibold text-gray-900">{summary.totals.draft}</div>
              </div>
              <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
                <div className="text-xs uppercase tracking-wide text-gray-500">
                  {translate(BROADCAST_COPY.summary.scheduled)}
                </div>
                <div className="mt-2 text-2xl font-semibold text-gray-900">{summary.totals.scheduled}</div>
              </div>
              <div className="rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
                <div className="text-xs uppercase tracking-wide text-gray-500">
                  {translate(BROADCAST_COPY.summary.sent)}
                </div>
                <div className="mt-2 text-2xl font-semibold text-gray-900">{summary.totals.sent}</div>
                <div className="text-xs text-gray-500">
                  {translateWithVars(BROADCAST_COPY.summary.failed, { count: summary.totals.failed })}
                </div>
              </div>
            </div>

            <div className="hide-scrollbar overflow-x-auto">
              <Table.Table className="min-w-[1000px] text-left rtl:text-right">
                <Table.THead>
                  <Table.TR>
                    <Table.TH className={`${notificationTableHeadCellClass} w-[32%]`}>
                      {translate(BROADCAST_COPY.table.header.broadcast)}
                    </Table.TH>
                    <Table.TH className={`${notificationTableHeadCellClass} w-[20%]`}>
                      {translate(BROADCAST_COPY.table.header.audience)}
                    </Table.TH>
                    <Table.TH className={`${notificationTableHeadCellClass} w-[16%]`}>
                      {translate(BROADCAST_COPY.table.header.delivery)}
                    </Table.TH>
                    <Table.TH className={`${notificationTableHeadCellClass} w-[20%]`}>
                      {translate(BROADCAST_COPY.table.header.timeline)}
                    </Table.TH>
                    <Table.TH className={`${notificationTableHeadCellClass} w-[12%] text-right`}>
                      {translate(BROADCAST_COPY.table.header.actions)}
                    </Table.TH>
                  </Table.TR>
                </Table.THead>
                <Table.TBody>
                  {loading && (
                    <Table.TR className={notificationTableRowClass}>
                      <Table.TD colSpan={5} className="px-6 py-10 text-center">
                        <div className="flex items-center justify-center gap-2 text-sm text-indigo-600">
                          <Spinner size="sm" />
                          <span>{translate(BROADCAST_COPY.table.loading)}</span>
                        </div>
                      </Table.TD>
                    </Table.TR>
                  )}
                  {!loading && broadcasts.length === 0 && (
                    <Table.TR className={notificationTableRowClass}>
                      <Table.TD colSpan={5} className="px-6 py-12 text-center text-sm text-gray-500">
                        {translate(BROADCAST_COPY.table.empty)}
                      </Table.TD>
                    </Table.TR>
                  )}
                  {!loading &&
                    broadcasts.map((broadcast) => {
                      const statusClass = STATUS_THEME[broadcast.status] ?? STATUS_THEME.draft;
                      const tpl = broadcast.template_id ? templateMap.get(broadcast.template_id) : undefined;
                      const audienceValue = broadcast.audience?.type ?? 'all_users';
                      const isMutable = broadcast.status === 'draft' || broadcast.status === 'scheduled';
                      const isScheduled = broadcast.status === 'scheduled';
                      const rowState = rowBusy[broadcast.id];
                      const statusLabel = translate(STATUS_LABELS[broadcast.status]);
                      const audienceLabel = translate(
                        AUDIENCE_LABELS[(audienceValue as AudienceType) ?? 'all_users'] ?? AUDIENCE_LABELS.all_users,
                      );

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
                                  {statusLabel}
                                </span>
                              </div>
                              {tpl ? (
                                <div className="text-xs text-gray-500 dark:text-dark-200">
                                  {translate(BROADCAST_COPY.table.templatePrefix)} {tpl.name} ({tpl.slug})
                                </div>
                              ) : null}
                              {broadcast.body && (
                                <div className="text-xs text-gray-500 dark:text-dark-300">
                                  {translate(BROADCAST_COPY.table.previewPrefix)} {previewBody(broadcast.body)}
                                </div>
                              )}
                              <div className="text-xs text-gray-400">
                                {translateWithVars(BROADCAST_COPY.table.createdBy, {
                                  date: formatDateTime(broadcast.created_at),
                                  author: broadcast.created_by,
                                })}
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
                                  {translateWithVars(BROADCAST_COPY.table.recipients, {
                                    count: broadcast.audience.user_ids.length,
                                  })}
                                </div>
                              ) : null}
                            </div>
                          </Table.TD>
                          <Table.TD className="px-6 py-4 align-top">
                            <div className="text-sm text-gray-700 dark:text-dark-100">
                              {translateWithVars(BROADCAST_COPY.table.sentRatio, {
                                sent: broadcast.sent,
                                total: broadcast.total,
                              })}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-dark-300">
                              {translateWithVars(BROADCAST_COPY.table.failed, { count: broadcast.failed })}
                            </div>
                          </Table.TD>
                          <Table.TD className="px-6 py-4 align-top">
                            <div className="text-xs text-gray-500 dark:text-dark-300">
                              {translateWithVars(BROADCAST_COPY.table.scheduled, {
                                value: formatDateTime(broadcast.scheduled_at),
                              })}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-dark-300">
                              {translateWithVars(BROADCAST_COPY.table.started, {
                                value: formatDateTime(broadcast.started_at),
                              })}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-dark-300">
                              {translateWithVars(BROADCAST_COPY.table.finished, {
                                value: formatDateTime(broadcast.finished_at),
                              })}
                            </div>
                          </Table.TD>
                          <Table.TD className="px-6 py-4 align-top text-right">
                            <div className="flex justify-end gap-2">
                              {isMutable && (
                                <Button size="sm" variant="ghost" onClick={() => openDrawer(broadcast)}>
                                  {translate(BROADCAST_COPY.table.edit)}
                                </Button>
                              )}
                              {isMutable && (
                                <Button
                                  size="sm"
                                  variant="outlined"
                                  onClick={() => handleSendNow(broadcast.id)}
                                  disabled={rowState === 'send'}
                                >
                                  {rowState === 'send'
                                    ? translate(BROADCAST_COPY.table.sending)
                                    : translate(BROADCAST_COPY.table.sendNow)}
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
                                  {rowState === 'cancel'
                                    ? translate(BROADCAST_COPY.table.cancelling)
                                    : translate(BROADCAST_COPY.table.cancel)}
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
                <span>{translate(BROADCAST_COPY.filters.rowsPerPage)}</span>
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
            title={translate(editing ? BROADCAST_COPY.drawer.editTitle : BROADCAST_COPY.drawer.newTitle)}
            widthClass="w-full max-w-2xl"
            footer={
              <div className="flex justify-end gap-2">
                <Button variant="outlined" color="neutral" onClick={closeDrawer} disabled={saving}>
                  {translate(BROADCAST_COPY.drawer.cancel)}
                </Button>
                <Button onClick={submit} disabled={saving}>
                  {saving
                    ? translate(BROADCAST_COPY.drawer.saving)
                    : translate(editing ? BROADCAST_COPY.drawer.update : BROADCAST_COPY.drawer.create)}
                </Button>
              </div>
            }
          >
            <div className="space-y-5 p-6">
              {formError && (
                <div className="rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                  {formError}
                </div>
              )}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {translate(BROADCAST_COPY.drawer.titleLabel)}
                </label>
                <Input
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder={translate(BROADCAST_COPY.drawer.titlePlaceholder)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {translate(BROADCAST_COPY.drawer.templateLabel)}
                </label>
                <Select value={templateId} onChange={(event) => setTemplateId(event.target.value)}>
                  <option value="">{translate(BROADCAST_COPY.drawer.templateEmpty)}</option>
                  {templates.map((tpl) => (
                    <option key={tpl.id} value={tpl.id}>
                      {tpl.name} ({tpl.slug})
                    </option>
                  ))}
                </Select>
                {templatesLoading && (
                  <div className="text-xs text-gray-500">{translate(BROADCAST_COPY.drawer.templateLoading)}</div>
                )}
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {translate(BROADCAST_COPY.drawer.bodyLabel)}
                </label>
                <Textarea
                  rows={6}
                  value={body}
                  onChange={(event) => setBody(event.target.value)}
                  placeholder={translate(BROADCAST_COPY.drawer.bodyPlaceholder)}
                />
                <p className="text-xs text-gray-500">{translate(BROADCAST_COPY.drawer.bodyHint)}</p>
              </div>
              <div className="space-y-3">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {translate(BROADCAST_COPY.drawer.audienceLabel)}
                </label>
                <Select value={audienceType} onChange={(event) => setAudienceType(event.target.value as AudienceType)}>
                  <option value="all_users">{translate(AUDIENCE_LABELS.all_users)}</option>
                  <option value="segment">{translate(AUDIENCE_LABELS.segment)}</option>
                  <option value="explicit_users">{translate(AUDIENCE_LABELS.explicit_users)}</option>
                </Select>
                {audienceType === 'segment' && (
                  <div className="space-y-3 rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm">
                    <div className="grid gap-3 sm:grid-cols-2">
                      {SEGMENT_FILTER_KEYS.map(({ key, label }) => (
                        <div key={key} className="space-y-1">
                          <label className="text-xs font-medium text-gray-500">{translate(label)}</label>
                          <Input
                            value={segmentFilters[key] ?? ''}
                            onChange={(event) =>
                              setSegmentFilters((prev) => ({
                                ...prev,
                                [key]: event.target.value,
                              }))
                            }
                            placeholder={translate(label)}
                          />
                        </div>
                      ))}
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs font-medium text-gray-500">
                        {translate(BROADCAST_COPY.drawer.segmentAdvancedLabel)}
                      </label>
                      <Textarea
                        rows={3}
                        value={segmentCustom}
                        onChange={(event) => setSegmentCustom(event.target.value)}
                        placeholder='{"region": "emea"}'
                      />
                      <p className="text-xs text-gray-500">
                        {translate(BROADCAST_COPY.drawer.segmentAdvancedHint)}
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
                    <p className="text-xs text-gray-500">{translate(BROADCAST_COPY.drawer.explicitHint)}</p>
                  </div>
                )}
              </div>
              <div className="space-y-2 border-t border-white/60 pt-4 dark:border-dark-600/50">
                <label className="text-xs font-semibold uppercase tracking-wide text-gray-500">
                  {translate(BROADCAST_COPY.drawer.schedulingLabel)}
                </label>
                <div className="grid gap-3 sm:grid-cols-[180px_1fr]">
                  <Select value={scheduleMode} onChange={(event) => setScheduleMode(event.target.value as 'none' | 'schedule')}>
                    <option value="none">{translate(BROADCAST_COPY.drawer.schedulingNone)}</option>
                    <option value="schedule">{translate(BROADCAST_COPY.drawer.schedulingLater)}</option>
                  </Select>
                  {scheduleMode === 'schedule' && (
                    <div className="space-y-1">
                      <Input
                        type="datetime-local"
                        value={scheduledAtInput}
                        onChange={(event) => setScheduledAtInput(event.target.value)}
                      />
                      <p className="text-xs text-gray-500">{translate(BROADCAST_COPY.drawer.schedulingHint)}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </Drawer>
        </div>
      </ContentLayout>
      {confirmationElement}
    </>
  );
}

import React from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Avatar, Badge, Button, Card, Drawer, Pagination, Spinner, Tabs } from "@ui";
import { formatDateTime } from '../../../shared/utils/format';
import { CaseConversation } from './CaseConversation';
import { CaseWorkflowControls } from './CaseWorkflowControls';
import { CaseTimeline } from './CaseTimeline';
import { apiGet } from '../../../shared/api/client';
import { useAuth } from '../../../shared/auth';
import { useModerationCase } from './hooks';
import { Paperclip } from "lucide-react";
import { CaseNote } from './types';

type CaseFormState = {
  title: string;
  status: string;
  type: string;
  queue: string;
  severity: string;
  priority: string;
  assignee_id: string;
  tags: string[];
  description: string;
};

type CaseFormField = keyof CaseFormState;
type ModerationUserDetail = {
  id: string;
  username?: string | null;
  email?: string | null;
  roles?: string[];
  status?: string | null;
  registered_at?: string | null;
  last_seen_at?: string | null;
  complaints_count?: number | null;
  notes_count?: number | null;
  sanction_count?: number | null;
  active_sanctions?: Array<{
    id?: string;
    type?: string | null;
    status?: string | null;
    reason?: string | null;
    issued_at?: string | null;
    starts_at?: string | null;
    ends_at?: string | null;
  }>;
  last_sanction?: {
    id?: string;
    type?: string | null;
    status?: string | null;
    reason?: string | null;
    issued_at?: string | null;
    starts_at?: string | null;
    ends_at?: string | null;
  } | null;
  meta?: Record<string, any> | null;
};

type ComposerAttachment = {
  id: string;
  name: string;
  type: string;
  dataUrl: string;
};

const TIMELINE_PAGE_SIZE = 20;

function humanizeLabel(value?: string | null) {
  if (value == null) return null;
  const normalized = String(value).trim();
  if (!normalized) return null;
  return normalized
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatNumber(value?: number | null): number {
  if (typeof value !== 'number') return 0;
  if (!Number.isFinite(value)) return 0;
  return value;
}

function normalizeNickname(note: CaseNote, fallback?: string | null): string {
  const meta = (note.meta || {}) as Record<string, unknown>;
  const candidates: Array<string | null | undefined> = [
    note.author_name,
    (meta as any)?.author_name,
    (meta as any)?.author_username,
    (meta as any)?.username,
    (meta as any)?.user_name,
    (meta as any)?.display_name,
    (meta as any)?.actor_name,
    fallback,
    note.author_id,
  ];
  for (const candidate of candidates) {
    if (typeof candidate !== 'string') continue;
    const trimmed = candidate.trim();
    if (trimmed) return trimmed;
  }
  return 'User';
}

export function CaseDetailPage() {
  const { caseId: routeCaseId } = useParams<{ caseId: string }>();
  const navigate = useNavigate();
  const { caseId, data, loading, error, load, update, addNote, select } = useModerationCase(routeCaseId);

  const { user } = useAuth();
  const currentUserId = React.useMemo(() => {
    if (!user) return '';
    return (user as any).id || (user as any).sub || '';
  }, [user]);
  const currentUserLabel = React.useMemo(() => {
    if (!user) return '';
    return (user as any).username || (user as any).email || currentUserId;
  }, [user, currentUserId]);

  const [form, setForm] = React.useState<CaseFormState>(() => ({
    title: '',
    status: '',
    type: '',
    queue: '',
    severity: '',
    priority: '',
    assignee_id: '',
    tags: [],
    description: '',
  }));
  const [tab, setTab] = React.useState<'internal' | 'external' | 'timeline'>('internal');
  const [message, setMessage] = React.useState('');
  const [messagePinned, setMessagePinned] = React.useState(false);
  const [messageAttachments, setMessageAttachments] = React.useState<ComposerAttachment[]>([]);
  const [saving, setSaving] = React.useState(false);
  const [sending, setSending] = React.useState(false);
  const [localError, setLocalError] = React.useState<string | null>(null);
  const [showUserDrawer, setShowUserDrawer] = React.useState(false);
  const [userDetail, setUserDetail] = React.useState<ModerationUserDetail | null>(null);
  const [userLoading, setUserLoading] = React.useState(false);
  const [userError, setUserError] = React.useState<string | null>(null);
  const [timelineDrawerOpen, setTimelineDrawerOpen] = React.useState(false);
  const [timelinePage, setTimelinePage] = React.useState(1);

  const conversationScrollRef = React.useRef<HTMLDivElement | null>(null);
  const attachmentInputRef = React.useRef<HTMLInputElement | null>(null);
  const composerTextareaRef = React.useRef<HTMLTextAreaElement | null>(null);

  const subjectId = data?.subject_id ? String(data.subject_id) : '';
  const subjectLabel = data?.subject_label ? String(data.subject_label) : '';
  const subjectIsUser = React.useMemo(() => {
    const type = String(data?.subject_type || '').toLowerCase();
    return ['user', 'customer', 'player', 'account'].includes(type);
  }, [data?.subject_type]);

  const sortedTimelineItems = React.useMemo(() => {
    if (!Array.isArray(data?.events)) return [];
    return [...data.events].sort((a, b) => {
      const at = a?.created_at ? new Date(a.created_at).getTime() : 0;
      const bt = b?.created_at ? new Date(b.created_at).getTime() : 0;
      return bt - at;
    });
  }, [data?.events]);
  const timelinePageCount = Math.max(1, Math.ceil(sortedTimelineItems.length / TIMELINE_PAGE_SIZE));
  const timelinePageItems = React.useMemo(() => {
    if (!sortedTimelineItems.length) return [];
    const start = (timelinePage - 1) * TIMELINE_PAGE_SIZE;
    return sortedTimelineItems.slice(start, start + TIMELINE_PAGE_SIZE);
  }, [sortedTimelineItems, timelinePage]);
  const timelineHasMore = sortedTimelineItems.length > TIMELINE_PAGE_SIZE;
  const timelineSummaryText = React.useMemo(() => {
    const total = sortedTimelineItems.length;
    if (total === 0) return 'No events';
    return total === 1 ? 'Showing 1 event' : `Showing ${total} events`;
  }, [sortedTimelineItems.length]);

  React.useEffect(() => {
    if (!routeCaseId) return;
    select(routeCaseId);
    void load(routeCaseId, { force: true });
  }, [load, routeCaseId, select]);

  React.useEffect(() => {
    if (!data) return;
    setForm({
      title: String(data.title ?? ''),
      status: String(data.status ?? ''),
      type: String(data.type ?? ''),
      queue: String(data.queue ?? ''),
      severity: String(data.severity ?? ''),
      priority: String(data.priority ?? ''),
      assignee_id: String(data.assignee_id ?? ''),
      tags: Array.isArray(data.tags) ? data.tags.filter(Boolean).map(String) : [],
      description: String(data.description ?? ''),
    });
  }, [data]);

  React.useEffect(() => {
    setShowUserDrawer(false);
    setUserDetail(null);
    setUserError(null);
    setUserLoading(false);
    setTimelineDrawerOpen(false);
    setTimelinePage(1);
    setMessageAttachments([]);
    setMessage('');
    setMessagePinned(false);
  }, [routeCaseId]);

  React.useEffect(() => {
    if (!showUserDrawer) return;
    if (!subjectIsUser) return;
    const fetch = async () => {
      if (!subjectId) {
        setUserDetail(null);
        return;
      }
      setUserLoading(true);
      setUserError(null);
      try {
        const detail = await apiGet<ModerationUserDetail>(`/api/moderation/users/${encodeURIComponent(subjectId)}`);
        setUserDetail(detail || null);
      } catch (err: any) {
        setUserError(String(err?.message || err || 'error'));
        setUserDetail(null);
      } finally {
        setUserLoading(false);
      }
    };
    void fetch();
  }, [showUserDrawer, subjectId, subjectIsUser]);

  React.useEffect(() => {
    const textarea = composerTextareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 240)}px`;
  }, [message]);


  React.useEffect(() => {
    if (tab === 'timeline') return;
    const node = conversationScrollRef.current;
    if (!node) return;
    node.scrollTop = node.scrollHeight;
  }, [tab, data?.notes?.length]);

  const handleFieldChange = React.useCallback(
    (field: CaseFormField, value: any) => {
      setForm((prev) => ({ ...prev, [field]: value }));
    },
    []
  );

  const handleAssigneeChange = React.useCallback(
    (option: { id?: string | null; label?: string | null } | null) => {
      setForm((prev) => ({ ...prev, assignee_id: option?.id ? String(option.id) : '' }));
    },
    []
  );

  const handleSave = React.useCallback(async () => {
    setSaving(true);
    setLocalError(null);
    try {
      await update({
        title: form.title || null,
        status: form.status || null,
        type: form.type || null,
        queue: form.queue || null,
        severity: form.severity || null,
        priority: form.priority || null,
        assignee_id: form.assignee_id || null,
        tags: form.tags.filter(Boolean),
        description: form.description || null,
      });
      await load(undefined, { force: true });
    } catch (err) {
      const messageText =
        err && typeof err === 'object' && 'message' in err ? String((err as any).message) : String(err ?? 'error');
      setLocalError(messageText);
    } finally {
      setSaving(false);
    }
  }, [form, load, update]);

  const handleMessageChange = React.useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(event.target.value);
  }, []);

  const handleAttachmentFiles = React.useCallback((files: FileList | null) => {
    if (!files || files.length === 0) return;
    setLocalError(null);
    const toRead = Array.from(files);
    const promises = toRead.map(
      (file) =>
        new Promise<ComposerAttachment>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            if (typeof reader.result !== 'string') {
              reject(new Error('Failed to read attachment'));
              return;
            }
            const id =
              typeof globalThis !== 'undefined' && globalThis.crypto && 'randomUUID' in globalThis.crypto
                ? (globalThis.crypto as Crypto).randomUUID()
                : Math.random().toString(36).slice(2, 10);
            resolve({
              id,
              name: file.name || 'attachment',
              type: file.type || 'application/octet-stream',
              dataUrl: reader.result,
            });
          };
          reader.onerror = () => reject(reader.error || new Error('Failed to read attachment'));
          reader.readAsDataURL(file);
        }),
    );
    void Promise.all(promises)
      .then((loaded) => {
        setMessageAttachments((prev) => [...prev, ...loaded]);
      })
      .catch((err) => {
        const messageText =
          err && typeof err === 'object' && 'message' in err ? String((err as any).message) : 'Failed to attach file';
        setLocalError(messageText);
      })
      .finally(() => {
        if (attachmentInputRef.current) {
          attachmentInputRef.current.value = '';
        }
      });
  }, []);

  const handleAttachmentRemove = React.useCallback((id: string) => {
    setMessageAttachments((prev) => prev.filter((item) => item.id !== id));
  }, []);

  const handleAttachmentButtonClick = React.useCallback(() => {
    attachmentInputRef.current?.click();
  }, []);

  const handleSendMessage = React.useCallback(async () => {
    const text = message.trim();
    const hasAttachments = messageAttachments.length > 0;
    if (!text && !hasAttachments) return;
    setSending(true);
    setLocalError(null);
    try {
      await addNote({
        text: text || '',
        visibility: tab === 'internal' ? 'internal' : 'external',
        pinned: messagePinned,
        attachments: messageAttachments.map((file) => ({
          name: file.name,
          type: file.type,
          url: file.dataUrl,
        })),
      });
      setMessage('');
      setMessagePinned(false);
      setMessageAttachments([]);
      if (attachmentInputRef.current) attachmentInputRef.current.value = '';
    } catch (err) {
      const messageText =
        err && typeof err === 'object' && 'message' in err ? String((err as any).message) : String(err ?? 'error');
      setLocalError(messageText);
    } finally {
      setSending(false);
    }
  }, [addNote, message, messageAttachments, messagePinned, tab]);

  const handleComposerKeyDown = React.useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        void handleSendMessage();
      }
    },
    [handleSendMessage],
  );

  const composerCanSend = React.useMemo(() => {
    return Boolean(message.trim()) || messageAttachments.length > 0;
  }, [message, messageAttachments.length]);

  const subjectDisplayName = React.useMemo(() => {
    if (subjectLabel) return subjectLabel;
    if (subjectIsUser && Array.isArray(data?.notes) && data.notes.length) {
      const lastNote = [...data.notes].reverse().find((note) => note.visibility !== 'external');
      if (lastNote) {
        return normalizeNickname(lastNote, subjectLabel);
      }
    }
    return subjectId || '-';
  }, [data?.notes, subjectId, subjectLabel, subjectIsUser]);

  const assigneeDisplay = React.useMemo(() => {
    return form.assignee_id || data?.assignee_label || data?.assignee_id || 'Unassigned';
  }, [data?.assignee_id, data?.assignee_label, form.assignee_id]);

  const composerHint = tab === 'internal' ? 'Internal note...' : 'Customer reply...';

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 text-sm text-gray-500 dark:border-dark-600">
        <Button variant="ghost" color="neutral" onClick={() => navigate('/moderation/cases')}>
          Back
        </Button>
        <div className="flex items-center gap-3">
          <span className="hidden text-xs text-gray-400 sm:inline">Case ID: {caseId || '-'}</span>
          <Button variant="ghost" color="neutral" onClick={() => void (caseId ? load(caseId, { force: true }) : Promise.resolve())}>
            Refresh
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-hidden px-6 pb-6 pt-5">
        {loading && !data && (
          <div className="flex items-center gap-2 text-gray-500">
            <Spinner size="sm" /> Loading case...
          </div>
        )}
        {localError && (
          <div className="rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{localError}</div>
        )}
        {error && (
          <div className="rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
        )}

        {data && (
          <div className="grid h-full min-h-0 gap-6 xl:grid-cols-[minmax(0,2.2fr)_minmax(0,1fr)]">
            <Card
              skin="shadow"
              className="flex h-full min-h-0 flex-col overflow-hidden rounded-3xl bg-gradient-to-br from-white via-white to-gray-50 shadow-sm dark:from-dark-800 dark:via-dark-800 dark:to-dark-700"
            >
              <div className="flex items-center justify-between border-b border-gray-200 px-5 py-3 text-sm font-semibold text-gray-700 dark:border-dark-600 dark:text-gray-100">
                <div className="flex items-center gap-2">
                  <span>Conversation</span>
                  <span className="rounded-full bg-primary-100 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-primary-700 dark:bg-primary-500/30 dark:text-primary-100">
                    {sortedTimelineItems.length} events
                  </span>
                </div>
                <div className="text-xs text-gray-400">Case ID: {caseId || '-'}</div>
              </div>
              <div className="flex min-h-0 flex-col">
                <div className="border-b border-gray-200 px-5 pt-3 dark:border-dark-600">
                  <Tabs
                    value={tab}
                    onChange={(key) => setTab(key as 'internal' | 'external' | 'timeline')}
                    items={[
                      { key: 'internal', label: 'Internal' },
                      { key: 'external', label: 'Customer' },
                      { key: 'timeline', label: 'Timeline' },
                    ]}
                  />
                </div>
                <div className="flex-1 overflow-hidden px-5 py-4">
                  {tab === 'timeline' ? (
                    <div className="h-full overflow-y-auto pr-1">
                      <CaseTimeline items={sortedTimelineItems} emptyMessage="No events yet" />
                    </div>
                  ) : (
                    <div className="flex h-full flex-col gap-4">
                      <div ref={conversationScrollRef} className="flex-1 overflow-y-auto pr-1">
                        <CaseConversation
                          notes={data.notes}
                          variant={tab === 'external' ? 'external' : 'internal'}
                          subjectId={data?.subject_id}
                          subjectLabel={subjectDisplayName}
                        />
                      </div>
                      <div className="rounded-3xl border border-gray-200 bg-white p-4 shadow-sm">
                        {messageAttachments.length > 0 && (
                          <div className="mb-3 flex flex-wrap gap-3">
                            {messageAttachments.map((file) => (
                              <div
                                key={file.id}
                                className="relative overflow-hidden rounded-2xl border border-gray-200 bg-gray-50 shadow-sm"
                              >
                                <img src={file.dataUrl} alt={file.name} className="h-24 w-24 object-cover" />
                                <button
                                  type="button"
                                  className="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-black/60 text-xs font-semibold text-white transition hover:bg-black/80"
                                  onClick={() => handleAttachmentRemove(file.id)}
                                  aria-label={`Remove ${file.name}`}
                                >
                                  &times;
                                </button>
                                <div className="w-24 truncate px-2 pb-2 text-[11px] text-gray-500">{file.name}</div>
                              </div>
                            ))}
                          </div>
                        )}
                        <div className="flex items-end gap-3">
                          <button
                            type="button"
                            onClick={handleAttachmentButtonClick}
                            className="flex h-10 w-10 items-center justify-center rounded-2xl border border-gray-200 bg-gray-50 text-gray-500 transition hover:border-primary-200 hover:bg-primary-50 hover:text-primary-600 disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={sending}
                          >
                            <Paperclip className="h-4 w-4" />
                            <span className="sr-only">Attach image</span>
                          </button>
                          <textarea
                            ref={composerTextareaRef}
                            value={message}
                            placeholder={composerHint}
                            onChange={handleMessageChange}
                            onKeyDown={handleComposerKeyDown}
                            className="min-h-[44px] flex-1 resize-none border-0 bg-transparent text-sm text-gray-800 placeholder:text-gray-400 outline-none focus:outline-none focus:ring-0"
                            rows={1}
                          />
                        </div>
                        <input
                          ref={attachmentInputRef}
                          type="file"
                          accept="image/*"
                          multiple
                          className="hidden"
                          onChange={(event) => handleAttachmentFiles(event.target.files)}
                        />
                        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-gray-500">
                          <label className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={messagePinned}
                              onChange={(e) => setMessagePinned(e.target.checked)}
                            />
                            Pin message
                          </label>
                          <div className="flex items-center gap-4">
                            <span className="hidden text-[11px] text-gray-400 sm:inline">Ctrl/Cmd + Enter to send</span>
                            <Button size="sm" onClick={handleSendMessage} disabled={!composerCanSend || sending}>
                              {sending ? 'Sending...' : tab === 'internal' ? 'Add note' : 'Send reply'}
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                {tab === 'timeline' && (
                  <div className="flex items-center justify-between gap-2 border-t border-gray-200 px-5 py-3 text-xs text-gray-500 dark:border-dark-600">
                    <span>{timelineSummaryText}</span>
                    {timelineHasMore && (
                      <Button size="sm" variant="ghost" color="neutral" onClick={() => setTimelineDrawerOpen(true)}>
                        Open full timeline
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </Card>

            <Card skin="shadow" className="flex h-full min-h-0 flex-col overflow-hidden rounded-3xl bg-white p-0 shadow-sm dark:bg-dark-800">
              <div className="flex-1 overflow-y-auto px-4 py-4">
                <CaseWorkflowControls
                  subjectLabel={subjectDisplayName || '-'}
                  onSubjectClick={subjectIsUser ? () => setShowUserDrawer(true) : undefined}
                  createdAt={formatDateTime(data?.created_at)}
                  updatedAt={formatDateTime(data?.updated_at)}
                  typeValue={form.type}
                  onTypeChange={(value) => handleFieldChange('type', value)}
                  title={form.title}
                  onTitleChange={(value) => handleFieldChange('title', value)}
                  tags={form.tags}
                  onTagsChange={(value) => handleFieldChange('tags', value)}
                  description={form.description}
                  onDescriptionChange={(value) => handleFieldChange('description', value)}
                  status={form.status}
                  severity={form.severity}
                  priority={form.priority}
                  queue={form.queue}
                  assigneeId={form.assignee_id}
                  assigneeLabel={assigneeDisplay}
                  onStatusChange={(value) => handleFieldChange('status', value)}
                  onSeverityChange={(value) => handleFieldChange('severity', value)}
                  onPriorityChange={(value) => handleFieldChange('priority', value)}
                  onQueueChange={(value) => handleFieldChange('queue', value ?? '')}
                  onAssigneeChange={handleAssigneeChange}
                  currentUserId={currentUserId}
                  currentUserLabel={currentUserLabel}
                  onSave={handleSave}
                  onMarkResolved={() => handleFieldChange('status', 'resolved')}
                  onMoveToEscalation={() => handleFieldChange('queue', 'escalation')}
                  saving={saving}
                  loading={loading}
                />
              </div>
            </Card>
          </div>
        )}
      </div>

      <Drawer
        open={showUserDrawer}
        onClose={() => setShowUserDrawer(false)}
        title={subjectDisplayName ? `User ${subjectDisplayName}` : 'User'}
        widthClass="w-[520px]"
      >
        <div className="space-y-4 p-4">
          {userLoading ? (
            <div className="flex items-center justify-center py-8">
              <Spinner />
            </div>
          ) : userError ? (
            <div className="rounded border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{userError}</div>
          ) : userDetail ? (
            <>
              <div className="flex items-center gap-3">
                <Avatar size="md" name={userDetail.username || subjectDisplayName || subjectId || 'User'} />
                <div className="min-w-0">
                  <div className="text-lg font-semibold">{userDetail.username || subjectDisplayName || subjectId || 'User'}</div>
                  <div className="text-xs text-gray-500 break-all">ID: {userDetail.id}</div>
                  {userDetail.email && <div className="text-xs text-gray-500 break-all">{userDetail.email}</div>}
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs">
                {userDetail.status && (
                  <Badge color={String(userDetail.status).toLowerCase() === 'banned' ? 'error' : 'primary'} variant="soft">
                    {humanizeLabel(userDetail.status) || userDetail.status}
                  </Badge>
                )}
                {(userDetail.roles || []).map((role) => (
                  <Badge key={role} color="neutral" variant="soft">
                    {humanizeLabel(role) || role}
                  </Badge>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <div className="text-gray-500">Registered</div>
                  <div className="font-medium text-gray-800 dark:text-gray-100">{formatDateTime(userDetail.registered_at) || '-'}</div>
                </div>
                <div>
                  <div className="text-gray-500">Last seen</div>
                  <div className="font-medium text-gray-800 dark:text-gray-100">{formatDateTime(userDetail.last_seen_at) || '-'}</div>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3 text-center text-sm">
                <div className="rounded border border-gray-200 p-3 dark:border-dark-600">
                  <div className="text-xl font-semibold text-gray-900 dark:text-gray-100">{formatNumber(userDetail.complaints_count)}</div>
                  <div className="text-xs text-gray-500">Complaints</div>
                </div>
                <div className="rounded border border-gray-200 p-3 dark:border-dark-600">
                  <div className="text-xl font-semibold text-gray-900 dark:text-gray-100">{formatNumber(userDetail.notes_count)}</div>
                  <div className="text-xs text-gray-500">Notes</div>
                </div>
                <div className="rounded border border-gray-200 p-3 dark:border-dark-600">
                  <div className="text-xl font-semibold text-gray-900 dark:text-gray-100">{formatNumber(userDetail.sanction_count)}</div>
                  <div className="text-xs text-gray-500">Sanctions</div>
                </div>
              </div>
              {Array.isArray(userDetail.active_sanctions) && userDetail.active_sanctions.length > 0 && (
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">Active sanctions</div>
                  <ul className="mt-2 space-y-2">
                    {userDetail.active_sanctions.slice(0, 3).map((sanction) => (
                      <li
                        key={sanction?.id || `${sanction?.type}-${sanction?.issued_at}`}
                        className="rounded border border-gray-200 p-3 text-sm dark:border-dark-600 dark:bg-dark-700/40"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500 dark:text-gray-400">
                          <span className="font-medium text-gray-700 dark:text-gray-200">{humanizeLabel(sanction?.type) || 'Sanction'}</span>
                          <span>{formatDateTime(sanction?.issued_at || sanction?.starts_at)}</span>
                        </div>
                        {sanction?.reason && <div className="mt-1 text-gray-800 dark:text-gray-100">{sanction.reason}</div>}
                        {sanction?.ends_at && (
                          <div className="mt-1 text-[11px] uppercase tracking-wide text-gray-400 dark:text-gray-500">
                            Ends {formatDateTime(sanction.ends_at)}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {userDetail.last_sanction && !(Array.isArray(userDetail.active_sanctions) && userDetail.active_sanctions.length > 0) && (
                <div className="rounded border border-gray-200 p-3 text-xs dark:border-dark-600 dark:bg-dark-700/40">
                  <div className="flex items-center justify-between text-gray-500 dark:text-gray-400">
                    <span className="font-medium text-gray-700 dark:text-gray-100">Last sanction</span>
                    <span>{formatDateTime(userDetail.last_sanction.issued_at || userDetail.last_sanction.starts_at)}</span>
                  </div>
                  {userDetail.last_sanction.reason && (
                    <div className="mt-1 text-sm text-gray-800 dark:text-gray-100">{userDetail.last_sanction.reason}</div>
                  )}
                </div>
              )}
              {userDetail.meta && Object.keys(userDetail.meta).length > 0 && (
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">User metadata</div>
                  <div className="mt-2 space-y-2 text-xs">
                    {Object.entries(userDetail.meta).map(([key, value]) => (
                      <div key={key}>
                        <div className="font-medium text-gray-600 dark:text-gray-300">{key}</div>
                        <pre className="mt-1 whitespace-pre-wrap rounded bg-gray-50 p-2 text-gray-800 dark:bg-dark-700/40 dark:text-gray-100">
                          {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-sm text-gray-500">User data not available.</div>
          )}
        </div>
      </Drawer>
      <Drawer
        open={timelineDrawerOpen}
        onClose={() => setTimelineDrawerOpen(false)}
        title="Case timeline"
        widthClass="w-[640px]"
      >
        <div className="space-y-4 p-4">
          <CaseTimeline items={timelinePageItems} />
          {timelinePageCount > 1 && (
            <div className="flex justify-center">
              <Pagination page={timelinePage} total={timelinePageCount} onChange={(value) => setTimelinePage(value)} />
            </div>
          )}
        </div>
      </Drawer>
    </div>
  );
}

export default CaseDetailPage;
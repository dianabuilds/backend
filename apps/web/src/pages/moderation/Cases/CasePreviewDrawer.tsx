import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../shared/auth';
import { Badge, Button, Card, Drawer, Spinner } from "@ui";
import { apiGet } from '../../../shared/api/client';
import { formatDateTime } from '../../../shared/utils/format';
import { CaseWorkflowControls } from './CaseWorkflowControls';
import { CaseConversation } from './CaseConversation';
import { ModerationCaseDetail } from './types';

type Props = {
  open: boolean;
  loading: boolean;
  data: ModerationCaseDetail | null;
  error?: string | null;
  onClose: () => void;
  onRefresh: () => Promise<void>;
  onUpdate: (payload: Record<string, any>) => Promise<void>;
  onAddInternalNote: (note: { text: string; pinned?: boolean }) => Promise<void>;
};

export function CasePreviewDrawer({
  open,
  loading,
  data,
  error,
  onClose,
  onRefresh,
  onUpdate,
  onAddInternalNote,
}: Props) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const currentUserId = React.useMemo(() => {
    if (!user) return '';
    return (user as any).id || (user as any).sub || '';
  }, [user]);
  const currentUserLabel = React.useMemo(() => {
    if (!user) return '';
    return (user as any).username || (user as any).email || currentUserId;
  }, [user, currentUserId]);

  const [form, setForm] = React.useState({
    title: '',
    type: '',
    status: '',
    severity: '',
    priority: '',
    assignee_id: '',
    assignee_label: '',
    queue: '',
    tags: [] as string[],
    description: '',
  });
  const [saving, setSaving] = React.useState(false);
  const [noteText, setNoteText] = React.useState('');
  const [notePinned, setNotePinned] = React.useState(false);
  const [noteSubmitting, setNoteSubmitting] = React.useState(false);
  const [lastError, setLastError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!data) {
      setForm({
        title: '',
        type: '',
        status: '',
        severity: '',
        priority: '',
        assignee_id: '',
        assignee_label: '',
        queue: '',
        tags: [],
        description: '',
      });
      setNoteText('');
      setNotePinned(false);
      setLastError(error || null);
      return;
    }
    setForm({
      title: String(data.title ?? ''),
      type: String(data.type ?? ''),
      status: String(data.status ?? ''),
      severity: String(data.severity ?? ''),
      priority: String(data.priority ?? ''),
      assignee_id: String(data.assignee_id ?? ''),
      assignee_label: String((data as any).assignee_label ?? data.assignee_id ?? ''),
      queue: String(data.queue ?? ''),
      tags: Array.isArray(data.tags) ? data.tags.filter(Boolean).map(String) : [],
      description: String(data.description ?? ''),
    });
    setLastError(error || null);
  }, [data, error]);

  React.useEffect(() => {
    const id = data?.assignee_id;
    if (!id || !id.trim()) return;
    if (form.assignee_label && form.assignee_label !== id) return;
    (async () => {
      try {
        const res = await apiGet<{ username?: string | null; name?: string | null; email?: string | null }>(
          `/api/moderation/users/${encodeURIComponent(id)}`,
        );
        const label = res?.username || res?.name || res?.email || id;
        setForm((prev) => ({
          ...prev,
          assignee_label: prev.assignee_id === id ? String(label) : prev.assignee_label,
        }));
      } catch {
        // ignore lookup errors
      }
    })().catch(() => {});
  }, [data?.assignee_id, form.assignee_label]);

  const handleFieldChange = React.useCallback(
    (field: keyof typeof form, value: string) => {
      setForm((prev) => ({
        ...prev,
        [field]: value,
      }));
    },
    [],
  );

  const handleTagsChange = React.useCallback((tags: string[]) => {
    setForm((prev) => ({
      ...prev,
      tags,
    }));
  }, []);

  const handleAssigneeChange = React.useCallback(
    (option: { id?: string | null; label?: string | null } | null) => {
      const id = option?.id ? String(option.id) : '';
      const label = option?.label ? String(option.label) : '';
      setForm((prev) => ({
        ...prev,
        assignee_id: id,
        assignee_label: label || id,
      }));
    },
    [],
  );

  const handleSave = React.useCallback(async () => {
    if (!data) return;
    setSaving(true);
    setLastError(null);
    try {
      await onUpdate({
        title: form.title,
        type: form.type,
        status: form.status,
        severity: form.severity,
        priority: form.priority,
        assignee_id: form.assignee_id,
        queue: form.queue,
        tags: form.tags,
        description: form.description,
      });
      await onRefresh();
    } catch (err: any) {
      setLastError(String(err?.message || err || 'error'));
    } finally {
      setSaving(false);
    }
  }, [data, form, onRefresh, onUpdate]);

  const handleNoteSubmit = React.useCallback(async () => {
    if (!noteText.trim()) return;
    setNoteSubmitting(true);
    try {
      await onAddInternalNote({ text: noteText.trim(), pinned: notePinned });
      setNoteText('');
      setNotePinned(false);
      await onRefresh();
    } catch (err: any) {
      setLastError(String(err?.message || err || 'error'));
    } finally {
      setNoteSubmitting(false);
    }
  }, [notePinned, noteText, onAddInternalNote, onRefresh]);

  const subject = data?.subject_label || data?.subject_id || '-';
  const assigneeDisplay = form.assignee_label || form.assignee_id || 'Unassigned';

  const header = data ? (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
        <span>Case</span>
        <span className="font-mono text-gray-700 dark:text-gray-300">{data.id}</span>
        {data.status && <Badge color="warning">{data.status}</Badge>}
        {form.type && <Badge color="primary">{form.type}</Badge>}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-base font-semibold text-gray-900 dark:text-gray-50">{form.title || 'Untitled case'}</span>
        {data.severity && <Badge color="error">Severity: {data.severity}</Badge>}
        {data.priority && <Badge color="primary">Priority: {data.priority}</Badge>}
      </div>
    </div>
  ) : (
    'Case preview'
  );

  const footer = data && (
    <div className="flex items-center justify-between gap-2 text-xs text-gray-500">
      <span>Last update: {formatDateTime(data.updated_at) || '-'}</span>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          color="neutral"
          onClick={() => void onRefresh()}
          disabled={loading || saving || noteSubmitting}
        >
          Refresh
        </Button>
        <Button onClick={handleSave} disabled={saving || loading}>
          {saving ? 'Saving...' : 'Save changes'}
        </Button>
      </div>
    </div>
  );

  return (
    <Drawer open={open} onClose={onClose} title={header} widthClass="w-[720px]" footer={footer}>
      <div className="space-y-5 p-4 text-sm">
        {loading && (
          <div className="flex items-center gap-2 text-gray-500">
            <Spinner size="sm" /> Loading case...
          </div>
        )}
        {lastError && (
          <div className="rounded border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">{lastError}</div>
        )}

        {data ? (
          <>
            <Card skin="shadow" className="space-y-4 rounded-3xl bg-white p-5 shadow-sm dark:bg-dark-800">
              <CaseWorkflowControls
                subjectLabel={subject}
                createdAt={formatDateTime(data.created_at)}
                updatedAt={formatDateTime(data.updated_at)}
                typeValue={form.type}
                onTypeChange={(value) => handleFieldChange('type', value)}
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
                title={form.title}
                onTitleChange={(value) => handleFieldChange('title', value)}
                tags={form.tags}
                onTagsChange={handleTagsChange}
                description={form.description}
                onDescriptionChange={(value) => handleFieldChange('description', value)}
                noteText={noteText}
                onNoteTextChange={setNoteText}
                notePinned={notePinned}
                onNotePinnedChange={setNotePinned}
                onNoteSubmit={handleNoteSubmit}
                noteSubmitting={noteSubmitting}
              />
              <div className="mt-4 flex justify-end">
                <Button size="sm" variant="ghost" onClick={() => navigate(`/moderation/cases/${data.id}`)}
                >
                  Open full case
                </Button>
              </div>
            </Card>

            {data.notes && data.notes.length > 0 && (
              <section className="space-y-3">
                <h3 className="text-xs font-semibold uppercase text-gray-500">Latest notes</h3>
                <CaseConversation notes={data.notes} variant="internal" />
              </section>
            )}
          </>
        ) : (
          !loading && <div className="py-12 text-center text-sm text-gray-500">Select a case to see details</div>
        )}
      </div>
    </Drawer>
  );
}

export default CasePreviewDrawer;

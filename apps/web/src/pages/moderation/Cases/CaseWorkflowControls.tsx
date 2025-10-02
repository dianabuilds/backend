import React from 'react';
import { Button, Input, TagInput, Textarea } from "@ui";
import { CASE_PRIORITY_OPTIONS, CASE_SEVERITY_OPTIONS, CASE_STATUS_OPTIONS, CASE_TYPE_OPTIONS } from './constants';
import { CaseAttributeCard } from './CaseAttributeCard';
import { AssigneeSearchSelect } from './AssigneeSearchSelect';
import { QueueSearchSelect } from './QueueSearchSelect';

type AssigneeOption = { id?: string | null; label?: string | null } | null;

type CaseWorkflowControlsProps = {
  status: string;
  severity: string;
  priority: string;
  queue: string;
  assigneeId: string;
  assigneeLabel: string;
  onStatusChange: (value: string) => void;
  onSeverityChange: (value: string) => void;
  onPriorityChange: (value: string) => void;
  onQueueChange: (value: string | null) => void;
  onAssigneeChange: (option: AssigneeOption) => void;
  currentUserId?: string;
  currentUserLabel?: string;
  onSave: () => void;
  onMarkResolved: () => void;
  onMoveToEscalation: () => void;
  saving?: boolean;
  loading?: boolean;
  subjectLabel: string;
  onSubjectClick?: () => void;
  createdAt?: string | null;
  updatedAt?: string | null;
  typeValue: string;
  onTypeChange: (value: string) => void;
  title: string;
  onTitleChange: (value: string) => void;
  tags: string[];
  onTagsChange: (tags: string[]) => void;
  description: string;
  onDescriptionChange: (value: string) => void;
  noteText?: string;
  onNoteTextChange?: (value: string) => void;
  notePinned?: boolean;
  onNotePinnedChange?: (value: boolean) => void;
  onNoteSubmit?: () => void;
  noteSubmitting?: boolean;
};

const STATUS_COLORS: Record<string, string> = {
  open: 'border-amber-200 bg-amber-50 text-amber-900',
  pending: 'border-amber-200 bg-amber-50 text-amber-900',
  in_progress: 'border-sky-200 bg-sky-50 text-sky-900',
  blocked: 'border-rose-200 bg-rose-50 text-rose-900',
  resolved: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  closed: 'border-slate-200 bg-slate-50 text-slate-800',
};

function statusCardClasses(status: string): string {
  return STATUS_COLORS[status] ?? 'border-indigo-200 bg-indigo-50 text-indigo-900';
}

const POPPER_CLASSES =
  'absolute left-0 right-0 top-full z-30 mt-2 rounded-lg border border-gray-200 bg-white p-3 shadow-xl dark:border-dark-500 dark:bg-dark-700';
const CONTROL_CARD_CLASSES = 'rounded-2xl border border-gray-200 bg-white p-3 shadow-sm dark:border-dark-600 dark:bg-dark-700/60';

function renderOptionList(options: string[], current: string, onSelect: (value: string) => void) {
  return (
    <div className="max-h-64 overflow-auto rounded-md border border-gray-200 bg-white shadow-lg dark:border-dark-500 dark:bg-dark-700">
      {options.map((option) => {
        const active = current === option;
        const baseClasses =
          'flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm transition hover:bg-gray-100 dark:hover:bg-dark-600';
        const stateClasses = active
          ? 'font-semibold text-primary-700 dark:text-primary-200'
          : 'text-gray-700 dark:text-gray-100';
        return (
          <button
            key={option || 'not-set'}
            type="button"
            className={`${baseClasses} ${stateClasses}`}
            onClick={() => onSelect(option)}
          >
            <span className="capitalize">{option || 'not set'}</span>
            {active && <span className="text-xs text-primary-600">Selected</span>}
          </button>
        );
      })}
    </div>
  );
}

export function CaseWorkflowControls({
  status,
  severity,
  priority,
  queue,
  assigneeId,
  assigneeLabel,
  onStatusChange,
  onSeverityChange,
  onPriorityChange,
  onQueueChange,
  onAssigneeChange,
  currentUserId,
  currentUserLabel,
  onSave,
  onMarkResolved,
  onMoveToEscalation,
  saving,
  loading,
  subjectLabel,
  onSubjectClick,
  createdAt,
  updatedAt,
  typeValue,
  onTypeChange,
  title,
  onTitleChange,
  tags,
  onTagsChange,
  description,
  onDescriptionChange,
  noteText,
  onNoteTextChange,
  notePinned,
  onNotePinnedChange,
  onNoteSubmit,
  noteSubmitting,
}: CaseWorkflowControlsProps) {
  const [statusOpen, setStatusOpen] = React.useState(false);
  const [severityOpen, setSeverityOpen] = React.useState(false);
  const [priorityOpen, setPriorityOpen] = React.useState(false);
  const [queueOpen, setQueueOpen] = React.useState(false);
  const [assigneeOpen, setAssigneeOpen] = React.useState(false);
  const [typeOpen, setTypeOpen] = React.useState(false);

  const statusRef = React.useRef<HTMLDivElement | null>(null);
  const statusPopoverRef = React.useRef<HTMLDivElement | null>(null);
  const severityRef = React.useRef<HTMLDivElement | null>(null);
  const severityPopoverRef = React.useRef<HTMLDivElement | null>(null);
  const priorityRef = React.useRef<HTMLDivElement | null>(null);
  const priorityPopoverRef = React.useRef<HTMLDivElement | null>(null);
  const queueRef = React.useRef<HTMLDivElement | null>(null);
  const queuePopoverRef = React.useRef<HTMLDivElement | null>(null);
  const assigneeRef = React.useRef<HTMLDivElement | null>(null);
  const assigneePopoverRef = React.useRef<HTMLDivElement | null>(null);
  const typeRef = React.useRef<HTMLDivElement | null>(null);
  const typePopoverRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (statusOpen && !statusRef.current?.contains(target) && !statusPopoverRef.current?.contains(target)) {
        setStatusOpen(false);
      }
      if (severityOpen && !severityRef.current?.contains(target) && !severityPopoverRef.current?.contains(target)) {
        setSeverityOpen(false);
      }
      if (priorityOpen && !priorityRef.current?.contains(target) && !priorityPopoverRef.current?.contains(target)) {
        setPriorityOpen(false);
      }
      if (queueOpen && !queueRef.current?.contains(target) && !queuePopoverRef.current?.contains(target)) {
        setQueueOpen(false);
      }
      if (assigneeOpen && !assigneeRef.current?.contains(target) && !assigneePopoverRef.current?.contains(target)) {
        setAssigneeOpen(false);
      }
      if (typeOpen && !typeRef.current?.contains(target) && !typePopoverRef.current?.contains(target)) {
        setTypeOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [assigneeOpen, priorityOpen, queueOpen, severityOpen, statusOpen, typeOpen]);

  const handleStatusSelect = React.useCallback(
    (value: string) => {
      onStatusChange(value);
      setStatusOpen(false);
    },
    [onStatusChange],
  );

  const handleSeveritySelect = React.useCallback(
    (value: string) => {
      onSeverityChange(value);
      setSeverityOpen(false);
    },
    [onSeverityChange],
  );

  const handlePrioritySelect = React.useCallback(
    (value: string) => {
      onPriorityChange(value);
      setPriorityOpen(false);
    },
    [onPriorityChange],
  );

  const handleQueueSelect = React.useCallback(
    (value: string | null) => {
      onQueueChange(value);
      setQueueOpen(false);
    },
    [onQueueChange],
  );

  const handleAssigneeSelect = React.useCallback(
    (option: AssigneeOption) => {
      onAssigneeChange(option);
      setAssigneeOpen(false);
    },
    [onAssigneeChange],
  );

  const handleAssignSelf = React.useCallback(() => {
    if (!currentUserId) return;
    onAssigneeChange({ id: currentUserId, label: currentUserLabel || currentUserId });
    setAssigneeOpen(false);
  }, [currentUserId, currentUserLabel, onAssigneeChange]);

  const handleTypeSelect = React.useCallback(
    (value: string) => {
      onTypeChange(value);
      setTypeOpen(false);
    },
    [onTypeChange],
  );

  const showNoteCard = Boolean(onNoteTextChange && onNoteSubmit);

  return (
    <section className="space-y-6 text-xs text-gray-500">
      <div className="space-y-3">
        <h3 className="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Overview</h3>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <CaseAttributeCard
            label="Subject"
            value={subjectLabel || '-'}
            hint="Entity under review"
            onClick={onSubjectClick}
            tone={onSubjectClick ? 'highlight' : 'default'}
          />
          <div ref={typeRef} className="relative">
            <CaseAttributeCard
              label="Type"
              value={typeValue || 'Not set'}
              hint="Primary case classification"
              onClick={() => setTypeOpen((prev) => !prev)}
            />
            {typeOpen && (
              <div ref={typePopoverRef} className={POPPER_CLASSES}>
                {renderOptionList(CASE_TYPE_OPTIONS, typeValue, handleTypeSelect)}
              </div>
            )}
          </div>
          <CaseAttributeCard label="Created" value={createdAt || '-'} hint="Initial intake timestamp" tone="muted" />
          <CaseAttributeCard label="Updated" value={updatedAt || '-'} hint="Last change timestamp" tone="muted" />
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Workflow</h3>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div ref={statusRef} className="relative">
            <CaseAttributeCard
              label="Status"
              value={status || 'not set'}
              hint="Click to update workflow state."
              className={statusCardClasses(status)}
              valueClassName="capitalize"
              onClick={() => setStatusOpen((prev) => !prev)}
            />
            {statusOpen && (
              <div ref={statusPopoverRef} className={POPPER_CLASSES}>
                {renderOptionList(CASE_STATUS_OPTIONS, status, handleStatusSelect)}
              </div>
            )}
          </div>

          <div ref={severityRef} className="relative">
            <CaseAttributeCard
              label="Severity"
              value={severity || 'not set'}
              hint="Adjust escalation level."
              valueClassName="capitalize"
              onClick={() => setSeverityOpen((prev) => !prev)}
            />
            {severityOpen && (
              <div ref={severityPopoverRef} className={POPPER_CLASSES}>
                {renderOptionList(CASE_SEVERITY_OPTIONS, severity, handleSeveritySelect)}
              </div>
            )}
          </div>

          <div ref={priorityRef} className="relative">
            <CaseAttributeCard
              label="Priority"
              value={priority || 'not set'}
              hint="Set handling urgency."
              valueClassName="capitalize"
              onClick={() => setPriorityOpen((prev) => !prev)}
            />
            {priorityOpen && (
              <div ref={priorityPopoverRef} className={POPPER_CLASSES}>
                {renderOptionList(CASE_PRIORITY_OPTIONS, priority, handlePrioritySelect)}
              </div>
            )}
          </div>

          <div ref={queueRef} className="relative sm:col-span-2 xl:col-span-1">
            <CaseAttributeCard
              label="Queue"
              value={queue || 'not set'}
              hint="Choose routing lane."
              valueClassName="capitalize"
              onClick={() => setQueueOpen((prev) => !prev)}
            />
            {queueOpen && (
              <div ref={queuePopoverRef} className={POPPER_CLASSES}>
                <QueueSearchSelect value={queue} onChange={handleQueueSelect} onClose={() => setQueueOpen(false)} />
              </div>
            )}
          </div>

          <div ref={assigneeRef} className="relative sm:col-span-2 xl:col-span-4">
            <CaseAttributeCard
              label="Assignee"
              value={assigneeLabel || assigneeId || 'Unassigned'}
              hint="Click to change owner."
              tone="highlight"
              onClick={() => setAssigneeOpen((prev) => !prev)}
              action={
                <Button
                  variant="ghost"
                  color="neutral"
                  size="xs"
                  disabled={!currentUserId}
                  onClick={(event) => {
                    event.stopPropagation();
                    handleAssignSelf();
                  }}
                >
                  Assign to me
                </Button>
              }
            />
            {assigneeOpen && (
              <div ref={assigneePopoverRef} className={POPPER_CLASSES}>
                <AssigneeSearchSelect
                  value={assigneeId}
                  label={assigneeLabel || assigneeId}
                  onChange={handleAssigneeSelect}
                  placeholder="Start typing username or email"
                  onClose={() => setAssigneeOpen(false)}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-[11px] font-semibold uppercase tracking-wide text-gray-500">Case details</h3>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className={`${CONTROL_CARD_CLASSES} sm:col-span-2 xl:col-span-2`}>
            <Input label="Title" value={title} onChange={(event) => onTitleChange(event.target.value)} />
          </div>
          <div className={`${CONTROL_CARD_CLASSES} sm:col-span-2 xl:col-span-2`}>
            <TagInput value={tags} onChange={onTagsChange} label="Tags" placeholder="tag" />
          </div>
          <div className={`${CONTROL_CARD_CLASSES} sm:col-span-2 xl:col-span-4`}>
            <Textarea
              rows={4}
              label="Description"
              value={description}
              onChange={(event) => onDescriptionChange(event.target.value)}
            />
          </div>
          <div className={`${CONTROL_CARD_CLASSES} sm:col-span-2 xl:col-span-4`}>
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500 dark:text-gray-400">
              <span>Tip: Set status to resolved when work is done.</span>
              <div className="flex flex-wrap items-center gap-2">
                <Button onClick={onSave} disabled={saving || loading}>
                  {saving ? 'Saving...' : 'Save changes'}
                </Button>
                <Button variant="ghost" color="neutral" onClick={onMarkResolved}>
                  Mark resolved
                </Button>
                <Button variant="ghost" color="neutral" onClick={onMoveToEscalation}>
                  Move to escalation
                </Button>
              </div>
            </div>
          </div>
          {showNoteCard && (
            <div className={`${CONTROL_CARD_CLASSES} sm:col-span-2 xl:col-span-4`}>
              <div className="space-y-3">
                <Textarea
                  rows={4}
                  placeholder="Internal note..."
                  value={noteText ?? ''}
                  onChange={(event) => onNoteTextChange?.(event.target.value)}
                />
                <label className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                  <input
                    type="checkbox"
                    checked={Boolean(notePinned)}
                    onChange={(event) => onNotePinnedChange?.(event.target.checked)}
                  />
                  Pin note to timeline
                </label>
                <div className="flex items-center justify-end gap-2">
                  <Button
                    variant="ghost"
                    color="neutral"
                    onClick={() => onNoteTextChange?.('')}
                    disabled={noteSubmitting}
                  >
                    Clear
                  </Button>
                  <Button onClick={onNoteSubmit} disabled={noteSubmitting || !(noteText ?? '').trim()}>
                    {noteSubmitting ? 'Adding...' : 'Add note'}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

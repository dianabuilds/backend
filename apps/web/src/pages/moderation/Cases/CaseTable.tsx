import React from 'react';
import clsx from 'clsx';
import { Badge, Button } from '@ui';
import { Table as UITable } from '@ui/table';
import { formatDateTime } from '@shared/utils/format';
import type { ModerationCaseSummary } from './types';

const STATUS_COLORS: Record<string, 'warning' | 'info' | 'success' | 'neutral' | 'error'> = {
  open: 'warning',
  pending: 'info',
  in_progress: 'info',
  blocked: 'error',
  escalated: 'error',
  resolved: 'success',
  closed: 'neutral',
};

const SEVERITY_COLORS: Record<string, 'neutral' | 'warning' | 'error'> = {
  low: 'neutral',
  medium: 'warning',
  high: 'error',
  critical: 'error',
};

const PRIORITY_LABELS: Record<string, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  urgent: 'Urgent',
};

type Props = {
  items: ModerationCaseSummary[];
  onSelect: (item: ModerationCaseSummary) => void;
  selectedId?: string | null;
  selectedIds: Set<string>;
  onToggleSelect: (caseId: string, checked: boolean) => void;
  onToggleAll: (checked: boolean) => void;
  disabled?: boolean;
};

function normalize(value?: unknown, fallback = 'N/A'): string {
  if (value == null) return fallback;
  const text = String(value).trim();
  return text.length ? text : fallback;
}

type SlaDescriptor = {
  label: string;
  tone: 'neutral' | 'success' | 'warning' | 'error';
  helper?: string;
};

function resolveSla(item: ModerationCaseSummary): SlaDescriptor | null {
  const meta = (item.meta ?? {}) as Record<string, unknown>;
  const rawRemaining =
    Number(meta.sla_remaining_minutes ?? meta.sla_due_in_minutes ?? meta.sla_minutes ?? item.sla_remaining_minutes ?? item.sla_due_in_minutes);

  if (Number.isFinite(rawRemaining)) {
    const remaining = Number(rawRemaining);
    if (remaining <= 0) {
      return { label: 'Overdue', tone: 'error', helper: `${Math.abs(remaining)}m over` };
    }
    if (remaining <= 60) {
      return { label: `${remaining}m`, tone: 'warning', helper: 'At risk' };
    }
    return { label: `${remaining}m`, tone: 'success', helper: 'On track' };
  }

  const dueAt = normalize(meta.sla_due_at ?? item.sla_due_at ?? '', '');
  if (dueAt) {
    const dueDate = new Date(dueAt);
    if (!Number.isNaN(dueDate.getTime())) {
      const diffMinutes = Math.floor((dueDate.getTime() - Date.now()) / 60000);
      if (diffMinutes <= 0) {
        return { label: 'Overdue', tone: 'error', helper: formatDateTime(dueAt) };
      }
      if (diffMinutes <= 60) {
        return { label: `${diffMinutes}m`, tone: 'warning', helper: formatDateTime(dueAt) };
      }
      return { label: formatDateTime(dueAt), tone: 'neutral' };
    }
  }

  const status = String(meta.sla_status ?? meta.sla_state ?? '').toLowerCase();
  if (status) {
    if (status.includes('breach')) {
      return { label: 'Breached', tone: 'error' };
    }
    if (status.includes('warning') || status.includes('risk')) {
      return { label: 'At risk', tone: 'warning' };
    }
    if (status.includes('ok') || status.includes('green')) {
      return { label: 'On track', tone: 'success' };
    }
  }

  return null;
}

export function CaseTable({
  items,
  onSelect,
  selectedId,
  selectedIds,
  onToggleSelect,
  onToggleAll,
  disabled,
}: Props) {
  const selectAllRef = React.useRef<HTMLInputElement | null>(null);
  const allSelected = items.length > 0 && items.every((item) => selectedIds.has(item.id));
  const fallbackValue = 'N/A';

  React.useEffect(() => {
    if (!selectAllRef.current) return;
    selectAllRef.current.indeterminate = selectedIds.size > 0 && !allSelected;
  }, [allSelected, selectedIds]);

  return (
    <div className="relative overflow-x-auto rounded-2xl border border-gray-200 dark:border-dark-600">
      <UITable preset="surface" className="min-w-[1000px]" hover headerSticky>
        <UITable.THead>
          <UITable.TR>
            <UITable.TH className="w-12">
              <input
                ref={selectAllRef}
                type="checkbox"
                className="form-checkbox accent-primary-600"
                aria-label="Select all cases"
                checked={allSelected}
                disabled={disabled || items.length === 0}
                onClick={(event) => event.stopPropagation()}
                onChange={(event) => onToggleAll(event.currentTarget.checked)}
              />
            </UITable.TH>
            <UITable.TH className="w-28">Case</UITable.TH>
            <UITable.TH className="min-w-[240px]">Title & Subject</UITable.TH>
            <UITable.TH>Queue</UITable.TH>
            <UITable.TH>Severity</UITable.TH>
            <UITable.TH>Priority</UITable.TH>
            <UITable.TH>SLA</UITable.TH>
            <UITable.TH>Assignee</UITable.TH>
            <UITable.TH>Updated</UITable.TH>
          </UITable.TR>
        </UITable.THead>
        <UITable.TBody>
          {items.length === 0 ? (
            <UITable.Empty
              colSpan={9}
              title="No cases"
              description="Incoming moderation cases will appear here once reported."
            />
          ) : (
            items.map((item) => {
              const isActive = selectedId === item.id;
              const isSelected = selectedIds.has(item.id);
              const statusColor = STATUS_COLORS[String(item.status ?? '').toLowerCase()] ?? 'neutral';
              const severityColor = SEVERITY_COLORS[String(item.severity ?? '').toLowerCase()] ?? 'neutral';
              const priorityLabel = PRIORITY_LABELS[String(item.priority ?? '').toLowerCase()] ?? normalize(item.priority, fallbackValue);
              const sla = resolveSla(item);

              return (
                <UITable.TR
                  key={item.id}
                  className={clsx(
                    'cursor-pointer transition-colors',
                    isActive
                      ? 'bg-primary-50/60 dark:bg-primary-900/20'
                      : isSelected
                      ? 'bg-primary-50/30 dark:bg-primary-900/10'
                      : 'bg-white dark:bg-dark-800',
                  )}
                  onClick={() => onSelect(item)}
                >
                  <UITable.TD className="align-top">
                    <input
                      type="checkbox"
                      className="form-checkbox accent-primary-600"
                      checked={isSelected}
                      disabled={disabled}
                      onClick={(event) => event.stopPropagation()}
                      onChange={(event) => onToggleSelect(item.id, event.currentTarget.checked)}
                    />
                  </UITable.TD>
                  <UITable.TD className="align-top">
                    <div className="flex flex-col gap-1">
                      <Button
                        variant="ghost"
                        color="neutral"
                        size="xs"
                        onClick={(event) => {
                          event.stopPropagation();
                          onSelect(item);
                        }}
                      >
                        {item.id.slice(0, 8)}
                      </Button>
                      {item.status ? <Badge color={statusColor}>{toTitle(String(item.status))}</Badge> : null}
                    </div>
                  </UITable.TD>
                  <UITable.TD className="align-top">
                    <div className="flex flex-col gap-1">
                      <div className="font-medium text-gray-900 dark:text-gray-50">
                        {normalize(item.title, 'Untitled case')}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-dark-200/80">
                        {normalize(item.subject_label ?? item.subject_id ?? '', fallbackValue)}
                      </div>
                      {Array.isArray(item.tags) && item.tags.length ? (
                        <div className="flex flex-wrap gap-1">
                          {item.tags.map((tag) => (
                            <Badge key={tag} color="neutral" variant="outline" className="text-[10px]">
                              #{tag}
                            </Badge>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </UITable.TD>
                  <UITable.TD className="align-top text-sm text-gray-600 dark:text-dark-200/80">
                    {normalize(item.queue, fallbackValue)}
                  </UITable.TD>
                  <UITable.TD className="align-top">
                    {item.severity ? (
                      <Badge color={severityColor} variant="soft" className="capitalize">
                        {toTitle(String(item.severity))}
                      </Badge>
                    ) : (
                      <span className="text-sm text-gray-500 dark:text-dark-300">{fallbackValue}</span>
                    )}
                  </UITable.TD>
                  <UITable.TD className="align-top">
                    <Badge color="info" variant="soft" className="capitalize">
                      {priorityLabel}
                    </Badge>
                  </UITable.TD>
                  <UITable.TD className="align-top">
                    {sla ? (
                      <div className="flex flex-col gap-1">
                        <Badge
                          color={sla.tone === 'error' ? 'error' : sla.tone === 'warning' ? 'warning' : sla.tone === 'success' ? 'success' : 'neutral'}
                          variant="soft"
                        >
                          {sla.label}
                        </Badge>
                        {sla.helper ? (
                          <span className="text-xs text-gray-500 dark:text-dark-200/80">{sla.helper}</span>
                        ) : null}
                      </div>
                    ) : (
                      <span className="text-sm text-gray-500 dark:text-dark-300">{fallbackValue}</span>
                    )}
                  </UITable.TD>
                  <UITable.TD className="align-top text-sm text-gray-600 dark:text-dark-200/80">
                    {normalize(item.assignee_label ?? item.assignee_id, 'Unassigned')}
                  </UITable.TD>
                  <UITable.TD className="align-top text-sm text-gray-600 dark:text-dark-200/80">
                    {formatDateTime(item.updated_at)}
                  </UITable.TD>
                </UITable.TR>
              );
            })
          )}
        </UITable.TBody>
      </UITable>
    </div>
  );
}

function toTitle(value: string): string {
  return value
    .split(/[_\s-]+/)
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(' ');
}

export default CaseTable;

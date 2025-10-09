
import React from 'react';
import { Badge, Button } from '@ui';
import { Table as UITable } from '@ui/table';
import { formatDateTime } from '@shared/utils/format';
import { ModerationCaseSummary } from './types';

type Props = {
  items: ModerationCaseSummary[];
  onSelect: (item: ModerationCaseSummary) => void;
  selectedId?: string | null;
};

export function CaseTable({ items, onSelect, selectedId }: Props) {
  return (
    <div className="relative overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-500">
      <UITable preset="surface" className="min-w-[960px]" hover>
        <UITable.THead>
          <UITable.TR>
            <UITable.TH>ID</UITable.TH>
            <UITable.TH>Title</UITable.TH>
            <UITable.TH>Subject</UITable.TH>
            <UITable.TH>Type</UITable.TH>
            <UITable.TH>Status</UITable.TH>
            <UITable.TH>Queue</UITable.TH>
            <UITable.TH>Severity</UITable.TH>
            <UITable.TH>Priority</UITable.TH>
            <UITable.TH>Assignee</UITable.TH>
            <UITable.TH>Updated</UITable.TH>
          </UITable.TR>
        </UITable.THead>
        <UITable.TBody>
          {items.length === 0 ? (
            <UITable.Empty
              colSpan={10}
              title="No cases"
              description="Incoming moderation cases will appear here once reported."
            />
          ) : (
            items.map((item) => {
              const isActive = selectedId === item.id;
              return (
                <UITable.TR
                  key={item.id}
                  className={`transition ${
                    isActive ? 'bg-primary-50/60 dark:bg-primary-900/20' : 'bg-white dark:bg-dark-800'
                  } hover:bg-primary-50/50 dark:hover:bg-dark-700`}
                >
                  <UITable.TD className="align-top">
                    <Button variant="ghost" color="neutral" size="xs" onClick={() => onSelect(item)}>
                      {item.id.slice(0, 8)}...
                    </Button>
                  </UITable.TD>
                  <UITable.TD className="align-top">
                    <div className="font-medium text-gray-900 dark:text-gray-50">{item.title || 'Untitled'}</div>
                    {Array.isArray(item.tags) && item.tags.length > 0 && (
                      <div className="mt-1 flex flex-wrap gap-1">
                        {item.tags.map((tag) => (
                          <Badge key={tag} variant="soft" color="neutral" className="text-[10px]">
                            #{tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </UITable.TD>
                  <UITable.TD className="align-top text-xs text-gray-500 dark:text-dark-300">
                    {item.subject_label || item.subject_id || '—'}
                  </UITable.TD>
                  <UITable.TD className="align-top text-xs text-gray-500 dark:text-dark-300">{item.type || '—'}</UITable.TD>
                  <UITable.TD className="align-top">
                    <Badge color="warning" className="capitalize">
                      {item.status || '—'}
                    </Badge>
                  </UITable.TD>
                  <UITable.TD className="align-top text-xs text-gray-500 dark:text-dark-300">{item.queue || '—'}</UITable.TD>
                  <UITable.TD className="align-top text-xs text-gray-500 dark:text-dark-300">{item.severity || '—'}</UITable.TD>
                  <UITable.TD className="align-top text-xs text-gray-500 dark:text-dark-300">{item.priority || '—'}</UITable.TD>
                  <UITable.TD className="align-top text-xs text-gray-500 dark:text-dark-300">{item.assignee_id || '—'}</UITable.TD>
                  <UITable.TD className="align-top text-xs text-gray-500 dark:text-dark-300">{formatDateTime(item.updated_at)}</UITable.TD>
                </UITable.TR>
              );
            })
          )}
        </UITable.TBody>
      </UITable>
    </div>
  );
}

export default CaseTable;

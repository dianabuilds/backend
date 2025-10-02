import React from 'react';
import { Badge, Button } from "@ui";
import { formatDateTime } from '../../../shared/utils/format';
import { ModerationCaseSummary } from './types';

type Props = {
  items: ModerationCaseSummary[];
  onSelect: (item: ModerationCaseSummary) => void;
  selectedId?: string | null;
};

export function CaseTable({ items, onSelect, selectedId }: Props) {
  if (!items.length) {
    return <div className="rounded border border-dashed border-gray-300 py-12 text-center text-sm text-gray-500">No cases</div>;
  }

  return (
    <div className="relative overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-500">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-dark-700/40">
          <tr>
            <th className="px-3 py-2 text-left">ID</th>
            <th className="px-3 py-2 text-left">Title</th>
            <th className="px-3 py-2 text-left">Subject</th>
            <th className="px-3 py-2 text-left">Type</th>
            <th className="px-3 py-2 text-left">Status</th>
            <th className="px-3 py-2 text-left">Queue</th>
            <th className="px-3 py-2 text-left">Severity</th>
            <th className="px-3 py-2 text-left">Priority</th>
            <th className="px-3 py-2 text-left">Assignee</th>
            <th className="px-3 py-2 text-left">Updated</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const isActive = selectedId === item.id;
            const className = `border-b border-gray-100 transition hover:bg-primary-50/50 dark:border-dark-600 ${
              isActive ? 'bg-primary-50/60' : 'bg-white dark:bg-dark-800'
            }`;
            return (
              <tr key={item.id} className={className}>
                <td className="px-3 py-2 align-top">
                  <Button variant="ghost" color="neutral" size="xs" onClick={() => onSelect(item)}>
                    {item.id.slice(0, 8)}...
                  </Button>
                </td>
                <td className="px-3 py-2 align-top">
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
                </td>
                <td className="px-3 py-2 align-top text-xs text-gray-500">
                  {item.subject_label || item.subject_id || '-'}
                </td>
                <td className="px-3 py-2 align-top text-xs text-gray-500">{item.type || '-'}</td>
                <td className="px-3 py-2 align-top">
                  <Badge color="warning" className="capitalize">
                    {item.status || '-'}
                  </Badge>
                </td>
                <td className="px-3 py-2 align-top text-xs text-gray-500">{item.queue || '-'}</td>
                <td className="px-3 py-2 align-top text-xs text-gray-500">{item.severity || '-'}</td>
                <td className="px-3 py-2 align-top text-xs text-gray-500">{item.priority || '-'}</td>
                <td className="px-3 py-2 align-top text-xs text-gray-500">{item.assignee_id || '-'}</td>
                <td className="px-3 py-2 align-top text-xs text-gray-500">{formatDateTime(item.updated_at)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default CaseTable;

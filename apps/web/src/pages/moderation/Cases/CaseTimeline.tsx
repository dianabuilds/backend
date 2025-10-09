import React from 'react';
import { CaseEvent, CaseNote } from './types';
import { formatDateTime } from '@shared/utils/format';
import { Badge } from "@ui";

type TimelineItem = (CaseEvent | (CaseNote & { type?: string })) & { id?: string };

type Props = {
  items?: TimelineItem[] | null;
  limit?: number;
  emptyMessage?: string;
};

function eventColor(type?: string | null) {
  const normalized = String(type || '').toLowerCase();
  if (normalized.includes('error') || normalized.includes('fail')) return 'error';
  if (normalized.includes('resolve') || normalized.includes('note')) return 'info';
  if (normalized.includes('create')) return 'primary';
  if (normalized.includes('status')) return 'primary';
  if (normalized.includes('assign')) return 'success';
  return 'neutral';
}

export function CaseTimeline({ items, limit, emptyMessage = 'No events' }: Props) {
  const sliced = React.useMemo(() => {
    if (!Array.isArray(items)) return [];
    const data = items
      .slice()
      .sort((a, b) => {
        const at = a.created_at ? new Date(a.created_at).getTime() : 0;
        const bt = b.created_at ? new Date(b.created_at).getTime() : 0;
        return bt - at;
      });
    return typeof limit === 'number' ? data.slice(0, limit) : data;
  }, [items, limit]);

  if (!sliced.length) {
    return <div className="py-3 text-sm text-gray-500">{emptyMessage}</div>;
  }

  return (
    <ul className="space-y-3 py-3">
      {sliced.map((item) => {
        const key = item.id || `${item.type || 'event'}-${item.created_at || Math.random()}`;
        const title = 'title' in item ? item.title : undefined;
        const text = 'text' in item ? item.text : undefined;
        const description = 'description' in item ? item.description : undefined;
        const actor = (item as any).actor || (item as any).author_id;
        const label = title || (item.type ? item.type : 'Event');
        return (
          <li key={key} className="rounded border border-gray-200 bg-white p-3 text-sm shadow-sm dark:border-dark-600 dark:bg-dark-700/40">
            <div className="mb-1 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge color={eventColor(item.type)}>{label}</Badge>
                {actor && <span className="text-xs text-gray-500">{actor}</span>}
              </div>
              <div className="text-xs text-gray-400">{formatDateTime(item.created_at)}</div>
            </div>
            {text && <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-200">{text}</div>}
            {description && !text && (
              <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-200">{description}</div>
            )}
            {'field' in item && item.field && (
              <div className="mt-2 text-xs text-gray-500">
                {item.field}: {(item as any).from ?? '-'} {'->'} {(item as any).to ?? '-'}
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}

export default CaseTimeline;

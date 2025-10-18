import { Card } from "@ui";
import React from 'react';
import { apiGet } from '@shared/api/client';

const fallback = [
  { id: 'e1', who: 'System', what: 'Initial import', when: 'Just now' },
];

type EditRow = {
  id: string;
  who: string;
  what: string;
  when: string;
};

function formatTimestamp(value?: string | null): string {
  if (!value) return 'Just now';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString();
}

export function Edits() {
  const [edits, setEdits] = React.useState<EditRow[]>(fallback);

  React.useEffect(() => {
    void (async () => {
      try {
        const data = await apiGet<{ items?: any[] }>('/v1/content/edits?limit=5');
        if (Array.isArray(data?.items) && data.items.length) {
          setEdits(
            data.items.map((row) => ({
              id: String(row.id ?? row.uid ?? Math.random()),
              who: row.user?.name || row.user?.id || 'Unknown',
              what: row.action || row.title || 'Updated content',
              when: formatTimestamp(row.when ?? row.updated_at ?? row.updatedAt),
            })),
          );
        }
      } catch (err) {
        console.warn('Failed to load recent edits', err);
      }
    })();
  }, []);

  return (
    <Card className="px-4 pb-4">
      <div className="flex min-w-0 items-center justify-between gap-3 py-3">
        <h2 className="truncate font-medium tracking-wide text-gray-800 dark:text-dark-100">Recent edits</h2>
      </div>
      <ul className="mt-2 space-y-2.5 text-sm">
        {edits.map((edit) => (
          <li key={edit.id} className="flex items-center justify-between gap-3">
            <span className="truncate text-gray-700 dark:text-dark-100">
              <span className="font-medium text-gray-900 dark:text-white">{edit.who}</span> {edit.what}
            </span>
            <span className="whitespace-nowrap text-xs text-gray-400 dark:text-dark-300">{edit.when}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

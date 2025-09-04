import type { ReactNode } from 'react';

export interface SummaryItem {
  label: string;
  value: ReactNode;
  highlight?: boolean;
}

export default function SummaryCard({ title, items }: { title: string; items: SummaryItem[] }) {
  return (
    <div className="rounded border p-3 bg-white shadow-sm dark:bg-gray-900">
      <div className="text-sm text-gray-500 dark:text-gray-400">{title}</div>
      <div className="text-sm mt-2 space-y-1">
        {items.map((it, i) => (
          <div key={i} className={it.highlight ? 'font-semibold text-red-600' : ''}>
            {it.label}: {it.value}
          </div>
        ))}
      </div>
    </div>
  );
}

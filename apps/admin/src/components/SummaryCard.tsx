import type { ReactNode } from "react";

export interface SummaryItem {
  label: string;
  value: ReactNode;
  highlight?: boolean;
}

export default function SummaryCard({
  title,
  items,
}: {
  title: string;
  items: SummaryItem[];
}) {
  return (
    <div className="rounded border p-3">
      <div className="text-sm text-gray-500">{title}</div>
      <div className="text-sm mt-2 space-y-1">
        {items.map((it, i) => (
          <div
            key={i}
            className={it.highlight ? "text-red-600 font-semibold" : ""}
          >
            {it.label}: {it.value}
          </div>
        ))}
      </div>
    </div>
  );
}

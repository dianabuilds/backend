import React from 'react';

export type KPIs = {
  nodes: number;
  quests: number;
  worlds: number;
  published: number;
  drafts: number;
  linksPerObject: number;
};

const fallback: KPIs = {
  nodes: 0,
  quests: 0,
  worlds: 0,
  published: 0,
  drafts: 0,
  linksPerObject: 0,
};

type StatisticsProps = {
  stats: KPIs | null;
};

export function Statistics({ stats }: StatisticsProps) {
  const data = stats ?? fallback;
  const items = [
    { label: 'Nodes', value: data.nodes.toLocaleString() },
    { label: 'Quests', value: data.quests.toLocaleString() },
    { label: 'Worlds', value: data.worlds.toLocaleString() },
    { label: 'Published', value: data.published.toLocaleString() },
    { label: 'Drafts', value: data.drafts.toLocaleString() },
    { label: 'Links / Object', value: data.linksPerObject.toFixed(2) },
  ];

  return (
    <div className="col-span-12 px-4 sm:col-span-5 sm:px-5 lg:col-span-4">
      <div className="grid gap-6 sm:grid-cols-2">
        {items.map((item) => (
          <div key={item.label} className="rounded-2xl border border-gray-200 bg-white/80 p-4 shadow-sm transition dark:border-dark-600 dark:bg-dark-800/70">
            <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">{item.label}</div>
            <div className="mt-2 text-2xl font-semibold text-gray-900 dark:text-white">{item.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
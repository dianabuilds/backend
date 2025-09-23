import { Card } from '../../../shared/ui';
import React from 'react';
import { apiGet } from '../../../shared/api/client';

type TagRow = {
  id: string;
  name: string;
  count: number;
  trend?: number;
};

const fallback: TagRow[] = [
  { id: 't1', name: 'magic', count: 2300 },
  { id: 't2', name: 'npc', count: 1820 },
  { id: 't3', name: 'lore', count: 1204 },
  { id: 't4', name: 'dungeon', count: 980 },
  { id: 't5', name: 'trade', count: 651 },
];

export function TopTags() {
  const [tags, setTags] = React.useState<TagRow[]>(fallback);

  React.useEffect(() => {
    void (async () => {
      try {
        const data = await apiGet<{ items?: any[] }>('/v1/content/tags/top?limit=5');
        if (Array.isArray(data?.items) && data.items.length) {
          setTags(
            data.items.map((item, index) => ({
              id: String(item.id ?? item.slug ?? index),
              name: String(item.name ?? item.slug ?? 'tag'),
              count: Number(item.count ?? item.usage_count ?? 0),
              trend: typeof item.trend === 'number' ? item.trend : 0,
            })),
          );
        }
      } catch (err) {
        console.warn('Failed to load top tags', err);
      }
    })();
  }, []);

  return (
    <Card className="px-4 pb-4">
      <div className="flex min-w-0 items-center justify-between gap-3 py-3">
        <h2 className="truncate font-medium tracking-wide text-gray-800 dark:text-dark-100">Top tags by usage</h2>
      </div>
      <div className="mt-4 flex justify-between text-xs font-semibold uppercase text-gray-400 dark:text-dark-300">
        <span>Tag</span>
        <span>Uses</span>
      </div>
      <div className="mt-2 space-y-2.5">
        {tags.map((tag) => (
          <div key={tag.id} className="flex min-w-0 justify-between gap-4">
            <span className="truncate text-sm font-medium text-gray-800 dark:text-dark-50">#{tag.name}</span>
            <div className="flex items-center gap-1.5">
              <p className="text-sm text-gray-700 dark:text-dark-100">{tag.count.toLocaleString()}</p>
              <span className={`size-3 inline-block rounded-full ${tag.trend && tag.trend < 0 ? 'bg-error' : 'bg-success'}`} />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
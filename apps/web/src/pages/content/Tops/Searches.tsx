import { Card } from '../../../shared/ui';
import React from 'react';
import { apiGet } from '../../../shared/api/client';

type SearchRow = {
  id: string;
  text: string;
  count: number | string;
  up: boolean;
};

const fallback: SearchRow[] = [
  { id: 's1', text: 'arcane ritual', count: '23.1k', up: true },
  { id: 's2', text: 'alchemy', count: '12.2k', up: false },
  { id: 's3', text: 'companion quests', count: '4.1k', up: true },
  { id: 's4', text: 'ancient ruins', count: '1.5k', up: true },
  { id: 's5', text: 'npc shop', count: '322', up: true },
];

export function Searches() {
  const [terms, setTerms] = React.useState<SearchRow[]>(fallback);

  React.useEffect(() => {
    void (async () => {
      try {
        const data = await apiGet<any>('/v1/search/stats/top?limit=5');
        if (Array.isArray(data)) {
          setTerms(
            data.map((row: any, index: number) => ({
              id: String(row.id ?? row.term ?? index),
              text: String(row.term ?? row.q ?? 'search term'),
              count: row.count ?? row.cnt ?? 0,
              up: Boolean(row.trend == null ? true : row.trend >= 0),
            })),
          );
        }
      } catch (err) {
        console.warn('Failed to load search stats', err);
      }
    })();
  }, []);

  return (
    <Card className="px-4 pb-4">
      <div className="flex min-w-0 items-center justify-between gap-3 py-3">
        <h2 className="truncate font-medium tracking-wide text-gray-800 dark:text-dark-100">Trending searches</h2>
      </div>
      <div className="mt-4 flex justify-between text-xs font-semibold uppercase text-gray-400 dark:text-dark-300">
        <span>Query</span>
        <span>Volume</span>
      </div>
      <div className="mt-2 space-y-2.5">
        {terms.map((t) => (
          <div key={t.id} className="flex min-w-0 justify-between gap-4">
            <span className="truncate text-sm font-medium text-gray-800 dark:text-dark-50">{t.text}</span>
            <div className="flex items-center gap-1.5">
              <p className="text-sm text-gray-700 dark:text-dark-100">{typeof t.count === 'number' ? t.count.toLocaleString() : t.count}</p>
              <span className={`size-3 inline-block rounded-full ${t.up ? 'bg-success' : 'bg-error'}`} />
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
import { useEffect, useState } from 'react';

import { getSearchTop, type SearchTopItem } from '../api/search';
import PageLayout from './_shared/PageLayout';

export default function SearchTop() {
  const [items, setItems] = useState<SearchTopItem[]>([]);

  useEffect(() => {
    (async () => {
      try {
        const data = await getSearchTop();
        setItems(data);
      } catch {
        setItems([]);
      }
    })();
  }, []);

  return (
    <PageLayout title="Search queries">
      <table className="min-w-full border text-sm">
        <thead>
          <tr className="text-left">
            <th className="border px-2 py-1">Query</th>
            <th className="border px-2 py-1">Count</th>
            <th className="border px-2 py-1">Results</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.query} className={item.results === 0 ? 'bg-red-50 dark:bg-red-900' : ''}>
              <td className="border px-2 py-1">{item.query}</td>
              <td className="border px-2 py-1 text-center">{item.count}</td>
              <td className="border px-2 py-1 text-center">{item.results}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </PageLayout>
  );
}

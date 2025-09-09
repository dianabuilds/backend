import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { ApiError } from '../api/client';
import { type FeatureFlag, listFlags, updateFlag } from '../api/flags';
import FlagEditModal from '../components/FlagEditModal';
import PageLayout from './_shared/PageLayout';

function ToggleView({ checked }: { checked: boolean }) {
  return (
    <div
      className={`inline-flex items-center px-2 py-1 rounded pointer-events-none ${checked ? 'bg-green-600 text-white' : 'bg-gray-200 dark:bg-gray-800'}`}
      aria-pressed={checked}
    >
      {checked ? 'On' : 'Off'}
    </div>
  );
}

const PAGE_SIZE = 50;

export default function FeatureFlagsPage() {
  const [filter, setFilter] = useState('');
  const [editing, setEditing] = useState<FeatureFlag | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading, error, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useInfiniteQuery({
      queryKey: ['feature-flags', filter],
      queryFn: ({ pageParam = 0 }) =>
        listFlags({
          q: filter || undefined,
          limit: PAGE_SIZE,
          offset: pageParam * PAGE_SIZE,
        }),
      getNextPageParam: (lastPage, pages) =>
        lastPage.length === PAGE_SIZE ? pages.length : undefined,
      initialPageParam: 0,
    });

  const flags = useMemo(() => data?.pages.flat() ?? [], [data]);

  const onSave = async (
    key: string,
    patch: {
      description: string;
      value: boolean;
      audience: FeatureFlag['audience'];
    },
  ) => {
    try {
      await updateFlag(key, patch);
      setEditing(null);
      await queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? typeof e.detail === 'string'
            ? e.detail
            : e.message
          : e instanceof Error
            ? e.message
            : String(e);
      alert(msg);
    }
  };

  return (
    <PageLayout title="Feature Flags" subtitle="Включение/выключение функционала админки">
      {isLoading && <div className="animate-pulse text-sm text-gray-500">Loading...</div>}
      {error && (
        <div className="text-sm text-red-600">
          {error instanceof Error ? error.message : String(error)}
        </div>
      )}
      <div className="mt-4 mb-2">
        <input
          type="text"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter by key"
          aria-label="Filter by key"
          className="px-2 py-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
        />
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left text-gray-500">
            <tr>
              <th className="py-2 pr-4">Key</th>
              <th className="py-2 pr-4">Description</th>
              <th className="py-2 pr-4">Enabled</th>
              <th className="py-2 pr-4">Audience</th>
              <th className="py-2 pr-4">Updated</th>
              <th className="py-2 pr-4">Updated by</th>
            </tr>
          </thead>
          <tbody>
            {flags.map((f) => (
              <tr
                key={f.key}
                className="border-t border-gray-200 dark:border-gray-800 cursor-pointer"
                onClick={() => setEditing(f)}
              >
                <td className="py-2 pr-4 font-mono">{f.key}</td>
                <td className="py-2 pr-4">{f.description || '-'}</td>
                <td className="py-2 pr-4">
                  <ToggleView checked={!!f.value} />
                </td>
                <td className="py-2 pr-4">{f.audience}</td>
                <td className="py-2 pr-4 text-gray-500">
                  {f.updated_at ? new Date(f.updated_at).toLocaleString() : '-'}
                </td>
                <td className="py-2 pr-4 text-gray-500">{f.updated_by || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hasNextPage && (
        <div className="mt-4">
          <button
            className="px-4 py-2 bg-gray-200 rounded"
            onClick={() => fetchNextPage()}
            disabled={isFetchingNextPage}
          >
            {isFetchingNextPage ? 'Loading...' : 'Load more'}
          </button>
        </div>
      )}
      <FlagEditModal flag={editing} onClose={() => setEditing(null)} onSave={onSave} />
    </PageLayout>
  );
}

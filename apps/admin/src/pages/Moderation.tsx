import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { api } from '../api/client';
import { ensureArray } from '../shared/utils';

interface HiddenNode {
  slug: string;
  title: string | null;
  reason: string | null;
  hidden_by: string | null;
  hidden_at: string;
}

async function fetchHiddenNodes(): Promise<HiddenNode[]> {
  const res = await api.get('/admin/moderation/hidden-nodes');
  return ensureArray<HiddenNode>(res.data);
}

export default function Moderation() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['hidden-nodes'],
    queryFn: fetchHiddenNodes,
  });

  const [slug, setSlug] = useState('');
  const [reason, setReason] = useState('');

  const hideMutation = useMutation({
    mutationFn: async () => {
      if (!slug.trim()) return;
      await api.post(`/admin/moderation/nodes/${slug}/hide`, { reason });
    },
    onSuccess: () => {
      setSlug('');
      setReason('');
      queryClient.invalidateQueries({ queryKey: ['hidden-nodes'] });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: async (s: string) => {
      await api.post(`/admin/moderation/nodes/${s}/restore`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hidden-nodes'] });
    },
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Moderation</h1>
      <div className="mb-4 space-x-2">
        <input
          className="border rounded px-2 py-1"
          placeholder="Node slug"
          value={slug}
          onChange={(e) => setSlug(e.target.value)}
        />
        <input
          className="border rounded px-2 py-1"
          placeholder="Reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <button
          className="bg-blue-500 text-white px-3 py-1 rounded"
          onClick={() => hideMutation.mutate()}
        >
          Hide
        </button>
      </div>
      {isLoading && <p>Loading...</p>}
      {error && (
        <p className="text-red-500">{error instanceof Error ? error.message : String(error)}</p>
      )}
      {!isLoading && !error && (
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="border-b">
              <th className="p-2">Slug</th>
              <th className="p-2">Title</th>
              <th className="p-2">Reason</th>
              <th className="p-2">Hidden by</th>
              <th className="p-2">Hidden at</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((n) => (
              <tr key={n.slug} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="p-2 font-mono">{n.slug}</td>
                <td className="p-2">{n.title ?? ''}</td>
                <td className="p-2">{n.reason ?? ''}</td>
                <td className="p-2 font-mono">{n.hidden_by ?? ''}</td>
                <td className="p-2">{new Date(n.hidden_at).toLocaleString()}</td>
                <td className="p-2">
                  <button
                    className="bg-green-500 text-white px-2 py-1 rounded"
                    onClick={() => restoreMutation.mutate(n.slug)}
                  >
                    Restore
                  </button>
                </td>
              </tr>
            ))}
            {data?.length === 0 && (
              <tr>
                <td colSpan={6} className="p-4 text-center text-gray-500">
                  No hidden nodes
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

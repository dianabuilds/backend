import { useCallback, useEffect, useState } from 'react';

import { useAccount } from '../account/AccountContext';
import { api } from '../api/client';
import ErrorBanner from '../components/ErrorBanner';

interface LimitMap {
  [key: string]: number;
}

interface BlockItem {
  id: string;
  user_id: string;
  key: string;
  created_at: string;
}

export default function Limits() {
  const { accountId } = useAccount();
  const [tab, setTab] = useState<'Account' | 'User'>('Account');
  const [userId, setUserId] = useState('');
  const [limits, setLimits] = useState<LimitMap>({});
  const [blocks, setBlocks] = useState<BlockItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadLimits = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const q = tab === 'User' && userId ? `?user_id=${encodeURIComponent(userId)}` : '';
      const res = await api.get<LimitMap>(`/admin/ops/limits${q}`);
      setLimits(res.data || {});
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load limits');
      setLimits({});
    } finally {
      setLoading(false);
    }
  }, [tab, userId]);

  const loadBlocks = async () => {
    try {
      const res = await api.get<BlockItem[]>('/admin/ops/limit-blocks');
      setBlocks(res.data || []);
    } catch {
      setBlocks([]);
    }
  };

  useEffect(() => {
    loadLimits();
  }, [loadLimits, accountId]);

  useEffect(() => {
    loadBlocks();
  }, [accountId]);

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold">Limits</h1>
        <a
          href="https://docs.example.com/limits"
          target="_blank"
          rel="noreferrer"
          className="text-sm text-blue-600 hover:underline"
        >
          Docs
        </a>
      </div>
      <div>
        <div className="border-b flex gap-4">
          <button
            className={`py-2 text-sm ${tab === 'Account' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
            onClick={() => setTab('Account')}
          >
            Account
          </button>
          <button
            className={`py-2 text-sm ${tab === 'User' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
            onClick={() => setTab('User')}
          >
            User
          </button>
        </div>
        <div className="p-4 space-y-2">
          {tab === 'User' && (
            <div className="flex items-center gap-2">
              <input
                className="rounded border px-2 py-1 w-64"
                placeholder="User ID"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
              />
              <button
                onClick={loadLimits}
                disabled={!userId || loading}
                className="px-3 py-1 rounded border"
              >
                Load
              </button>
            </div>
          )}
          {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
          {loading && <div className="text-sm text-gray-500">Loading…</div>}
          {!loading && Object.keys(limits).length > 0 && (
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500">
                  <th className="px-2 py-1">Limit</th>
                  <th className="px-2 py-1">Remaining</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(limits).map(([k, v]) => (
                  <tr key={k} className="border-t">
                    <td className="px-2 py-1">{k}</td>
                    <td className="px-2 py-1">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!loading && Object.keys(limits).length === 0 && (
            <div className="text-sm text-gray-500">no data</div>
          )}
        </div>
      </div>
      <div>
        <h2 className="font-semibold mb-2">Latest blocks</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500">
                <th className="px-2 py-1">Time</th>
                <th className="px-2 py-1">User</th>
                <th className="px-2 py-1">Limit</th>
              </tr>
            </thead>
            <tbody>
              {blocks.map((b) => (
                <tr key={b.id} className="border-t">
                  <td className="px-2 py-1">{new Date(b.created_at).toLocaleString()}</td>
                  <td className="px-2 py-1">{b.user_id}</td>
                  <td className="px-2 py-1">{b.key}</td>
                </tr>
              ))}
              {blocks.length === 0 && (
                <tr>
                  <td className="px-2 py-3 text-gray-500" colSpan={3}>
                    no blocks
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

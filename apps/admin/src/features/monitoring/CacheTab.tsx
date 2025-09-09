import { useEffect, useState } from 'react';

import { api } from '../../api/client';
import Tooltip from '../../components/Tooltip';

interface CacheStats {
  counters: Record<string, Record<string, number>>;
  hot_keys: { key: string; count: number; ttl: number | null }[];
}

function normalizeCacheStats(raw: unknown): CacheStats {
  const obj = (raw && typeof raw === 'object' ? raw : {}) as Record<string, unknown>;
  const counters =
    obj && typeof obj.counters === 'object'
      ? (obj.counters as Record<string, Record<string, number>>)
      : {};
  const hot_keys = Array.isArray(obj?.hot_keys as unknown[])
    ? (obj.hot_keys as CacheStats['hot_keys'])
    : [];
  return { counters, hot_keys };
}

export default function CacheTab() {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [pattern, setPattern] = useState('');
  const [invLoading, setInvLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get('/admin/cache/stats');
      setStats(normalizeCacheStats(res.data));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  const invalidate = async () => {
    setInvLoading(true);
    try {
      await api.post('/admin/cache/invalidate_by_pattern', { pattern });
      setPattern('');
      await load();
      alert('Cache invalidated');
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setInvLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-end gap-2">
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-600 flex items-center gap-1">
            Invalidate by pattern <Tooltip text="Redis key pattern, e.g., nav:*" />
          </label>
          <input
            value={pattern}
            onChange={(e) => setPattern(e.target.value)}
            placeholder="nav:* or *slug*"
            className="border rounded px-2 py-1 w-80"
          />
        </div>
        <button
          onClick={invalidate}
          disabled={!pattern || invLoading}
          className="px-3 py-1 rounded bg-rose-600 text-white disabled:opacity-50"
        >
          {invLoading ? 'Invalidating...' : 'Invalidate'}
        </button>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}

      {stats && (
        <div className="space-y-4">
          <section>
            <h2 className="font-semibold mb-2">Hot keys</h2>
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="p-2 text-left">Key</th>
                  <th className="p-2 text-left">Hits</th>
                  <th className="p-2 text-left">TTL</th>
                </tr>
              </thead>
              <tbody>
                {(stats.hot_keys ?? []).map((k) => (
                  <tr key={k.key} className="border-b">
                    <td className="p-2 font-mono">{k.key}</td>
                    <td className="p-2">{k.count}</td>
                    <td className="p-2">{k.ttl ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section>
            <h2 className="font-semibold mb-2">Counters</h2>
            <div className="space-y-4">
              {Object.entries(stats.counters ?? {}).map(([group, counters]) => (
                <div key={group} className="space-y-2">
                  <h3 className="font-medium">{group}</h3>
                  <div className="grid grid-cols-5 md:grid-cols-3 sm:grid-cols-2 gap-2">
                    {Object.entries(counters ?? {}).map(([name, value]) => (
                      <div key={name} className="p-2 rounded border">
                        <div className="text-xs text-gray-500">{name}</div>
                        <div className="text-sm font-semibold">{value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

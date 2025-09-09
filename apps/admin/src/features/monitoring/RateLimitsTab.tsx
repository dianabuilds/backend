import { useEffect, useState } from 'react';

import { api } from '../../api/client';
import Pill from '../../components/Pill';
import { Card, CardContent } from '../../components/ui/card';

interface RateRules {
  enabled: boolean;
  rules: Record<string, string>;
}
interface RecentHit {
  path: string;
  ip: string;
  rule: string;
  ts: string;
}

type Recent429 = RecentHit[];

export default function RateLimitsTab() {
  const [rules, setRules] = useState<RateRules | null>(null);
  const [recent, setRecent] = useState<Recent429 | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<Record<string, boolean>>({});

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [r, h] = await Promise.all([
        api.get<RateRules>('/admin/ratelimit/rules'),
        api.get<Recent429>('/admin/ratelimit/recent429'),
      ]);
      setRules(r.data || null);
      setDraft(
        ((r.data as { rules?: Record<string, string> } | null)?.rules || {}) as Record<
          string,
          string
        >,
      );
      setRecent(h.data || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const saveRule = async (key: string) => {
    setSaving((s) => ({ ...s, [key]: true }));
    try {
      await api.patch('/admin/ratelimit/rules', { key, rule: draft[key] });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving((s) => ({ ...s, [key]: false }));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const entries = Object.entries(draft);

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">Rate limits</h2>
            {rules && (
              <Pill variant={rules.enabled ? 'ok' : 'warn'} className="text-sm">
                {rules.enabled ? 'Enabled' : 'Disabled'}
              </Pill>
            )}
          </div>
          {loading && <p>Loading...</p>}
          {error && <p className="text-red-600">{error}</p>}
          {rules && (
            <section className="space-y-2">
              {entries.map(([key, value]) => (
                <div key={key} className="flex items-center gap-2">
                  <label className="w-40 text-sm text-gray-600">{key}</label>
                  <input
                    className="border rounded px-2 py-1 w-40"
                    value={value}
                    onChange={(e) => setDraft((d) => ({ ...d, [key]: e.target.value }))}
                    placeholder="5/min, 10/sec"
                  />
                  <button
                    className="px-3 py-1 rounded border"
                    onClick={() => saveRule(key)}
                    disabled={saving[key]}
                  >
                    {saving[key] ? 'Saving...' : 'Save'}
                  </button>
                </div>
              ))}
            </section>
          )}
        </CardContent>
      </Card>
      {recent && (
        <Card>
          <CardContent>
            <h3 className="font-semibold mb-2">Recent 429</h3>
            {recent.length ? (
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="p-2 text-left">Path</th>
                    <th className="p-2 text-left">IP</th>
                    <th className="p-2 text-left">Rule</th>
                    <th className="p-2 text-left">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {recent.map((r, i) => (
                    <tr key={i} className="border-b">
                      <td className="p-2 font-mono">{r.path}</td>
                      <td className="p-2">{r.ip}</td>
                      <td className="p-2">{r.rule}</td>
                      <td className="p-2">{r.ts}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-gray-500">No recent 429 errors.</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

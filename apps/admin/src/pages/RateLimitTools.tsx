import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";

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

export default function RateLimitTools() {
  const [rules, setRules] = useState<RateRules | null>(null);
  const [recent, setRecent] = useState<Recent429 | null>(null);
  const [loading, setLoading] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.get<RateRules>("/admin/ratelimit/rules");
      const hits = await api.get<Recent429>("/admin/ratelimit/recent429");
      setRules(r.data || null);
      setDraft(((r.data as any)?.rules || {}) as Record<string, string>);
      setRecent(hits.data || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const toggle = async () => {
    if (!rules) return;
    setToggling(true);
    try {
      await api.post("/admin/ratelimit/disable", { disabled: rules.enabled });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setToggling(false);
    }
  };

  const entries = useMemo(() => Object.entries(draft), [draft]);

  const counts = useMemo(() => {
    if (!recent) return {} as Record<string, number>;
    return recent.reduce((acc, r) => {
      const p = r.path || "unknown";
      acc[p] = (acc[p] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [recent]);

  const max = useMemo(() => {
    return Object.values(counts).reduce((m, v) => (v > m ? v : m), 1);
  }, [counts]);

  const saveRule = async (key: string) => {
    try {
      await api.patch("/admin/ratelimit/rules", { key, rule: draft[key] });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Rate limit</h1>
      <p className="text-sm text-gray-600 mb-6">
        Manage rate limit rules and inspect recent 429 errors.
      </p>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {rules && (
        <div className="mb-4 flex items-center gap-2">
          <span className="px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-800 text-sm">
            {rules.enabled ? "Enabled" : "Disabled"}
          </span>
          <button
            onClick={toggle}
            disabled={toggling}
            className="px-3 py-1 rounded border"
          >
            {toggling
              ? "Applying..."
              : rules.enabled
                ? "Disable (non-prod only)"
                : "Enable"}
          </button>
        </div>
      )}

      {rules && (
        <section className="mb-6">
          <h2 className="font-semibold mb-2">Rules</h2>
          <div className="space-y-2">
            {entries.map(([key, value]) => (
              <div key={key} className="flex items-center gap-2">
                <label className="w-40 text-sm text-gray-600">{key}</label>
                <input
                  className="border rounded px-2 py-1 w-40"
                  value={value}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, [key]: e.target.value }))
                  }
                  placeholder="5/min, 10/sec, 3/hour"
                />
                <button
                  className="px-3 py-1 rounded border"
                  onClick={() => saveRule(key)}
                >
                  Save
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {recent && (
        <section>
          <h2 className="font-semibold mb-2">Recent 429</h2>
          {recent.length ? (
            <>
              <table className="min-w-full text-sm mb-4">
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
              <div className="flex items-end gap-2 h-32">
                {Object.entries(counts).map(([p, c]) => (
                  <div
                    key={p}
                    className="bg-blue-500 w-8"
                    style={{ height: `${(c / max) * 100}%` }}
                    title={`${p}: ${c}`}
                  />
                ))}
              </div>
            </>
          ) : (
            <p>No recent 429 errors.</p>
          )}
        </section>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { api } from "../api/client";

interface RateRules {
  enabled: boolean;
  rules: Record<string, unknown>;
}
type Recent429 = Array<Record<string, unknown>>;

export default function RateLimitTools() {
  const [rules, setRules] = useState<RateRules | null>(null);
  const [recent, setRecent] = useState<Recent429 | null>(null);
  const [loading, setLoading] = useState(false);
  const [toggling, setToggling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await api.get<RateRules>("/admin/ratelimit/rules");
      const hits = await api.get<Recent429>("/admin/ratelimit/recent429");
      setRules(r.data || null);
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

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Rate limit</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {rules && (
        <div className="mb-4 flex items-center gap-2">
          <span className="px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-800 text-sm">
            {rules.enabled ? "Enabled" : "Disabled"}
          </span>
          <button onClick={toggle} disabled={toggling} className="px-3 py-1 rounded border">
            {toggling ? "Applying..." : rules.enabled ? "Disable (non-prod only)" : "Enable"}
          </button>
        </div>
      )}
      {rules && (
        <section className="mb-6">
          <h2 className="font-semibold mb-2">Rules</h2>
          <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded text-xs overflow-auto">{JSON.stringify(rules.rules, null, 2)}</pre>
        </section>
      )}
      {recent && (
        <section>
          <h2 className="font-semibold mb-2">Recent 429</h2>
          <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded text-xs overflow-auto">{JSON.stringify(recent, null, 2)}</pre>
        </section>
      )}
    </div>
  );
}

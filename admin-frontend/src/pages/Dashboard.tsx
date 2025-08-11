import { useEffect, useState } from "react";
import KpiCard from "../components/KpiCard";

interface DashboardData {
  kpi: {
    active_users_24h: number;
    new_registrations_24h: number;
    active_premium: number;
    nodes_24h: number;
    quests_24h: number;
  };
  latest_nodes: { id: string; title: string }[];
  latest_restrictions: { id: string; user_id: string; reason: string }[];
  system: {
    db_ok: boolean;
    redis_ok: boolean;
    nav_keys: number;
    comp_keys: number;
    sentry_errors?: { id: string; message: string }[];
    version?: string;
  };
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const token = localStorage.getItem("token");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const resp = await fetch("/admin/dashboard", {
          headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        });
        const text = await resp.text();
        if (!resp.ok) throw new Error(text || resp.statusText);
        let d: DashboardData;
        try {
          d = JSON.parse(text) as DashboardData;
        } catch {
          throw new Error("Invalid JSON in response");
        }
        setData(d);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [token]);

  const [invalidateScope, setInvalidateScope] = useState("nav");
  const [invalidateSlug, setInvalidateSlug] = useState("");
  const [invalidateMessage, setInvalidateMessage] = useState<string | null>(null);

  const handleInvalidate = async (e: React.FormEvent) => {
    e.preventDefault();
    setInvalidateMessage(null);
    try {
      const resp = await fetch("/admin/cache/invalidate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ scope: invalidateScope, slug: invalidateSlug || undefined }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      setInvalidateMessage("Invalidated");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setInvalidateMessage(msg);
    }
  };

  const [recomputeLimit, setRecomputeLimit] = useState(10);
  const [recomputeMessage, setRecomputeMessage] = useState<string | null>(null);

  const handleRecompute = async (e: React.FormEvent) => {
    e.preventDefault();
    setRecomputeMessage(null);
    try {
      const resp = await fetch("/admin/embeddings/recompute", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ limit: recomputeLimit }),
      });
      if (!resp.ok) throw new Error(await resp.text());
      setRecomputeMessage("Started");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setRecomputeMessage(msg);
    }
  };

  return (
    <div>
      <h1 className="mb-4 text-2xl font-bold">Dashboard</h1>
      {loading && <p className="text-gray-600 dark:text-gray-400">Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {data && (
        <div className="space-y-8">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
            <KpiCard title="Active users (24h)" value={data.kpi.active_users_24h} />
            <KpiCard title="New registrations (24h)" value={data.kpi.new_registrations_24h} />
            <KpiCard title="Active premium" value={data.kpi.active_premium} />
            <KpiCard title="Nodes created (24h)" value={data.kpi.nodes_24h} />
            <KpiCard title="Quests created (24h)" value={data.kpi.quests_24h} />
          </div>

          <div>
            <h2 className="mb-2 text-xl font-semibold">Latest nodes</h2>
            <ul className="space-y-1">
              {data.latest_nodes.map((n) => (
                <li key={n.id} className="text-gray-700 dark:text-gray-300">
                  {n.title}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="mb-2 text-xl font-semibold">Latest user restrictions</h2>
            <ul className="space-y-1">
              {data.latest_restrictions.map((r) => (
                <li key={r.id} className="text-gray-700 dark:text-gray-300">
                  {r.user_id}: {r.reason}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="mb-2 text-xl font-semibold">System</h2>
            <p className="text-gray-700 dark:text-gray-300">
              DB: {data.system.db_ok ? "OK" : "Fail"}, Redis: {data.system.redis_ok ? "OK" : "Fail"}
            </p>
            <p className="text-gray-700 dark:text-gray-300">
              nav keys: {data.system.nav_keys}, comp keys: {data.system.comp_keys}
            </p>
            {data.system.version && (
              <p className="text-gray-700 dark:text-gray-300">Version: {data.system.version}</p>
            )}
            {data.system.sentry_errors && data.system.sentry_errors.length > 0 && (
              <div className="mt-2">
                <p className="font-medium">Sentry errors:</p>
                <ul className="list-disc pl-5">
                  {data.system.sentry_errors.map((e) => (
                    <li key={e.id} className="text-gray-700 dark:text-gray-300">
                      {e.message}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div>
            <h2 className="mb-2 text-xl font-semibold">Quick actions</h2>
            <div className="mb-4">
              <form onSubmit={handleInvalidate} className="space-y-2">
                <div className="flex items-center gap-2">
                  <select
                    value={invalidateScope}
                    onChange={(e) => setInvalidateScope(e.target.value)}
                    className="rounded border p-1"
                  >
                    <option value="nav">nav</option>
                    <option value="comp">comp</option>
                  </select>
                  <input
                    value={invalidateSlug}
                    onChange={(e) => setInvalidateSlug(e.target.value)}
                    placeholder="slug"
                    className="flex-1 rounded border p-1"
                  />
                  <button
                    type="submit"
                    className="rounded bg-gray-800 px-3 py-1 text-white hover:bg-black dark:bg-gray-700 dark:hover:bg-gray-600"
                  >
                    Invalidate
                  </button>
                </div>
                {invalidateMessage && <p className="text-sm text-gray-600 dark:text-gray-400">{invalidateMessage}</p>}
              </form>
            </div>
            <div>
              <form onSubmit={handleRecompute} className="space-y-2">
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={recomputeLimit}
                    onChange={(e) => setRecomputeLimit(Number(e.target.value))}
                    className="w-24 rounded border p-1"
                  />
                  <button
                    type="submit"
                    className="rounded bg-gray-800 px-3 py-1 text-white hover:bg-black dark:bg-gray-700 dark:hover:bg-gray-600"
                  >
                    Recompute last N nodes
                  </button>
                </div>
                {recomputeMessage && <p className="text-sm text-gray-600 dark:text-gray-400">{recomputeMessage}</p>}
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

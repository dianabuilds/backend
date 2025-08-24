import { useState } from "react";

import { api, ApiError } from "../api/client";
import LimitBadge, {
  handleLimit429,
  refreshLimits,
} from "../components/LimitBadge";

interface RunResponse {
  transitions?: unknown[];
}

export default function Navigation() {
  const [nodeSlug, setNodeSlug] = useState("");
  const [userId, setUserId] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string>("");

  const [scope, setScope] = useState<"all" | "node" | "user">("all");
  const [invNodeSlug, setInvNodeSlug] = useState("");
  const [invUserId, setInvUserId] = useState("");
  const [invLoading, setInvLoading] = useState(false);

  const [pgv, setPgv] = useState<null | boolean>(null);
  const [pgvLoading, setPgvLoading] = useState(false);

  const run = async () => {
    setRunning(true);
    setResult("");
    try {
      const payload: Record<string, unknown> = { node_slug: nodeSlug.trim() };
      if (userId.trim()) payload.user_id = userId.trim();
      const res = await api.post<RunResponse>("/admin/navigation/run", payload);
      const count = Array.isArray(res.data?.transitions)
        ? (res.data?.transitions as unknown[]).length
        : 0;
      setResult(`Generated transitions: ${count}`);
      await refreshLimits();
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 429) {
        const retry = Number(e.headers?.get("Retry-After") || 0);
        await handleLimit429("compass_calls", retry);
        setResult("Rate limit exceeded");
      } else {
        setResult(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setRunning(false);
    }
  };

  const invalidate = async () => {
    setInvLoading(true);
    try {
      const payload: Record<string, unknown> = { scope };
      if (scope === "node") payload.node_slug = invNodeSlug.trim();
      if (scope === "user") payload.user_id = invUserId.trim();
      await api.post("/admin/navigation/cache/invalidate", payload);
      alert("Cache invalidated");
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    } finally {
      setInvLoading(false);
    }
  };

  const checkPgvector = async () => {
    setPgvLoading(true);
    try {
      const res = await api.get<{ enabled: boolean }>(
        "/admin/navigation/pgvector/status",
      );
      setPgv(res.data?.enabled ?? null);
    } catch {
      setPgv(null);
    } finally {
      setPgvLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-2xl font-bold mb-4">Navigation tools</h1>
        <div className="flex flex-col gap-2 max-w-xl">
          <label className="flex flex-col gap-1">
            <span className="text-sm text-gray-600">Node slug</span>
            <input
              value={nodeSlug}
              onChange={(e) => setNodeSlug(e.target.value)}
              className="border rounded px-2 py-1"
              placeholder="node-slug"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-sm text-gray-600">User ID (optional)</span>
            <input
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="border rounded px-2 py-1"
              placeholder="uuid or empty for anon"
            />
          </label>
          <div className="flex items-center gap-2">
            <button
              disabled={!nodeSlug || running}
              onClick={run}
              className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-50"
            >
              {running ? "Running..." : "Run generation"}
            </button>
            <LimitBadge limitKey="compass_calls" />
            <button
              onClick={checkPgvector}
              className="px-3 py-1 rounded border"
            >
              Check pgvector
            </button>
            {pgvLoading ? (
              <span className="text-sm text-gray-500">Checking...</span>
            ) : (
              pgv !== null && (
                <span
                  className={`text-sm ${pgv ? "text-green-600" : "text-yellow-700"}`}
                >
                  pgvector: {pgv ? "enabled" : "disabled"}
                </span>
              )
            )}
          </div>
          {result && <div className="text-sm mt-2">{result}</div>}
        </div>
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">
          Invalidate navigation cache
        </h2>
        <div className="flex flex-col gap-2 max-w-xl">
          <label className="flex items-center gap-2">
            <span>Scope:</span>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as any)}
              className="border rounded px-2 py-1"
            >
              <option value="all">all</option>
              <option value="node">node</option>
              <option value="user">user</option>
            </select>
          </label>
          {scope === "node" && (
            <input
              placeholder="node-slug"
              value={invNodeSlug}
              onChange={(e) => setInvNodeSlug(e.target.value)}
              className="border rounded px-2 py-1"
            />
          )}
          {scope === "user" && (
            <input
              placeholder="user-id"
              value={invUserId}
              onChange={(e) => setInvUserId(e.target.value)}
              className="border rounded px-2 py-1"
            />
          )}
          <button
            onClick={invalidate}
            disabled={invLoading}
            className="px-3 py-1 rounded bg-rose-600 text-white disabled:opacity-50"
          >
            {invLoading ? "Invalidating..." : "Invalidate"}
          </button>
        </div>
      </section>
    </div>
  );
}

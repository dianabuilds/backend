import { useState } from "react";

import { api, ApiError } from "../api/client";
import LimitBadge, { handleLimit429, refreshLimits } from "../components/LimitBadge";

interface RunResponse {
  transitions?: unknown[];
}

export default function Navigation() {
  const [nodeSlug, setNodeSlug] = useState("");
  const [userId, setUserId] = useState("");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<string>("");

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

  return (
    <div>
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
        </div>
        {result && <div className="text-sm mt-2">{result}</div>}
      </div>
    </div>
  );
}


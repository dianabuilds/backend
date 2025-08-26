import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useState } from "react";

import { useWorkspace } from "../workspace/WorkspaceContext";

import { api } from "../api/client";
import { createNode, listNodes } from "../api/nodes";
import KpiCard from "../components/KpiCard";

interface NodeItem {
  id: string;
  type: string;
  status: string;
  updated_at?: string;
  updatedAt?: string;
  created_at?: string;
  createdAt?: string;
}

function Progress({ label, value, limit }: { label: string; value: number; limit: number }) {
  const pct = Math.min(100, Math.round((value / limit) * 100));
  return (
    <div>
      <div className="flex justify-between text-xs">
        <span>{label}</span>
        <span>
          {value}/{limit}
        </span>
      </div>
      <div className="h-2 w-full rounded bg-gray-200">
        <div className="h-2 rounded bg-blue-500" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export default function ContentDashboard() {
  const navigate = useNavigate();
  const { workspaceId } = useWorkspace();
  const [search, setSearch] = useState("");
  const [recomputeLimit, setRecomputeLimit] = useState(10);
  const [recomputeMessage, setRecomputeMessage] = useState<string | null>(null);
  const [rebuildMessage, setRebuildMessage] = useState<string | null>(null);

  const {
    data: nodes = [],
    refetch,
    isLoading,
  } = useQuery<NodeItem[]>({
    queryKey: ["content", "dashboard", "nodes"],
    queryFn: async () => await listNodes(),
  });

  const { data: tags = [] } = useQuery<{ id: string }[]>({
    queryKey: ["content", "dashboard", "tags"],
    queryFn: async () => {
      const res = await api.get<{ id: string }[]>("/admin/tags/list");
      return res.data ?? [];
    },
  });

  const nodesCount = nodes.length;
  const questsCount = nodes.filter((n) => n.type === "quest").length;
  const tagsCount = tags.length;

  const latestEdits = [...nodes]
    .sort(
      (a, b) =>
        new Date(b.updated_at || b.updatedAt || b.created_at || b.createdAt || 0).getTime() -
        new Date(a.updated_at || a.updatedAt || a.created_at || a.createdAt || 0).getTime(),
    )
    .slice(0, 5);

  const lastPublished = nodes
    .filter((n) => n.status === "published")
    .sort(
      (a, b) =>
        new Date(b.updated_at || b.updatedAt || b.created_at || b.createdAt || 0).getTime() -
        new Date(a.updated_at || a.updatedAt || a.created_at || a.createdAt || 0).getTime(),
    )[0];

  const createQuest = async () => {
    const n = await createNode("quest");
    const path = workspaceId
      ? `/nodes/${n.id}?workspace_id=${workspaceId}`
      : `/nodes/${n.id}`;
    navigate(path);
  };

  const createGenericNode = async () => {
    const n = await createNode("other");
    const path = workspaceId
      ? `/nodes/${n.id}?workspace_id=${workspaceId}`
      : `/nodes/${n.id}`;
    navigate(path);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (search.trim()) {
      navigate(`/search?q=${encodeURIComponent(search.trim())}`);
    }
  };

  const handleRecompute = async (e: React.FormEvent) => {
    e.preventDefault();
    setRecomputeMessage(null);
    try {
      await api.post("/admin/embeddings/recompute", { limit: recomputeLimit });
      setRecomputeMessage("Started");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setRecomputeMessage(msg);
    }
  };

  const handleRebuild = async () => {
    setRebuildMessage(null);
    try {
      await api.post("/admin/search/rebuild");
      setRebuildMessage("Started");
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setRebuildMessage(msg);
    }
  };

  const features = ["beta", "premium"];
  const limit = 100;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Content Dashboard</h1>
      {isLoading && <div className="text-sm text-gray-500">Loading…</div>}
      {!isLoading && (
        <>
          {/* Summary */}
          <div>
            <h2 className="mb-2 text-lg font-semibold">Summary</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <KpiCard title="Nodes" value={nodesCount} />
              <KpiCard title="Quests" value={questsCount} />
              <KpiCard title="Tags" value={tagsCount} />
            </div>
            <div className="mt-4 space-y-1 text-sm">
              <div className="font-semibold">Last 5 edits</div>
              <ul className="list-disc pl-5">
                {latestEdits.map((n) => (
                  <li key={n.id}>
                    {n.type} – {n.status}
                  </li>
                ))}
              </ul>
              {lastPublished && (
                <div>
                  Last published: {" "}
                  {new Date(
                    lastPublished.updated_at ||
                      lastPublished.updatedAt ||
                      lastPublished.created_at ||
                      lastPublished.createdAt ||
                      0,
                  ).toLocaleString()}
                </div>
              )}
            </div>
          </div>

          {/* Quick actions */}
          <div>
            <h2 className="mb-2 text-lg font-semibold">Quick actions</h2>
            <div className="mb-2 flex flex-wrap gap-2">
              <button className="rounded border px-2 py-1 text-sm" onClick={createQuest}>
                Create quest
              </button>
              <button className="rounded border px-2 py-1 text-sm" onClick={createGenericNode}>
                Create node
              </button>
              <button
                className="rounded border px-2 py-1 text-sm"
                onClick={() => navigate("/content/all")}
              >
                Import/Export
              </button>
            </div>
            <form onSubmit={handleSearch} className="flex gap-2">
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search content"
                className="flex-1 rounded border px-2 py-1 text-sm"
              />
              <button type="submit" className="rounded border px-3 py-1 text-sm">
                Search
              </button>
            </form>
          </div>

          {/* Limits and features */}
          <div>
            <h2 className="mb-2 text-lg font-semibold">Limits & features</h2>
            <div className="mb-2 flex flex-wrap gap-2">
              {features.map((f) => (
                <span key={f} className="rounded bg-gray-200 px-2 py-1 text-xs">
                  {f}
                </span>
              ))}
            </div>
            <div className="space-y-2">
              <Progress label="Nodes" value={nodesCount} limit={limit} />
              <Progress label="Quests" value={questsCount} limit={limit} />
              <Progress label="Tags" value={tagsCount} limit={limit} />
            </div>
          </div>

          {/* Maintenance */}
          <div>
            <h2 className="mb-2 text-lg font-semibold">Maintenance</h2>
            <form onSubmit={handleRecompute} className="mb-2 flex items-center gap-2">
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
                Recompute embeddings
              </button>
              {recomputeMessage && (
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {recomputeMessage}
                </span>
              )}
            </form>
            <div className="flex items-center gap-2">
              <button
                onClick={handleRebuild}
                className="rounded bg-gray-800 px-3 py-1 text-white hover:bg-black dark:bg-gray-700 dark:hover:bg-gray-600"
              >
                Rebuild index
              </button>
              {rebuildMessage && (
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {rebuildMessage}
                </span>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}


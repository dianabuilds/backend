import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { useToast } from "../components/ToastProvider";
import WorkspaceControlPanel from "../components/WorkspaceControlPanel";
import { useWorkspace } from "../workspace/WorkspaceContext";

interface QuestItem {
  id: string;
  title: string;
  subtitle?: string | null;
  description?: string | null;
  cover_image?: string | null;
  tags?: string[] | null;
  price?: number | null;
  is_premium_only?: boolean;
  allow_comments?: boolean;
  is_draft?: boolean;
  is_deleted?: boolean;
  author_id: string;
  created_at: string;
  published_at?: string | null;
}

function ensureArray<T = any>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as any;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (Array.isArray(obj.data)) return obj.data as T[];
  }
  return [];
}

async function fetchQuests(
  params: Record<string, string>,
): Promise<QuestItem[]> {
  const qs = new URLSearchParams(params).toString();
  const res = await api.get(`/admin/quests?${qs}`);
  return ensureArray<QuestItem>(res.data);
}

async function publishQuest(id: string): Promise<QuestItem> {
  const res = await api.post(`/quests/${id}/publish`, {});
  return res.data as QuestItem;
}

export default function Quests() {
  const { addToast } = useToast();
  const { workspaceId } = useWorkspace();
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [authorRole, setAuthorRole] = useState<string>(""); // any|admin|moderator|user
  const [status, setStatus] = useState<string>("draft"); // any|draft|published
  const [publishing, setPublishing] = useState<string | null>(null);

  const queryParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (q) p.q = q;
    if (authorRole) p.author_role = authorRole;
    if (status === "draft") p.draft = "true";
    else if (status === "published") p.draft = "false";
    return p;
  }, [q, authorRole, status]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["quests-admin", queryParams],
    queryFn: () => fetchQuests(queryParams),
  });

  const handlePublish = async (id: string) => {
    setPublishing(id);
    try {
      const q = await publishQuest(id);
      addToast({
        title: "Quest published",
        description: q.title,
        variant: "success",
      });
      qc.invalidateQueries({ queryKey: ["quests-admin"] });
    } catch (e) {
      addToast({
        title: "Failed to publish quest",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    } finally {
      setPublishing(null);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Quests</h1>

      <WorkspaceControlPanel />

      <div className="mb-4 flex items-end gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search..."
          className="border rounded px-2 py-1"
        />
        <label className="flex items-center gap-2 text-sm">
          <span>Author role</span>
          <select
            value={authorRole}
            onChange={(e) => setAuthorRole(e.target.value)}
            className="border rounded px-2 py-1"
          >
            <option value="">any</option>
            <option value="admin">admin</option>
            <option value="moderator">moderator</option>
            <option value="user">user</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <span>Status</span>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="border rounded px-2 py-1"
          >
            <option value="any">any</option>
            <option value="draft">draft</option>
            <option value="published">published</option>
          </select>
        </label>
        <Link
          className="px-3 py-1 rounded bg-blue-600 text-white"
          to="/nodes/new"
        >
          Create quest
        </Link>
      </div>

      {isLoading && <p>Loading…</p>}
      {error && <p className="text-red-600">{(error as Error).message}</p>}
      {!isLoading && !error && (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">Title</th>
              <th className="p-2 text-left">Author</th>
              <th className="p-2 text-left">Price</th>
              <th className="p-2 text-left">Premium</th>
              <th className="p-2 text-left">Status</th>
              <th className="p-2 text-left">Created</th>
              <th className="p-2 text-left">Published</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(data || []).map((q) => (
              <tr key={q.id} className="border-b">
                <td className="p-2">{q.title}</td>
                <td className="p-2 font-mono">{q.author_id}</td>
                <td className="p-2">{q.price ?? 0}</td>
                <td className="p-2">{q.is_premium_only ? "yes" : "no"}</td>
                <td className="p-2">{q.is_draft ? "Draft" : "Published"}</td>
                <td className="p-2">
                  {new Date(q.created_at).toLocaleString()}
                </td>
                <td className="p-2">
                  {q.published_at
                    ? new Date(q.published_at).toLocaleString()
                    : "-"}
                </td>
                <td className="p-2 space-x-2">
                  <a
                    href={`/transitions/trace?start=${encodeURIComponent(q.id)}&workspace=${workspaceId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-2 py-1 border rounded"
                  >
                    Trace candidates
                  </a>
                  {q.is_draft && (
                    <>
                      <button
                        className="px-2 py-1 rounded border"
                        onClick={() => handlePublish(q.id)}
                        disabled={publishing === q.id}
                      >
                        {publishing === q.id ? "Publishing..." : "Publish"}
                      </button>
                      <button
                        className="px-2 py-1 rounded border"
                        onClick={() => handlePublish(q.id)}
                        disabled={publishing === q.id}
                      >
                        {publishing === q.id
                          ? "Publishing..."
                          : "Publish & notify"}
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
            {(!data || data.length === 0) && (
              <tr>
                <td className="p-2 text-gray-500" colSpan={8}>
                  No quests
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

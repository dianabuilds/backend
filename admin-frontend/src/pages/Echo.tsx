import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

interface EchoTrace {
  id: string;
  from_slug: string;
  to_slug: string;
  user_id?: string | null;
  source?: string | null;
  channel?: string | null;
  created_at: string;
}

async function fetchEcho(page: number): Promise<EchoTrace[]> {
  const token = localStorage.getItem("token") || "";
  const resp = await fetch(`/admin/echo?page=${page}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error("Failed to load echoes");
  return resp.json();
}

async function deleteEcho(id: string) {
  const token = localStorage.getItem("token") || "";
  const resp = await fetch(`/admin/echo/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error("Failed to delete");
}

async function anonymizeEcho(id: string) {
  const token = localStorage.getItem("token") || "";
  const resp = await fetch(`/admin/echo/${id}/anonymize`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) throw new Error("Failed to anonymize");
}

async function recomputePopularity(slugs: string[]) {
  const token = localStorage.getItem("token") || "";
  const resp = await fetch(`/admin/echo/recompute_popularity`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ node_slugs: slugs.length ? slugs : undefined }),
  });
  if (!resp.ok) throw new Error("Failed to recompute");
}

export default function Echo() {
  const [page, setPage] = useState(1);
  const [recomputeInput, setRecomputeInput] = useState("");
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["echo", page],
    queryFn: () => fetchEcho(page),
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["echo"] });

  const handleDelete = async (id: string) => {
    await deleteEcho(id);
    refresh();
  };

  const handleAnon = async (id: string) => {
    await anonymizeEcho(id);
    refresh();
  };

  const handleRecompute = async () => {
    const slugs = recomputeInput.split(",").map((s) => s.trim()).filter(Boolean);
    await recomputePopularity(slugs);
    setRecomputeInput("");
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Echo Traces</h1>
      <div className="mb-4 flex items-center gap-2">
        <input
          type="text"
          placeholder="node slugs (comma separated)"
          value={recomputeInput}
          onChange={(e) => setRecomputeInput(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <button
          onClick={handleRecompute}
          className="px-3 py-1 bg-blue-600 text-white rounded"
        >
          Recompute popularity
        </button>
      </div>
      {isLoading && <p>Loading...</p>}
      {error && <p className="text-red-500">Error loading traces</p>}
      {!isLoading && !error && (
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="border-b">
              <th className="p-2">From</th>
              <th className="p-2">To</th>
              <th className="p-2">User</th>
              <th className="p-2">Source</th>
              <th className="p-2">Channel</th>
              <th className="p-2">Created</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((t) => (
              <tr key={t.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="p-2">{t.from_slug}</td>
                <td className="p-2">{t.to_slug}</td>
                <td className="p-2">{t.user_id ?? "anon"}</td>
                <td className="p-2">{t.source ?? ""}</td>
                <td className="p-2">{t.channel ?? ""}</td>
                <td className="p-2">{new Date(t.created_at).toLocaleString()}</td>
                <td className="p-2 space-x-2">
                  <button onClick={() => handleAnon(t.id)} className="text-blue-600">Anon</button>
                  <button onClick={() => handleDelete(t.id)} className="text-red-600">Del</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="mt-4 flex gap-2">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="px-3 py-1 border rounded"
        >
          Prev
        </button>
        <span>Page {page}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          className="px-3 py-1 border rounded"
        >
          Next
        </button>
      </div>
    </div>
  );
}

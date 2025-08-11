import { useEffect, useState } from "react";
import { api } from "../api/client";

type NodeItem = Record<string, any>;

function ensureArray<T = any>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as any;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (Array.isArray(obj.data)) return obj.data as T[];
  }
  return [];
}

export default function Nodes() {
  const [items, setItems] = useState<NodeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = q ? `?q=${encodeURIComponent(q)}` : "";
      const res = await api.get(`/admin/nodes${qs}`);
      setItems(ensureArray<NodeItem>(res.data));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Nodes</h1>
      <div className="mb-4 flex items-center gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by slug..." className="border rounded px-2 py-1" />
        <button onClick={load} className="px-3 py-1 rounded border">Search</button>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="border-b">
              <th className="p-2">ID</th>
              <th className="p-2">Slug</th>
              <th className="p-2">Status</th>
              <th className="p-2">Created</th>
              <th className="p-2">Updated</th>
            </tr>
          </thead>
          <tbody>
            {items.map((n, i) => (
              <tr key={n.id ?? i} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="p-2 font-mono">{n.id ?? "-"}</td>
                <td className="p-2">{n.slug ?? n.name ?? "-"}</td>
                <td className="p-2">{n.status ?? n.state ?? "-"}</td>
                <td className="p-2">{n.created_at ? new Date(n.created_at).toLocaleString() : "-"}</td>
                <td className="p-2">{n.updated_at ? new Date(n.updated_at).toLocaleString() : "-"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={5} className="p-4 text-center text-gray-500">No nodes found</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

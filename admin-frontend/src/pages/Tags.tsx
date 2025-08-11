import { useEffect, useState } from "react";
import { api } from "../api/client";

type TagItem = Record<string, any>;

function ensureArray<T = any>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as any;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (Array.isArray(obj.data)) return obj.data as T[];
  }
  return [];
}

export default function Tags() {
  const [items, setItems] = useState<TagItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = q ? `?q=${encodeURIComponent(q)}` : "";
      const res = await api.get(`/admin/tags${qs}`);
      setItems(ensureArray<TagItem>(res.data));
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
      <h1 className="text-2xl font-bold mb-4">Tags</h1>
      <div className="mb-4 flex items-center gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by tag name..." className="border rounded px-2 py-1" />
        <button onClick={load} className="px-3 py-1 rounded border">Search</button>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="border-b">
              <th className="p-2">ID</th>
              <th className="p-2">Name</th>
              <th className="p-2">Usage</th>
              <th className="p-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t, i) => (
              <tr key={t.id ?? i} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="p-2 font-mono">{t.id ?? "-"}</td>
                <td className="p-2">{t.name ?? t.slug ?? "-"}</td>
                <td className="p-2">{t.usage_count ?? t.count ?? "-"}</td>
                <td className="p-2">{t.created_at ? new Date(t.created_at).toLocaleString() : "-"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="p-4 text-center text-gray-500">No tags found</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getBlacklist,
  addToBlacklist,
  removeFromBlacklist,
  type BlacklistItem,
  listAdminTags,
  createAdminTag,
  deleteAdminTag,
} from "../api/tags";

type TagItem = {
  id?: string;
  slug?: string;
  name?: string;
  usage_count?: number;
  aliases_count?: number;
  created_at?: string;
};

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

  // pagination
  const [limit, setLimit] = useState<number>(50);
  const [offset, setOffset] = useState<number>(0);

  // create form
  const [newSlug, setNewSlug] = useState("");
  const [newName, setNewName] = useState("");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listAdminTags({ q, limit, offset });
      setItems(ensureArray<TagItem>(rows));
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
  }, [limit, offset]);

  const navigate = useNavigate();

  const [blItems, setBlItems] = useState<BlacklistItem[]>([]);
  const [blSlug, setBlSlug] = useState("");
  const [blReason, setBlReason] = useState("");

  const loadBlacklist = async () => {
    try {
      const rows = await getBlacklist();
      setBlItems(rows);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    loadBlacklist();
  }, []);

  const handleSearch = async () => {
    setOffset(0);
    await load();
  };

  const hasPrev = offset > 0;
  const hasNext = items.length >= limit;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Tags</h1>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search by tag name..."
          className="border rounded px-2 py-1"
        />
        <button onClick={handleSearch} className="px-3 py-1 rounded border">
          Search
        </button>
        <button onClick={() => navigate("/tags/merge")} className="px-3 py-1 rounded border">
          Merge…
        </button>
        <div className="ml-auto flex items-center gap-2">
          <label className="text-sm text-gray-600">Page size</label>
          <input
            type="number"
            min={1}
            max={1000}
            value={limit}
            onChange={(e) => setLimit(Math.max(1, Math.min(1000, Number(e.target.value) || 1)))}
            className="w-20 border rounded px-2 py-1"
          />
          <button
            className="px-2 py-1 rounded border"
            disabled={!hasPrev}
            onClick={() => setOffset(Math.max(0, offset - limit))}
            title="Previous page"
          >
            ‹ Prev
          </button>
          <button
            className="px-2 py-1 rounded border"
            disabled={!hasNext}
            onClick={() => setOffset(offset + limit)}
            title="Next page"
          >
            Next ›
          </button>
        </div>
      </div>

      <div className="mb-6 rounded border p-3">
        <h2 className="font-semibold mb-2">Create tag</h2>
        <div className="flex flex-wrap items-center gap-2">
          <input
            className="border rounded px-2 py-1"
            placeholder="slug"
            value={newSlug}
            onChange={(e) => setNewSlug(e.target.value)}
          />
          <input
            className="border rounded px-2 py-1 w-64"
            placeholder="name"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <button
            className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
            onClick={async () => {
              const slug = newSlug.trim();
              const name = newName.trim();
              if (!slug || !name) return;
              try {
                await createAdminTag(slug, name);
                setNewSlug("");
                setNewName("");
                // refresh from first page to show newly created tag more likely
                setOffset(0);
                await load();
              } catch (e) {
                setError(e instanceof Error ? e.message : String(e));
              }
            }}
          >
            Create
          </button>
        </div>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <>
          <table className="min-w-full text-sm text-left mb-6">
            <thead>
              <tr className="border-b">
                <th className="p-2">ID</th>
                <th className="p-2">Name</th>
                <th className="p-2">Aliases</th>
                <th className="p-2">Usage</th>
                <th className="p-2">Created</th>
                <th className="p-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((t, i) => (
                <tr key={t.id ?? `${t.slug}-${i}`} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="p-2 font-mono">{t.id || "—"}</td>
                  <td className="p-2">{t.name || t.slug || "—"}</td>
                  <td className="p-2">{typeof t.aliases_count === "number" ? t.aliases_count : "—"}</td>
                  <td className="p-2">{typeof t.usage_count === "number" ? t.usage_count : "—"}</td>
                  <td className="p-2">{t.created_at ? new Date(t.created_at).toLocaleString() : "—"}</td>
                  <td className="p-2 text-right">
                    <button
                      className="px-2 py-1 rounded border text-red-600 border-red-300"
                      onClick={async () => {
                        if (!t.id) return;
                        const ok = window.confirm(`Delete tag "${t.name || t.slug}"? This cannot be undone.`);
                        if (!ok) return;
                        try {
                          await deleteAdminTag(t.id);
                          await load();
                        } catch (e) {
                          setError(e instanceof Error ? e.message : String(e));
                        }
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={6} className="p-4 text-center text-gray-500">
                    No tags found
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          <div className="rounded border p-3">
            <h2 className="font-semibold mb-2">Blacklist</h2>
            <div className="flex items-center gap-2 mb-3">
              <input
                className="border rounded px-2 py-1"
                placeholder="tag slug…"
                value={blSlug}
                onChange={(e) => setBlSlug(e.target.value)}
              />
              <input
                className="border rounded px-2 py-1 w-64"
                placeholder="reason (optional)"
                value={blReason}
                onChange={(e) => setBlReason(e.target.value)}
              />
              <button
                className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
                onClick={async () => {
                  if (!blSlug.trim()) return;
                  await addToBlacklist(blSlug.trim(), blReason.trim() || undefined);
                  setBlSlug("");
                  setBlReason("");
                  await loadBlacklist();
                }}
              >
                Add
              </button>
            </div>
            <table className="min-w-full text-sm text-left">
              <thead>
                <tr className="border-b">
                  <th className="p-2">Slug</th>
                  <th className="p-2">Reason</th>
                  <th className="p-2">Created</th>
                  <th className="p-2"></th>
                </tr>
              </thead>
              <tbody>
                {blItems.map((b) => (
                  <tr key={b.slug} className="border-b">
                    <td className="p-2 font-mono">{b.slug}</td>
                    <td className="p-2">{b.reason || "—"}</td>
                    <td className="p-2">{new Date(b.created_at).toLocaleString()}</td>
                    <td className="p-2 text-right">
                      <button
                        className="px-2 py-1 rounded border text-red-600 border-red-300"
                        onClick={async () => {
                          await removeFromBlacklist(b.slug);
                          await loadBlacklist();
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
                {blItems.length === 0 && (
                  <tr>
                    <td className="p-4 text-center text-gray-500" colSpan={4}>
                      No blacklist entries
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import NodeEditorModal, { type NodeEditorData } from "../components/NodeEditorModal";

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

function makeDraft(): NodeEditorData {
  return {
    id: `draft-${Date.now()}`,
    title: "",
    subtitle: "",
    cover_image: null,
    tags: [],
    allow_comments: true,
    is_premium_only: false,
    contentData: { time: Date.now(), blocks: [{ type: "paragraph", data: { text: "" } }], version: "2.30.7" },
  };
}

export default function Nodes() {
  const [items, setItems] = useState<NodeItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  // Создание ноды
  const [editorOpen, setEditorOpen] = useState(false);
  const [draft, setDraft] = useState<NodeEditorData>(makeDraft());

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

  const canSave = useMemo(() => !!draft.title.trim(), [draft.title]);

  const doCreate = async () => {
    if (!canSave) return;
    const payload: Record<string, any> = {
      title: draft.title,
      content_format: "rich_json",              // Editor.js -> rich_json
      content: draft.contentData,               // имя поля content
      media: draft.cover_image ? [draft.cover_image] : undefined,
      tags: (draft.tags && draft.tags.length > 0) ? draft.tags : undefined,
      allow_feedback: draft.allow_comments ?? true,
      premium_only: draft.is_premium_only ?? false,
      meta: draft.subtitle ? { subtitle: draft.subtitle } : undefined,
    };
    const res = await api.post("/nodes", payload);
    return res.data as any;
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Nodes</h1>
      <div className="mb-4 flex items-center gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by slug..." className="border rounded px-2 py-1" />
        <button onClick={load} className="px-3 py-1 rounded border">Search</button>
        <button
          className="ml-auto px-3 py-1 rounded bg-blue-600 text-white"
          onClick={() => {
            setDraft(makeDraft());
            setEditorOpen(true);
          }}
        >
          Create node
        </button>
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

      {/* Модалка создания ноды */}
      <NodeEditorModal
        open={editorOpen}
        node={editorOpen ? draft : null}
        onChange={(patch) => setDraft((d) => ({ ...d, ...patch }))}
        onClose={() => setEditorOpen(false)}
        onCommit={async (action) => {
          try {
            await doCreate();
            if (action === "next") {
              // остаться в модалке с пустым черновиком
              setDraft(makeDraft());
            } else {
              setEditorOpen(false);
            }
            await load();
          } catch (e) {
            // Ошибка покажется в тостах на уровне api.request, если настроено. Здесь тихо закроем/оставим.
            console.error(e);
          }
        }}
      />
    </div>
  );
}

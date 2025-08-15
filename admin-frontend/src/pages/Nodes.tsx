import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import NodeEditorModal, { type NodeEditorData } from "../components/NodeEditorModal";
import { useToast } from "../components/ToastProvider";

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
    cover_url: null,
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
  const { addToast } = useToast();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [q, setQ] = useState("");
  const [page, setPage] = useState(0);
  const limit = 25;
  const [hasMore, setHasMore] = useState(false);

  // Создание ноды
  const [editorOpen, setEditorOpen] = useState(false);
  const [draft, setDraft] = useState<NodeEditorData>(makeDraft());

  const load = async (pageIndex = page) => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {
        limit: String(limit),
        offset: String(pageIndex * limit),
      };
      if (q) params.q = q;
      const qs = new URLSearchParams(params).toString();
      const res = await api.get(`/admin/nodes?${qs}`);
      const arr = ensureArray<NodeItem>(res.data);
      setItems(arr);
      setHasMore(arr.length === limit);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      addToast({ title: "Failed to load nodes", description: msg, variant: "error" });
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const canSave = useMemo(() => !!draft.title.trim(), [draft.title]);

  const doCreate = async () => {
    if (!canSave) return;
    // Отправляем только то, что действительно нужно
    const payload: Record<string, any> = {
      title: draft.title.trim(),
      content: draft.contentData, // Editor.js JSON
      // Совместимость алиасов на бэкенде:
      // allow_comments -> allow_feedback, is_premium_only -> premium_only
      allow_comments: draft.allow_comments,
      is_premium_only: draft.is_premium_only,
      tags: Array.isArray(draft.tags) ? draft.tags : [],
    } as Record<string, any>;
    const blocks = Array.isArray(draft.contentData?.blocks) ? draft.contentData.blocks : [];
    const media = blocks
      .filter((b: any) => b.type === "image" && b.data?.file?.url)
      .map((b: any) => String(b.data.file.url));
    if (media.length) payload.media = media;
    if (draft.cover_url || media.length) payload.cover_url = draft.cover_url || media[0];
    const res = await api.post("/nodes", payload);
    return res.data as any;
  };

  const toggleSelect = (id: string) => {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const clearSelection = () => setSelected(new Set());

  const doOp = async (ids: string[], op: string) => {
    try {
      await api.post("/admin/nodes/bulk", { ids, op });
      addToast({ title: "Nodes updated", variant: "success" });
      await load();
    } catch (e) {
      addToast({ title: "Operation failed", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const handleToggle = async (id: string, field: string, current: boolean) => {
    const opMap: Record<string, string> = {
      is_visible: current ? "hide" : "show",
      is_public: current ? "private" : "public",
      premium_only: "toggle_premium",
      is_recommendable: "toggle_recommendable",
    };
    const op = opMap[field];
    if (!op) return;
    await doOp([id], op);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Nodes</h1>
      <div className="mb-4 flex items-center gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by slug..." className="border rounded px-2 py-1" />
        <button
          onClick={() => {
            setPage(0);
            load(0);
          }}
          className="px-3 py-1 rounded border"
        >
          Search
        </button>
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
      {selected.size > 0 && (
        <div className="mb-2 flex gap-2">
          <span className="self-center text-sm">Selected {selected.size}</span>
          <button className="px-2 py-1 border rounded" onClick={() => doOp(Array.from(selected), "hide")}>Hide</button>
          <button className="px-2 py-1 border rounded" onClick={() => doOp(Array.from(selected), "show")}>Show</button>
          <button className="px-2 py-1 border rounded" onClick={() => doOp(Array.from(selected), "public")}>Public</button>
          <button className="px-2 py-1 border rounded" onClick={() => doOp(Array.from(selected), "private")}>Private</button>
          <button className="px-2 py-1 border rounded" onClick={() => doOp(Array.from(selected), "toggle_premium")}>Toggle premium</button>
          <button className="px-2 py-1 border rounded" onClick={() => doOp(Array.from(selected), "toggle_recommendable")}>Toggle recommendable</button>
          <button className="ml-auto px-2 py-1 border rounded" onClick={clearSelection}>Clear</button>
        </div>
      )}
      {!loading && !error && (
        <>
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="border-b">
              <th className="p-2"><input type="checkbox" checked={items.length>0 && selected.size===items.length} onChange={(e)=>setSelected(e.target.checked?new Set(items.map(i=>i.id)):new Set())} /></th>
              <th className="p-2">ID</th>
              <th className="p-2">Slug</th>
              <th className="p-2">Status</th>
              <th className="p-2">Visible</th>
              <th className="p-2">Public</th>
              <th className="p-2">Premium</th>
              <th className="p-2">Recommendable</th>
              <th className="p-2">Created</th>
              <th className="p-2">Updated</th>
            </tr>
          </thead>
          <tbody>
            {items.map((n, i) => (
              <tr key={n.id ?? i} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="p-2"><input type="checkbox" checked={selected.has(n.id)} onChange={()=>toggleSelect(n.id)} /></td>
                <td className="p-2 font-mono">{n.id ?? "-"}</td>
                <td className="p-2">{n.slug ?? n.name ?? "-"}</td>
                <td className="p-2">{n.status ?? n.state ?? "-"}</td>
                <td className="p-2 text-center"><input type="checkbox" checked={n.is_visible} onChange={()=>handleToggle(n.id,"is_visible",n.is_visible)} /></td>
                <td className="p-2 text-center"><input type="checkbox" checked={n.is_public} onChange={()=>handleToggle(n.id,"is_public",n.is_public)} /></td>
                <td className="p-2 text-center"><input type="checkbox" checked={n.premium_only} onChange={()=>handleToggle(n.id,"premium_only",n.premium_only)} /></td>
                <td className="p-2 text-center"><input type="checkbox" checked={n.is_recommendable} onChange={()=>handleToggle(n.id,"is_recommendable",n.is_recommendable)} /></td>
                <td className="p-2">{n.created_at ? new Date(n.created_at).toLocaleString() : "-"}</td>
                <td className="p-2">{n.updated_at ? new Date(n.updated_at).toLocaleString() : "-"}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={10} className="p-4 text-center text-gray-500">No nodes found</td>
              </tr>
            )}
          </tbody>
        </table>
        <div className="flex items-center gap-2 mt-2">
          <button
            className="px-2 py-1 border rounded"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
          >
            Prev
          </button>
          <span className="text-sm">Page {page + 1}</span>
          <button
            className="px-2 py-1 border rounded"
            disabled={!hasMore}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </button>
        </div>
        </>
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
            const msg = e instanceof Error ? e.message : String(e);
            addToast({ title: "Failed to create node", description: msg, variant: "error" });
          }
        }}
      />
    </div>
  );
}

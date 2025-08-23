import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import NodeEditorModal from "../components/NodeEditorModal";
import type { NodeEditorData } from "../components/NodeEditorModal.helpers";
import EditorJSViewer from "../components/EditorJSViewer";
import { useToast } from "../components/ToastProvider";

type NodeItem = {
  id: string;
  slug?: string;
  status?: string;
  is_visible: boolean;
  is_public: boolean;
  premium_only: boolean;
  is_recommendable: boolean;
  created_at?: string;
  updated_at?: string;
  [k: string]: any;
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

// Нормализуем поля ответа API (camelCase -> snake_case) и приводим тип
function normalizeNode(raw: any): NodeItem {
  const n = raw || {};
  return {
    ...n,
    id: String(n.id ?? n.uuid ?? n._id),
    slug: n.slug,
    is_visible: typeof n.is_visible === "boolean" ? n.is_visible : Boolean(n.isVisible),
    is_public: typeof n.is_public === "boolean" ? n.is_public : Boolean(n.isPublic),
    premium_only: typeof n.premium_only === "boolean" ? n.premium_only : Boolean(n.premiumOnly),
    is_recommendable:
      typeof n.is_recommendable === "boolean"
        ? n.is_recommendable
        : (typeof n.isRecommendable === "boolean" ? n.isRecommendable : true),
    created_at: n.created_at ?? n.createdAt ?? undefined,
    updated_at: n.updated_at ?? n.updatedAt ?? undefined,
  };
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

type ChangeSet = Partial<Pick<NodeItem, "is_visible" | "is_public" | "premium_only" | "is_recommendable">>;

export default function Nodes() {
  const { addToast } = useToast();

  // Пагинация/поиск
  const [q, setQ] = useState("");
  const [visibility, setVisibility] = useState<"all" | "visible" | "hidden">("all");
  const [page, setPage] = useState(0);
  const [limit, setLimit] = useState(20);

  // Данные
  const [items, setItems] = useState<NodeItem[]>([]);
  const [baseline, setBaseline] = useState<Map<string, NodeItem>>(new Map()); // снимок исходных значений
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Выделение и отложенные изменения
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [pending, setPending] = useState<Map<string, ChangeSet>>(new Map());
  const changesCount = useMemo(
    () =>
      Array.from(pending.values()).reduce(
        (acc, cs) => acc + Object.keys(cs).length,
        0,
      ),
    [pending],
  );
  const [applying, setApplying] = useState(false);

  // Модалка создания ноды
  const [editorOpen, setEditorOpen] = useState(false);
  const [draft, setDraft] = useState<NodeEditorData>(makeDraft());
  const canSave = useMemo(() => !!draft.title.trim(), [draft.title]);

  // Модерация: скрытие с причиной / восстановление
  const [modOpen, setModOpen] = useState(false);
  const [modTarget, setModTarget] = useState<NodeItem | null>(null);
  const [modReason, setModReason] = useState("");
  const [modBusy, setModBusy] = useState(false);

  // Превью ноды
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewBusy, setPreviewBusy] = useState(false);
  const [previewData, setPreviewData] = useState<any | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const openPreviewBySlug = async (slug?: string) => {
    if (!slug) return;
    setPreviewOpen(true);
    setPreviewBusy(true);
    setPreviewError(null);
    setPreviewData(null);
    try {
      const res = await api.get(`/nodes/${encodeURIComponent(slug)}`);
      setPreviewData(res.data);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setPreviewError(msg);
    } finally {
      setPreviewBusy(false);
    }
  };

  const openModerationFor = (node: NodeItem) => {
    // Если нода сейчас видима — запрашиваем причину и скрываем
    if (node.is_visible) {
      setModTarget(node);
      setModReason("");
      setModOpen(true);
    } else {
      // Восстановление: confirm и прямой вызов
      if (!node.slug) {
        addToast({ title: "Restore failed", description: "Slug is missing", variant: "error" });
        return;
      }
      if (!confirm("Restore this node?")) return;
      (async () => {
        try {
          setModBusy(true);
          await api.post(`/admin/moderation/nodes/${encodeURIComponent(String(node.slug))}/restore`);
          // Оптимистично обновляем строку и baseline
          setItems((prev) => prev.map((n) => (n.id === node.id ? { ...n, is_visible: true } : n)));
          setBaseline((prev) => {
            const m = new Map(prev);
            const base = m.get(node.id) || node;
            m.set(node.id, { ...base, is_visible: true });
            return m;
          });
          addToast({ title: "Node restored", variant: "success" });
          // Фоновая верификация
          await load(page);
        } catch (e) {
          addToast({ title: "Restore failed", description: e instanceof Error ? e.message : String(e), variant: "error" });
        } finally {
          setModBusy(false);
        }
      })();
    }
  };

  const submitModerationHide = async () => {
    if (!modTarget) return;
    if (!modTarget.slug) {
      addToast({ title: "Hide failed", description: "Slug is missing", variant: "error" });
      return;
    }
    try {
      setModBusy(true);
      await api.post(`/admin/moderation/nodes/${encodeURIComponent(String(modTarget.slug))}/hide`, { reason: modReason || "" });
      setModOpen(false);
      // Оптимистично: делаем ноду невидимой и фиксируем в baseline
      setItems((prev) => prev.map((n) => (n.id === modTarget.id ? { ...n, is_visible: false } : n)));
      setBaseline((prev) => {
        const m = new Map(prev);
        const base = m.get(modTarget.id) || modTarget;
        m.set(modTarget.id, { ...base, is_visible: false });
        return m;
      });
      addToast({ title: "Node hidden", variant: "success" });
      await load(page);
    } catch (e) {
      addToast({ title: "Hide failed", description: e instanceof Error ? e.message : String(e), variant: "error" });
    } finally {
      setModBusy(false);
    }
  };

  // Moderation sidebar removed — отдельные состояния/загрузки скрытых нод не нужны

  // Загрузка списка нод
  const loadingRef = useRef(false);
  const creatingRef = useRef(false);
  const load = async (pageIndex = page) => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {
        limit: String(limit),
        offset: String(pageIndex * limit),
      };
      if (q) params.q = q;
      if (visibility !== "all") params.visible = visibility === "visible" ? "true" : "false";
      const qs = new URLSearchParams(params).toString();
      const res = await api.get(`/admin/nodes?${qs}`);
      const raw = ensureArray<any>(res.data) as any[];
      const arr: NodeItem[] = raw.map((x) => normalizeNode(x));
      setItems(arr);
      setHasMore(arr.length === limit);
      // baseline фиксируем только при полной загрузке, чтобы сравнивать изменения
      const snap = new Map<string, NodeItem>();
      arr.forEach((n: NodeItem) => snap.set(n.id, { ...n }));
      setBaseline(snap);
      setPending(new Map());
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      addToast({ title: "Failed to load nodes", description: msg, variant: "error" });
      setItems([]);
      setBaseline(new Map());
      setPending(new Map());
    } finally {
      setLoading(false);
      loadingRef.current = false;
    }
  };

  useEffect(() => {
    load(page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  // Локальные изменения без немедленного вызова API.
  // Для is_visible используем модерационные ручки (hide с причиной / restore) — без staging.
  const toggleField = (id: string, field: keyof ChangeSet) => {
    if (field === "is_visible") {
      const node = items.find((n) => n.id === id);
      if (node) openModerationFor(node);
      return;
    }

    // Остальные флаги работают в staged-режиме
    const current =
      (items.find((n) => n.id === id)?.[field] as boolean | undefined) ??
      (baseline.get(id)?.[field] as boolean | undefined) ??
      false;
    const nextVal = !current;

    setItems((prev) => prev.map((n) => (n.id === id ? { ...n, [field]: nextVal } : n)));

    setPending((prev) => {
      const next = new Map(prev);
      const cs = { ...(next.get(id) || {}) };
      cs[field] = nextVal;
      next.set(id, cs);
      return next;
    });
  };

  const applyChanges = async () => {
    if (pending.size === 0) return;
    setApplying(true);
    const ops: Record<string, string[]> = {
      hide: [],
      show: [],
      public: [],
      private: [],
      toggle_premium: [],
      toggle_recommendable: [],
    };

    // Строим операции только по реально изменённым полям из pending
    for (const [id, cs] of pending.entries()) {
      const base = baseline.get(id);
      if (!base) continue;
      if (cs.is_visible !== undefined && cs.is_visible !== base.is_visible) {
        (cs.is_visible ? ops.show : ops.hide).push(id);
      }
      if (cs.is_public !== undefined && cs.is_public !== base.is_public) {
        (cs.is_public ? ops.public : ops.private).push(id);
      }
      if (cs.premium_only !== undefined && cs.premium_only !== base.premium_only) {
        ops.toggle_premium.push(id);
      }
      if (cs.is_recommendable !== undefined && cs.is_recommendable !== base.is_recommendable) {
        ops.toggle_recommendable.push(id);
      }
    }

    let any = false;
    const results: string[] = [];
    try {
      for (const [op, ids] of Object.entries(ops)) {
        if (ids.length === 0) continue;
        any = true;
        await api.post(`/admin/nodes/bulk`, { ids, op });
        results.push(`${op}: ${ids.length}`);
      }
      if (any) {
        addToast({ title: "Changes applied", description: results.join(", "), variant: "success" });
        // Оптимистично фиксируем новые значения как базовые,
        // чтобы статус в таблице не «откатывался» визуально.
        setBaseline(new Map(items.map((n) => [n.id, { ...n }])));
        setPending(new Map());
        // Фоновая верификация серверного состояния
        await load(page);
      } else {
        addToast({ title: "No changes to apply", variant: "info" });
      }
    } catch (e) {
      addToast({
        title: "Failed to apply changes",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    } finally {
      setApplying(false);
    }
  };

  const discardChanges = () => {
    // Откатываем к baseline
    setItems(Array.from(baseline.values()));
    setPending(new Map());
  };

  // Выделение строк
  const toggleSelect = (id: string) => {
    setSelected((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  // Создание ноды + явная установка тегов
  const doCreate = async () => {
    if (!canSave) return;
    const payload: Record<string, any> = {
      title: draft.title.trim(),
      content: draft.contentData,
      allow_comments: draft.allow_comments,
      is_premium_only: draft.is_premium_only,
      // передаем на случай, если backend уже поддерживает теги в /nodes
      tags: Array.isArray(draft.tags) ? draft.tags : [],
    };
    const blocks = Array.isArray(draft.contentData?.blocks) ? draft.contentData.blocks : [];
    const media = blocks
      .filter((b: any) => b.type === "image" && b.data?.file?.url)
      .map((b: any) => String(b.data.file.url));
    if (media.length) payload.media = media;
    if (draft.cover_url || media.length) payload.cover_url = draft.cover_url || media[0];

    const res = await api.post("/nodes", payload);
    const created: any = res.data;
    const nodeId = String(created?.id ?? created?.uuid ?? created?._id ?? "");
    const tags = Array.isArray(draft.tags) ? draft.tags.map((t) => String(t).trim()).filter(Boolean) : [];

    if (nodeId && tags.length > 0) {
      const body = { tags };
      // Пытаемся использовать доступные варианты эндпоинтов
      try {
        await api.request(`/nodes/${encodeURIComponent(nodeId)}/tags`, { method: "PUT", json: body });
      } catch {
        try {
          await api.post(`/nodes/${encodeURIComponent(nodeId)}/tags`, body);
        } catch {
          try {
            await api.post(`/admin/nodes/${encodeURIComponent(nodeId)}/tags`, body);
          } catch {
            // если все варианты недоступны — тихо продолжаем, чтобы не ломать флоу создания
          }
        }
      }
    }

    return created as any;
  };

  // Moderation actions by slug (hide/restore) удалены вместе с боковой панелью.

  return (
    <div className="flex gap-6">
      <div className="flex-1">
        <h1 className="text-2xl font-bold mb-4">Nodes</h1>

        {/* Панель поиска и применения изменений */}
        <div className="mb-3 flex items-center gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by slug..."
            className="border rounded px-2 py-1"
          />
          <select
            className="border rounded px-2 py-1"
            value={visibility}
            onChange={(e) => {
              setVisibility(e.target.value as any);
              setPage(0);
              // Подгружаем заново с новым фильтром
              setTimeout(() => load(0));
            }}
          >
            <option value="all">all</option>
            <option value="visible">visible</option>
            <option value="hidden">hidden</option>
          </select>
          <button
            type="button"
            onClick={() => {
              setPage(0);
              load(0);
            }}
            className="px-3 py-1 rounded border"
          >
            Search
          </button>

          <label className="ml-2 text-sm text-gray-600">
            per page:
            <select
              className="ml-2 border rounded px-2 py-1"
              value={limit}
              onChange={(e) => {
                const val = Number(e.target.value) || 10;
                setLimit(val);
                setPage(0);
                // перегружаем список с новым лимитом
                setTimeout(() => load(0));
              }}
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>

          <div className="ml-auto flex items-center gap-2">
            <button
              type="button"
              className="px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50"
              disabled={changesCount === 0 || loading || applying}
              onClick={applyChanges}
            >
              {applying ? "Applying…" : `Apply changes${changesCount > 0 ? ` (${changesCount})` : ""}`}
            </button>
            <button
              type="button"
              className="px-3 py-1 rounded border disabled:opacity-50"
              disabled={changesCount === 0 || loading || applying}
              onClick={discardChanges}
            >
              Discard
            </button>
            <button
              type="button"
              className="px-3 py-1 rounded bg-blue-600 text-white"
              onClick={() => {
                setDraft(makeDraft());
                setEditorOpen(true);
              }}
            >
              Create node
            </button>
          </div>
        </div>

        {loading && <p>Loading...</p>}
        {error && <p className="text-red-600">{error}</p>}

        {/* Bulk по выделению (по-прежнему доступно) */}
        {selected.size > 0 && (
          <div className="mb-2 flex gap-2">
            <span className="self-center text-sm">Selected {selected.size}</span>
            <button type="button" className="px-2 py-1 border rounded" onClick={() => { setItems(items.map(n => selected.has(n.id) ? { ...n, is_visible: false } : n)); setPending(p => { const m=new Map(p); Array.from(selected).forEach(id=>{ const cs={...(m.get(id)||{})}; cs.is_visible=false; m.set(id, cs);}); return m;}); }}>Hide</button>
            <button type="button" className="px-2 py-1 border rounded" onClick={() => { setItems(items.map(n => selected.has(n.id) ? { ...n, is_visible: true } : n)); setPending(p => { const m=new Map(p); Array.from(selected).forEach(id=>{ const cs={...(m.get(id)||{})}; cs.is_visible=true; m.set(id, cs);}); return m;}); }}>Show</button>
            <button type="button" className="px-2 py-1 border rounded" onClick={() => { setItems(items.map(n => selected.has(n.id) ? { ...n, is_public: true } : n)); setPending(p => { const m=new Map(p); Array.from(selected).forEach(id=>{ const cs={...(m.get(id)||{})}; cs.is_public=true; m.set(id, cs);}); return m;}); }}>Public</button>
            <button type="button" className="px-2 py-1 border rounded" onClick={() => { setItems(items.map(n => selected.has(n.id) ? { ...n, is_public: false } : n)); setPending(p => { const m=new Map(p); Array.from(selected).forEach(id=>{ const cs={...(m.get(id)||{})}; cs.is_public=false; m.set(id, cs);}); return m;}); }}>Private</button>
            <button type="button" className="px-2 py-1 border rounded" onClick={() => { setItems(items.map(n => selected.has(n.id) ? { ...n, premium_only: !n.premium_only } : n)); setPending(p => { const m=new Map(p); Array.from(selected).forEach(id=>{ const cs={...(m.get(id)||{})}; cs.premium_only = !(baseline.get(id)?.premium_only ?? false); m.set(id, cs);}); return m;}); }}>Toggle premium</button>
            <button type="button" className="px-2 py-1 border rounded" onClick={() => { setItems(items.map(n => selected.has(n.id) ? { ...n, is_recommendable: !n.is_recommendable } : n)); setPending(p => { const m=new Map(p); Array.from(selected).forEach(id=>{ const cs={...(m.get(id)||{})}; cs.is_recommendable = !(baseline.get(id)?.is_recommendable ?? false); m.set(id, cs);}); return m;}); }}>Toggle recommendable</button>
            <button type="button" className="ml-auto px-2 py-1 border rounded" onClick={() => setSelected(new Set())}>Clear</button>
          </div>
        )}

        {/* Таблица нод */}
        {!loading && !error && (
          <>
            <table className="min-w-full text-sm text-left">
              <thead>
                <tr className="border-b">
                  <th className="p-2">
                    <input
                      type="checkbox"
                      checked={items.length > 0 && selected.size === items.length}
                      onChange={(e) =>
                        setSelected(e.target.checked ? new Set(items.map((i) => i.id)) : new Set())
                      }
                    />
                  </th>
                  <th className="p-2">ID</th>
                  <th className="p-2">Slug</th>
                  <th className="p-2">Status</th>
                  <th className="p-2">Visible</th>
                  <th className="p-2">Public</th>
                  <th className="p-2">Premium</th>
                  <th className="p-2">Recommendable</th>
                  <th className="p-2">Created</th>
                  <th className="p-2">Updated</th>
                  <th className="p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((n, i) => {
                  const base = baseline.get(n.id);
                  const changed =
                    !!base &&
                    (base.is_visible !== n.is_visible ||
                      base.is_public !== n.is_public ||
                      base.premium_only !== n.premium_only ||
                      base.is_recommendable !== n.is_recommendable);

                  const statusParts = [
                    n.is_visible ? "visible" : "hidden",
                    n.is_public ? "public" : "private",
                    n.premium_only ? "premium" : null,
                    n.is_recommendable ? null : "not-recommendable",
                  ].filter(Boolean) as string[];

                  return (
                    <tr
                      key={n.id ?? i}
                      className={`border-b hover:bg-gray-50 dark:hover:bg-gray-800 ${changed ? "bg-amber-50 dark:bg-amber-900/20" : ""}`}
                    >
                      <td className="p-2">
                        <input type="checkbox" checked={selected.has(n.id)} onChange={() => toggleSelect(n.id)} />
                      </td>
                      <td className="p-2 font-mono">{n.id ?? "-"}</td>
                      <td className="p-2">{n.slug ?? n.name ?? "-"}</td>
                      <td className="p-2">{statusParts.length ? statusParts.join(" / ") : "-"}</td>
                      <td className="p-2 text-center">
                        <input
                          type="checkbox"
                          checked={!!n.is_visible}
                          onChange={() => toggleField(n.id, "is_visible")}
                          disabled={applying || loading || modBusy}
                          title={n.is_visible ? "Hide (with reason)" : "Restore"}
                        />
                      </td>
                      <td className="p-2 text-center">
                        <input type="checkbox" checked={!!n.is_public} onChange={() => toggleField(n.id, "is_public")} />
                      </td>
                      <td className="p-2 text-center">
                        <input type="checkbox" checked={!!n.premium_only} onChange={() => toggleField(n.id, "premium_only")} />
                      </td>
                      <td className="p-2 text-center">
                        <input type="checkbox" checked={!!n.is_recommendable} onChange={() => toggleField(n.id, "is_recommendable")} />
                      </td>
                      <td className="p-2">{n.created_at ? new Date(n.created_at).toLocaleString() : "-"}</td>
                      <td className="p-2">{n.updated_at ? new Date(n.updated_at).toLocaleString() : "-"}</td>
                      <td className="p-2">
                        <button
                          type="button"
                          className="px-2 py-1 border rounded disabled:opacity-50"
                          disabled={!n.slug}
                          onClick={() => openPreviewBySlug(String(n.slug))}
                          title="Просмотреть ноду"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={10} className="p-4 text-center text-gray-500">
                      No nodes found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            <div className="flex items-center gap-2 mt-2">
              <button
                type="button"
                className="px-2 py-1 border rounded"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Prev
              </button>
              <span className="text-sm">Page {page + 1}</span>
              <button
                type="button"
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
          busy={creatingRef.current}
          onCommit={async (action) => {
            if (creatingRef.current) return;
            creatingRef.current = true;
            try {
              const created = await doCreate();
              if (action === "next") {
                setDraft(makeDraft());
              } else {
                setEditorOpen(false);
              }
              await load(page);
              if (created?.slug) {
                addToast({ title: "Node created", description: `Slug: ${created.slug}`, variant: "success" });
              }
            } catch (e) {
              const msg = e instanceof Error ? e.message : String(e);
              addToast({ title: "Failed to create node", description: msg, variant: "error" });
            } finally {
              creatingRef.current = false;
            }
          }}
        />

        {/* Moderation modal: hide with reason */}
        {modOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded bg-white p-4 shadow dark:bg-gray-900">
              <h3 className="mb-3 text-lg font-semibold">Hide node</h3>
              <p className="mb-2 text-sm text-gray-600">
                Provide a reason for hiding this node. The action will be logged in audit.
              </p>
              <input
                className="mb-3 w-full rounded border px-2 py-1"
                placeholder="Reason (optional)"
                value={modReason}
                onChange={(e) => setModReason(e.target.value)}
                disabled={modBusy}
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  className="px-3 py-1 rounded border"
                  onClick={() => setModOpen(false)}
                  disabled={modBusy}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  className="px-3 py-1 rounded bg-gray-800 text-white disabled:opacity-50"
                  onClick={submitModerationHide}
                  disabled={modBusy}
                >
                  {modBusy ? "Hiding…" : "Hide"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Preview modal */}
        {previewOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-3xl rounded bg-white p-4 shadow dark:bg-gray-900">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold">Node preview</h3>
                <button className="px-2 py-1 rounded border" onClick={() => setPreviewOpen(false)} disabled={previewBusy}>
                  Close
                </button>
              </div>
              {previewBusy && <p>Loading…</p>}
              {previewError && <p className="text-red-600">{previewError}</p>}
              {!previewBusy && !previewError && previewData && (
                <div className="space-y-2">
                  <div><span className="font-semibold">Title:</span> {previewData.title ?? "-"}</div>
                  <div><span className="font-semibold">Slug:</span> {previewData.slug ?? "-"}</div>
                  <div>
                    <span className="font-semibold">Visible:</span>{" "}
                    {(previewData.is_visible !== undefined || previewData.isVisible !== undefined)
                      ? String(previewData.is_visible ?? previewData.isVisible)
                      : "-"}
                  </div>
                  <div>
                    <span className="font-semibold">Public:</span>{" "}
                    {(previewData.is_public !== undefined || previewData.isPublic !== undefined)
                      ? String(previewData.is_public ?? previewData.isPublic)
                      : "-"}
                  </div>
                  <div>
                    <span className="font-semibold">Tags:</span>{" "}
                    {
                      Array.isArray(previewData.tags)
                        ? previewData.tags.map((t: any) => (typeof t === "string" ? t : (t?.slug || t?.name || ""))).filter(Boolean).join(", ")
                        : (Array.isArray(previewData.tag_slugs) ? previewData.tag_slugs.join(", ") : "-")
                    }
                  </div>
                  <div className="mt-3">
                    <EditorJSViewer value={previewData.content ?? previewData.contentData ?? { blocks: [] }} />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Moderation sidebar removed: управление скрытием ведём через общий список и фильтр visible/hidden */}
    </div>
  );
}

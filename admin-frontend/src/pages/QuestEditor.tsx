import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/ToastProvider";
import NodeEditorModal from "../components/NodeEditorModal";

type Id = string;

interface LocalNode {
  id: Id;            // локальный временный id
  backendId?: string; // id ноды на сервере, если создана
  title: string;
  subtitle?: string;
  cover_image?: string | null;
  tags?: string[];
  allow_comments?: boolean;
  is_premium_only?: boolean;
  contentData: any;  // Editor.js data
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Edge {
  id: Id;
  from: Id; // local node id
  to: Id;   // local node id
}

function uuid() {
  return Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}

export default function QuestEditor() {
  const navigate = useNavigate();
  const { addToast } = useToast();

  // Метаданные квеста
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [price, setPrice] = useState<string>("");
  const [premiumOnly, setPremiumOnly] = useState(false);
  const [allowComments, setAllowComments] = useState(true);
  const [entryNodeLocalId, setEntryNodeLocalId] = useState<Id | "">("");

  // Граф
  const [nodes, setNodes] = useState<LocalNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selected, setSelected] = useState<Id | null>(null);
  const [connectMode, setConnectMode] = useState<boolean>(false);
  const [pendingFrom, setPendingFrom] = useState<Id | null>(null);

  const canvasRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const dragState = useRef<{ id: Id; dx: number; dy: number } | null>(null);

  const addNode = () => {
    const id = uuid();
    setNodes((prev) => [
      ...prev,
      {
        id,
        title: "New node",
        subtitle: "",
        cover_image: null,
        tags: [],
        allow_comments: true,
        is_premium_only: false,
        contentData: { time: Date.now(), blocks: [{ type: "paragraph", data: { text: "" } }], version: "2.30.7" },
        x: 80 + (prev.length % 5) * 140,
        y: 80 + Math.floor(prev.length / 5) * 140,
        width: 260,
        height: 160,
      },
    ]);
    return id;
  };

  const addNodeAndEdit = () => {
    const id = addNode();
    setSelected(id);
    return id;
  };

  const removeNode = (id: Id) => {
    setNodes((prev) => prev.filter((n) => n.id !== id));
    setEdges((prev) => prev.filter((e) => e.from !== id && e.to !== id));
    if (selected === id) setSelected(null);
  };

  const startConnect = (fromId: Id) => {
    setConnectMode(true);
    setPendingFrom(fromId);
  };

  const completeConnect = (toId: Id) => {
    if (!connectMode || !pendingFrom) return;
    if (pendingFrom === toId) {
      setConnectMode(false);
      setPendingFrom(null);
      return;
    }
    const id = `${pendingFrom}->${toId}`;
    setEdges((prev) => (prev.some((e) => e.id === id) ? prev : [...prev, { id, from: pendingFrom, to: toId }]));
    setConnectMode(false);
    setPendingFrom(null);
  };

  const removeEdge = (id: Id) => setEdges((prev) => prev.filter((e) => e.id !== id));

  // Drag & Drop
  const onMouseDown = (e: React.MouseEvent, nodeId: Id) => {
    const node = nodes.find((n) => n.id === nodeId);
    if (!node) return;
    const rect = canvasRef.current?.getBoundingClientRect();
    const startX = e.clientX - (rect?.left ?? 0);
    const startY = e.clientY - (rect?.top ?? 0);
    dragState.current = { id: nodeId, dx: startX - node.x, dy: startY - node.y };
    setSelected(nodeId);
  };

  const onMouseMove = useCallback(
    (e: MouseEvent) => {
      const st = dragState.current;
      if (!st) return;
      const rect = canvasRef.current?.getBoundingClientRect();
      const cx = e.clientX - (rect?.left ?? 0);
      const cy = e.clientY - (rect?.top ?? 0);
      const maxX = (rect?.width ?? 0) - 40;
      const maxY = (rect?.height ?? 0) - 40;
      setNodes((prev) =>
        prev.map((n) =>
          n.id === st.id
            ? {
                ...n,
                x: clamp(cx - st.dx, 0, maxX),
                y: clamp(cy - st.dy, 0, maxY),
              }
            : n,
        ),
      );
    },
    [],
  );

  const onMouseUp = useCallback(() => {
    dragState.current = null;
  }, []);

  useEffect(() => {
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, [onMouseMove, onMouseUp]);

  // Координаты центров для ребер
  const nodeCenters = useMemo(() => {
    const m: Record<Id, { cx: number; cy: number }> = {};
    nodes.forEach((n) => (m[n.id] = { cx: n.x + n.width / 2, cy: n.y + n.height / 2 }));
    return m;
  }, [nodes]);

  // Backend: создать недостающие ноды (черновики)
  const [busy, setBusy] = useState(false);

  const createMissingNodes = async () => {
    setBusy(true);
    try {
      const pending = nodes.filter((n) => !n.backendId);
      for (const n of pending) {
        // Старательно отправляем несколько возможных полей контента, чтобы согласоваться с бэком
        const payload: Record<string, any> = {
          title: n.title,
          subtitle: n.subtitle || null,
          cover_image: n.cover_image || null,
          tags: n.tags || [],
          allow_comments: n.allow_comments ?? true,
          is_premium_only: n.is_premium_only ?? false,
          content_json: n.contentData,
          is_draft: true,
        };
        const res = await api.post("/nodes", payload);
        const created = (res.data || {}) as any;
        const backendId = created.id || created.node_id || created.uuid || created.slug || created._id;
        if (!backendId) {
          throw new Error("Node creation failed: no id in response");
        }
        setNodes((prev) => prev.map((x) => (x.id === n.id ? { ...x, backendId: String(backendId) } : x)));
      }
      addToast({ title: "Nodes created", variant: "success" });
    } catch (e) {
      addToast({
        title: "Failed to create nodes",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    } finally {
      setBusy(false);
    }
  };

  // Сохранение квеста: сначала убеждаемся, что все ноды имеют backendId
  const saveQuest = async () => {
    if (!title.trim()) {
      addToast({ title: "Title is required", variant: "error" });
      return;
    }
    const missing = nodes.filter((n) => !n.backendId);
    if (missing.length > 0) {
      addToast({ title: "Create nodes first", description: "Some nodes are not created yet", variant: "warning" });
      return;
    }
    setBusy(true);
    try {
      const nodesIds = nodes.map((n) => n.backendId!) as string[];
      // custom_transitions: { [fromId]: { [toId]: {...meta} } }
      const transitions: Record<string, Record<string, any>> = {};
      edges.forEach((e) => {
        const from = nodes.find((n) => n.id === e.from)?.backendId!;
        const to = nodes.find((n) => n.id === e.to)?.backendId!;
        if (!from || !to) return;
        if (!transitions[from]) transitions[from] = {};
        transitions[from][to] = { type: "manual" };
      });

      const payload: any = {
        title,
        subtitle: subtitle || null,
        description: description || null,
        tags: tags ? tags.split(",").map((s) => s.trim()).filter(Boolean) : [],
        price: price ? Number(price) : null,
        is_premium_only: premiumOnly,
        allow_comments: allowComments,
        entry_node_id: entryNodeLocalId ? nodes.find((n) => n.id === entryNodeLocalId)?.backendId || null : null,
        nodes: nodesIds,
        custom_transitions: transitions,
      };

      const res = await api.post("/quests", payload);
      const created = res.data as any;
      addToast({ title: "Quest saved", description: created?.title || "", variant: "success" });
      navigate("/quests");
    } catch (e) {
      addToast({
        title: "Failed to save quest",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    } finally {
      setBusy(false);
    }
  };

  // Попытаться создать реальные переходы между нодами (best-effort)
  const materializeTransitions = async () => {
    const missing = nodes.filter((n) => !n.backendId);
    if (missing.length > 0) {
      addToast({ title: "Create nodes first", variant: "warning" });
      return;
    }
    setBusy(true);
    try {
      for (const e of edges) {
        const from = nodes.find((n) => n.id === e.from)?.backendId!;
        const to = nodes.find((n) => n.id === e.to)?.backendId!;
        if (!from || !to) continue;
        // Пытаемся оба распространённых варианта пути
        try {
          await api.post(`/nodes/${from}/transitions`, { to_node_id: to, type: "manual" });
        } catch {
          await api.post(`/nodes/${from}/transitions/${to}`, { type: "manual" });
        }
      }
      addToast({ title: "Transitions created", variant: "success" });
    } catch (e) {
      addToast({
        title: "Failed to create transitions",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="h-full flex gap-4">
      {/* Левая панель — метаданные квеста */}
      <div className="w-80 shrink-0 space-y-3">
        <h1 className="text-2xl font-bold">Quest editor</h1>
        <div className="space-y-2">
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Title</label>
            <input className="border rounded px-2 py-1" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Subtitle</label>
            <input className="border rounded px-2 py-1" value={subtitle} onChange={(e) => setSubtitle(e.target.value)} />
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Description</label>
            <textarea className="border rounded px-2 py-1" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Tags (comma)</label>
            <input className="border rounded px-2 py-1" value={tags} onChange={(e) => setTags(e.target.value)} />
          </div>
          <div className="flex gap-2">
            <div className="flex-1 flex flex-col">
              <label className="text-sm text-gray-600">Price</label>
              <input className="border rounded px-2 py-1" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="0 for free" />
            </div>
            <label className="flex items-center gap-2 mt-6">
              <input type="checkbox" checked={premiumOnly} onChange={(e) => setPremiumOnly(e.target.checked)} />
              <span className="text-sm">Premium</span>
            </label>
          </div>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={allowComments} onChange={(e) => setAllowComments(e.target.checked)} />
            <span className="text-sm">Allow comments</span>
          </label>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Entry node</label>
            <select className="border rounded px-2 py-1" value={entryNodeLocalId} onChange={(e) => setEntryNodeLocalId(e.target.value as Id)}>
              <option value="">—</option>
              {nodes.map((n) => (
                <option key={n.id} value={n.id}>
                  {n.title}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-wrap gap-2 pt-2">
            <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-700" onClick={addNodeAndEdit}>Add node</button>
            <button className={`px-3 py-1 rounded ${connectMode ? "bg-blue-600 text-white" : "bg-gray-200 dark:bg-gray-700"}`} onClick={() => setConnectMode((v) => !v)}>
              {connectMode ? "Connecting…" : "Connect"}
            </button>
            <button className="px-3 py-1 rounded bg-emerald-600 text-white disabled:opacity-60" onClick={createMissingNodes} disabled={busy}>
              Create nodes
            </button>
            <button className="px-3 py-1 rounded bg-indigo-600 text-white disabled:opacity-60" onClick={materializeTransitions} disabled={busy}>
              Create transitions
            </button>
            <button className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-60" onClick={saveQuest} disabled={busy}>
              Save quest
            </button>
            <button className="px-3 py-1 rounded border" onClick={() => navigate("/quests")}>Back</button>
          </div>
        </div>
      </div>

      {/* Холст */}
      <div className="relative flex-1 overflow-auto border rounded" ref={canvasRef} style={{ minHeight: 600 }}>
        {/* Рёбра */}
        <svg ref={svgRef} className="absolute inset-0 w-full h-full pointer-events-none">
          {edges.map((e) => {
            const from = nodeCenters[e.from];
            const to = nodeCenters[e.to];
            if (!from || !to) return null;
            return (
              <g key={e.id}>
                <defs>
                  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                    <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
                  </marker>
                </defs>
                <line x1={from.cx} y1={from.cy} x2={to.cx} y2={to.cy} stroke="#64748b" strokeWidth="2" markerEnd="url(#arrow)" />
                {/* Кнопка удаления ребра по центру */}
                <circle
                  cx={(from.cx + to.cx) / 2}
                  cy={(from.cy + to.cy) / 2}
                  r="8"
                  fill="#fff"
                  stroke="#e11d48"
                  className="cursor-pointer pointer-events-auto"
                  onClick={() => removeEdge(e.id)}
                />
              </g>
            );
          })}
        </svg>

        {/* Ноды */}
        {nodes.map((n) => (
          <div
            key={n.id}
            className={`absolute rounded shadow border bg-white dark:bg-gray-900 ${selected === n.id ? "ring-2 ring-blue-500" : ""}`}
            style={{ left: n.x, top: n.y, width: n.width, height: n.height }}
            onClick={(e) => {
              e.stopPropagation();
              if (connectMode) {
                if (pendingFrom) completeConnect(n.id);
                else startConnect(n.id);
              } else {
                setSelected(n.id);
              }
            }}
          >
            <div
              className="cursor-move bg-gray-100 dark:bg-gray-800 px-2 py-1 text-sm font-medium rounded-t flex items-center justify-between"
              onMouseDown={(e) => onMouseDown(e, n.id)}
            >
              <input
                className="bg-transparent outline-none w-full"
                value={n.title}
                onChange={(e) => setNodes((prev) => prev.map((x) => (x.id === n.id ? { ...x, title: e.target.value } : x)))}
                onCommit={(act: "save" | "next") => {
                  if (act === "next") {
                    addNodeAndEdit();
                  } else {
                    setSelected(null);
                  }
                }}
              />
              <div className="ml-2 flex items-center gap-1">
                <button
                  className="text-xs px-2 py-0.5 rounded border"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelected(n.id); // Expand
                  }}
                >
                  Expand
                </button>
                <button
                  className="text-xs px-2 py-0.5 rounded border"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeNode(n.id);
                  }}
                >
                  ×
                </button>
              </div>
            </div>
            <div className="p-2 h-[calc(100%-32px)] text-sm text-gray-600">
              {n.cover_image && (
                <img src={n.cover_image} alt="" className="w-full h-24 object-cover rounded mb-2 border" />
              )}
              <div className="line-clamp-3">
                {(Array.isArray(n.contentData?.blocks) && n.contentData.blocks.find((b: any) => b?.data?.text)?.data?.text) || "No content yet. Click Expand to edit."}
              </div>
              {n.backendId && <div className="absolute right-2 bottom-2 text-[10px] text-gray-500">id: {n.backendId}</div>}
            </div>
          </div>
        ))}

        {/* Модалка полного редактирования выбранной ноды */}
        <NodeEditorModal
          open={Boolean(selected)}
          node={
            selected
              ? (() => {
                  const n = nodes.find((x) => x.id === selected)!;
                  return {
                    id: n.id,
                    title: n.title,
                    subtitle: n.subtitle || "",
                    cover_image: n.cover_image || null,
                    tags: n.tags || [],
                    allow_comments: n.allow_comments ?? true,
                    is_premium_only: n.is_premium_only ?? false,
                    contentData: n.contentData,
                  };
                })()
              : null
          }
          onChange={(patch) => {
            if (!selected) return;
            setNodes((prev) =>
              prev.map((n) =>
                n.id === selected
                  ? {
                      ...n,
                      title: patch.title ?? n.title,
                      subtitle: patch.subtitle ?? n.subtitle,
                      cover_image: patch.cover_image ?? n.cover_image,
                      tags: patch.tags ?? n.tags,
                      allow_comments: patch.allow_comments ?? n.allow_comments,
                      is_premium_only: patch.is_premium_only ?? n.is_premium_only,
                      contentData: patch.contentData ?? n.contentData,
                    }
                  : n,
              ),
            );
          }}
          onClose={() => setSelected(null)}
          onCommit={(act: "save" | "next") => {
            if (act === "next") {
              addNodeAndEdit();
              // новая нода будет отредактирована сразу
            } else {
              setSelected(null);
            }
          }}
        />
      </div>
    </div>
  );
}

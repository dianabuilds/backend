import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import {
  autofixVersion,
  getVersion,
  publishVersion,
  putGraph,
  validateVersion,
  getQuestMeta,
  type VersionGraph,
} from "../api/questEditor";
import CollapsibleSection from "../components/CollapsibleSection";
import ContentEditor from "../components/content/ContentEditor";
import GraphCanvas from "../components/GraphCanvas";
import ErrorBoundary from "../components/ErrorBoundary";
import { useToast } from "../components/ToastProvider";
import ContentPicker from "../components/ContentPicker";
import PlaythroughPanel from "../components/PlaythroughPanel";
import type { OutputData } from "../types/editorjs";
import PageLayout from "./_shared/PageLayout";

interface NodeEditorData {
  id: number;
  title: string;
  slug: string;
  subtitle: string;
  coverUrl: string | null;
  tags: string[];
  allow_comments: boolean;
  is_premium_only: boolean;
  contentData: OutputData;
}

export default function QuestVersionEditor() {
  const { id: questId, versionId: id } =
    useParams<{ id: string; versionId: string }>();
  const [graph, setGraph] = useState<VersionGraph | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [nodeKey, setNodeKey] = useState("");
  const [nodeTitle, setNodeTitle] = useState("");
  const [nodeType, setNodeType] = useState<"start" | "normal" | "end">(
    "normal",
  );
  const [edgeFrom, setEdgeFrom] = useState("");
  const [edgeTo, setEdgeTo] = useState("");
  const [validate, setValidate] = useState<{
    ok: boolean;
    errors: string[];
    warnings: string[];
  } | null>(null);
  const [clientErrors, setClientErrors] = useState<string[]>([]);
  const [clientWarnings, setClientWarnings] = useState<string[]>([]);
  const [savingGraph, setSavingGraph] = useState(false);
  const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);

  // Поиск/пагинация нод
  const [nodesQuery, setNodesQuery] = useState("");
  const [nodesPage, setNodesPage] = useState(1);
  const [nodesPageSize, setNodesPageSize] = useState(20);
  const [nodesMultiColumn, setNodesMultiColumn] = useState(false);

  // Поиск/пагинация ребер
  const [edgesQuery, setEdgesQuery] = useState("");
  const [edgesPage, setEdgesPage] = useState(1);
  const [edgesPageSize, setEdgesPageSize] = useState(30);

  // Quest meta (read-only)
  const [meta, setMeta] = useState<{
    title: string;
    subtitle?: string | null;
    description?: string | null;
    cover_image?: string | null;
    price?: number | null;
    is_premium_only?: boolean;
    allow_comments?: boolean;
    tags?: string[];
  } | null>(null);

  // Modal editor state
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorNode, setEditorNode] = useState<NodeEditorData | null>(null);
  const [savingNode, setSavingNode] = useState(false);
  const { addToast } = useToast();

  const [pickerOpen, setPickerOpen] = useState(false);
  const [showSim, setShowSim] = useState(false);
  const [dirty, setDirty] = useState(false);
  const autoSaveRef = useRef<NodeJS.Timeout | null>(null);

  const nodeMap = useMemo(() => {
    const map = new Map<string, VersionGraph["nodes"][number]>();
    graph?.nodes.forEach((n) => map.set(n.key, n));
    return map;
  }, [graph]);

  const edgeMap = useMemo(() => {
    const map = new Map<string, VersionGraph["edges"][number]>();
    graph?.edges.forEach((e) => map.set(`${e.from_node_key}:${e.to_node_key}`, e));
    return map;
  }, [graph]);

  useEffect(() => {
    if (!graph) {
      setClientErrors([]);
      setClientWarnings([]);
      return;
    }
    const errors: string[] = [];
    const warnings: string[] = [];

    const startNodes = graph.nodes.filter((n) => n.type === "start");
    if (startNodes.length !== 1) {
      errors.push("Graph must contain exactly one start node");
    }
    const visited = new Set<string>();
    if (startNodes[0]) {
      const queue = [startNodes[0].key];
      visited.add(startNodes[0].key);
      while (queue.length) {
        const cur = queue.shift()!;
        graph.edges
          .filter((e) => e.from_node_key === cur)
          .forEach((e) => {
            if (!visited.has(e.to_node_key)) {
              visited.add(e.to_node_key);
              queue.push(e.to_node_key);
            }
          });
      }
    }

    graph.nodes
      .filter((n) => n.type === "end")
      .forEach((n) => {
        if (graph.edges.some((e) => e.from_node_key === n.key)) {
          errors.push(`End node "${n.key}" has outgoing edges`);
        }
      });

    graph.nodes.forEach((n) => {
      if (!visited.has(n.key)) {
        warnings.push(`Node "${n.key}" is unreachable from start`);
      }
    });

    setClientErrors(errors);
    setClientWarnings(warnings);
  }, [graph]);

  const load = async () => {
    if (!id) return;
    setErr(null);
    try {
      const v = await getVersion(id);
      setGraph(v);
      // подгружаем мету квеста
      const qid = questId || v.version.quest_id;
      if (qid) {
        try {
          const m = await getQuestMeta(qid);
          setMeta({
            title: m.title ?? "",
            subtitle: m.subtitle ?? "",
            description: m.description ?? "",
            cover_image: m.cover_image ?? null,
            price: m.price ?? null,
            is_premium_only: !!m.is_premium_only,
            allow_comments: !!m.allow_comments,
            tags: Array.isArray(m.tags) ? m.tags : [],
          });
        } catch (e) {
          console.warn("Failed to load quest meta:", e);
        }
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  useEffect(() => {
    if (!graph || !id) return;
    setDirty(true);
    if (autoSaveRef.current) clearTimeout(autoSaveRef.current);
    autoSaveRef.current = setTimeout(async () => {
      try {
        await putGraph(id, graph);
        setLastSavedAt(new Date().toLocaleTimeString());
        setDirty(false);
      } catch (e) {
        console.warn("Auto-save failed", e);
      }
    }, 2000);
    return () => {
      if (autoSaveRef.current) clearTimeout(autoSaveRef.current);
    };
  }, [graph, id]);

  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty]);

  const slugify = (s: string) =>
    s
      .toLowerCase()
      .trim()
      .replace(/\s+/g, "-")
      .replace(/[^a-z0-9_-]/g, "")
      .replace(/-+/g, "-");

  const addNode = () => {
    if (!graph) return;
    const key = slugify(nodeKey);
    if (!key) return; // ключ обязателен
    // запрет дублей
    if (graph.nodes.some((n) => n.key === key)) {
      addToast({
        title: `Node key "${key}" already exists`,
        variant: "error",
      });
      return;
    }
    // первая нода всегда стартовая
    const typeToUse: "start" | "normal" | "end" =
      graph.nodes.length === 0 ? "start" : nodeType;
    // Разрешаем пустой title как черновик
      setGraph({
        ...graph,
        nodes: [
          ...graph.nodes,
          { key, title: nodeTitle || "", type: typeToUse, content: null, rewards: null },
        ],
      });
    setNodeKey("");
    setNodeTitle("");
    setNodeType("normal");
  };

  const addEdge = () => {
    if (!graph || !edgeFrom || !edgeTo) return;
    if (edgeFrom === edgeTo) {
      addToast({
        title: "Нельзя создавать петлю (из узла в самого себя)",
        variant: "error",
      });
      return;
    }
    if (edgeMap.has(`${edgeFrom}:${edgeTo}`)) {
      addToast({ title: "Такое ребро уже есть", variant: "error" });
      return;
    }
    setGraph({
      ...graph,
      edges: [
        ...graph.edges,
        { from_node_key: edgeFrom, to_node_key: edgeTo, label: null, condition: null },
      ],
    });
    setEdgeFrom("");
    setEdgeTo("");
  };

  const startEditNode = (k: string) => {
    const n = nodeMap.get(k);
    if (!n) return;
    const data: NodeEditorData = {
      id: n.key,
      title: n.title,
      slug: "",
      subtitle: "",
      coverUrl: null,
      tags: [],
      allow_comments: true,
      is_premium_only: false,
      contentData: (n as any).content ?? {
        time: Date.now(),
        blocks: [],
        version: "2.30.7",
      },
    };
    setEditorNode(data);
    setEditorOpen(true);
  };

  // Отфильтрованные/страничные представления
  const filteredNodes = useMemo(() => {
    const q = nodesQuery.trim().toLowerCase();
    if (!graph) return [];
    if (!q) return graph.nodes;
    return graph.nodes.filter(
      (n) =>
        n.key.toLowerCase().includes(q) || n.title.toLowerCase().includes(q),
    );
  }, [graph, nodesQuery]);

  const nodesPageCount = useMemo(
    () => Math.max(1, Math.ceil(filteredNodes.length / nodesPageSize)),
    [filteredNodes.length, nodesPageSize],
  );
  const pagedNodes = useMemo(
    () =>
      filteredNodes.slice(
        (nodesPage - 1) * nodesPageSize,
        nodesPage * nodesPageSize,
      ),
    [filteredNodes, nodesPage, nodesPageSize],
  );

  const filteredEdges = useMemo(() => {
    const q = edgesQuery.trim().toLowerCase();
    if (!graph) return [];
    if (!q) return graph.edges;
    return graph.edges.filter(
      (e) =>
        e.from_node_key.toLowerCase().includes(q) ||
        e.to_node_key.toLowerCase().includes(q),
    );
  }, [graph, edgesQuery]);

  const edgesPageCount = useMemo(
    () => Math.max(1, Math.ceil(filteredEdges.length / edgesPageSize)),
    [filteredEdges.length, edgesPageSize],
  );
  const pagedEdges = useMemo(
    () =>
      filteredEdges.slice(
        (edgesPage - 1) * edgesPageSize,
        edgesPage * edgesPageSize,
      ),
    [filteredEdges, edgesPage, edgesPageSize],
  );

  const commitEditor = async (_action: "save" | "next") => {
    if (!editorNode || !graph) return;
    setSavingNode(true);
    try {
      // Сохраняем title и nodes в граф
      const nextNodes = graph.nodes.map((n) =>
        n.key === editorNode.id
          ? { ...n, title: editorNode.title, content: editorNode.contentData }
          : n,
      );
      setGraph({ ...graph, nodes: nextNodes });
      setEditorOpen(false);
    } finally {
      setSavingNode(false);
    }
  };

  const deleteNode = (key: string) => {
    if (!graph) return;
    const ok = confirm(
      `Delete node "${key}"? All connected edges will be removed.`,
    );
    if (!ok) return;
    const nextNodes = graph.nodes.filter((n) => n.key !== key);
    const nextEdges = graph.edges.filter(
      (e) => e.from_node_key !== key && e.to_node_key !== key,
    );
    setGraph({ ...graph, nodes: nextNodes, edges: nextEdges });
  };

  const onSave = async () => {
    if (!graph || !id) return;
    setSavingGraph(true);
    try {
      await putGraph(id, graph);
      const res = await validateVersion(id);
      setValidate(res);
      const ts = new Date().toLocaleTimeString();
      setLastSavedAt(ts);
      setDirty(false);
      if (!res.ok) {
        addToast({
          title: "Validation failed",
          description: res.errors.join("; "),
          variant: "error",
        });
      }
    } catch (e) {
      addToast({
        title: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    } finally {
      setSavingGraph(false);
    }
  };

  const onPublish = async () => {
    if (!id) return;
    // Сначала сохраняем метаданные и граф, затем публикуем
    await onSave();
    const res = await validateVersion(id);
    setValidate(res);
    if (!res.ok) {
      addToast({
        title: "Validation failed",
        description: res.errors.join("; "),
        variant: "error",
      });
      return;
    }
    await publishVersion(id);
    addToast({
      title: "Quest published",
      description: new Date().toLocaleString(),
      variant: "success",
    });
  };

  return (
    <ErrorBoundary>
      <PageLayout
        title="Quest Version Editor"
        subtitle={id || ""}
        actions={
          <div className="flex items-center gap-3">
          {lastSavedAt && (
            <span className="text-xs text-gray-500">Saved {lastSavedAt}</span>
          )}
          <button
            className="px-3 py-1 rounded border"
            onClick={async () => {
              if (!id) return;
              try {
                await autofixVersion(id);
                await load();
                const res = await validateVersion(id);
                setValidate(res);
              } catch (e) {
                addToast({
                  title: e instanceof Error ? e.message : String(e),
                  variant: "error",
                });
              }
            }}
          >
            Autofix (basic)
          </button>
          <button
            className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800 disabled:opacity-50"
            onClick={onSave}
            disabled={savingGraph}
          >
            {savingGraph ? "Saving…" : "Save & Validate"}
          </button>
          <button
            className="px-3 py-1 rounded border"
            onClick={() => setShowSim((v) => !v)}
          >
            {showSim ? "Close Sim" : "Simulate"}
          </button>
          <button
            className="px-3 py-1 rounded bg-green-600 text-white"
            onClick={onPublish}
          >
            Publish
          </button>
        </div>
      }
    >
      {err && <div className="text-red-600 text-sm">{err}</div>}
      {!graph ? (
        <div className="text-sm text-gray-500">Loading...</div>
      ) : (
        <div className="mt-4 grid grid-cols-3 gap-6">
          {/* Настройки квеста */}
          <div className="col-span-3">
            <CollapsibleSection title="Quest settings" defaultOpen={true}>
              {!meta ? (
                <div className="text-sm text-gray-500">Loading meta…</div>
              ) : (
                <>
                  <div className="p-2 rounded bg-yellow-50 text-sm text-gray-700 mb-2">
                    Quest fields are read-only. Use the quest editor to modify them.
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="md:col-span-2 space-y-2">
                      <input
                        className="w-full text-2xl font-bold mb-2 outline-none border-b pb-2 bg-transparent"
                        value={meta.title}
                        readOnly
                      />
                      <input
                        className="w-full text-base mb-2 outline-none border-b pb-2 bg-transparent"
                        value={meta.subtitle || ""}
                        readOnly
                      />
                      <textarea
                        className="w-full border rounded px-2 py-1"
                        rows={4}
                        value={meta.description || ""}
                        readOnly
                      />
                      {meta.tags && meta.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {meta.tags.map((t) => (
                            <span
                              key={t}
                              className="px-2 py-1 text-sm rounded bg-gray-200"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="flex items-center gap-6">
                        <label className="flex items-center gap-2 text-sm">
                          <input type="checkbox" checked={!!meta.allow_comments} readOnly />
                          <span>💬 Allow comments</span>
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                          <input type="checkbox" checked={!!meta.is_premium_only} readOnly />
                          <span>⭐ Premium only</span>
                        </label>
                        <label className="flex items-center gap-2 text-sm">
                          <span>💰 Price</span>
                          <input
                            type="number"
                            min={0}
                            className="border rounded px-2 py-1 w-32"
                            value={meta.price ?? 0}
                            readOnly
                          />
                        </label>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2">Cover</h4>
                      {meta.cover_image ? (
                        <img
                          src={meta.cover_image}
                          alt="cover"
                          className="w-[180px] h-[240px] object-cover rounded"
                        />
                      ) : (
                        <div className="w-[180px] h-[240px] border rounded flex items-center justify-center text-xs text-gray-500">
                          No cover
                        </div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </CollapsibleSection>
          </div>

          <div className="col-span-2 space-y-4">
            <CollapsibleSection title="Nodes" defaultOpen={true}>
              {/* Панель управления списком нод: поиск, размер страницы, пагинация, раскладка */}
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <input
                  className="border rounded px-2 py-1"
                  placeholder="Search nodes…"
                  value={nodesQuery}
                  onChange={(e) => {
                    setNodesQuery(e.target.value);
                    setNodesPage(1);
                  }}
                />
                <label className="text-sm text-gray-600 flex items-center gap-1">
                  per page
                  <select
                    className="border rounded px-1 py-0.5"
                    value={nodesPageSize}
                    onChange={(e) => {
                      setNodesPageSize(Number(e.target.value));
                      setNodesPage(1);
                    }}
                  >
                    <option value={10}>10</option>
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                  </select>
                </label>
                <div className="ml-auto flex items-center gap-2">
                  <button
                    className="px-2 py-1 rounded border disabled:opacity-50"
                    onClick={() => setNodesPage((p) => Math.max(1, p - 1))}
                    disabled={nodesPage <= 1}
                  >
                    Prev
                  </button>
                  <span className="text-sm text-gray-600">
                    {nodesPage} / {nodesPageCount}
                  </span>
                  <button
                    className="px-2 py-1 rounded border disabled:opacity-50"
                    onClick={() =>
                      setNodesPage((p) => Math.min(nodesPageCount, p + 1))
                    }
                    disabled={nodesPage >= nodesPageCount}
                  >
                    Next
                  </button>
                  <label className="text-sm text-gray-600 flex items-center gap-1">
                    grid
                    <input
                      type="checkbox"
                      checked={nodesMultiColumn}
                      onChange={(e) => setNodesMultiColumn(e.target.checked)}
                    />
                  </label>
                </div>
              </div>

              <div
                className={
                  nodesMultiColumn
                    ? "grid md:grid-cols-2 lg:grid-cols-3 gap-2"
                    : ""
                }
              >
                <input
                  className="border rounded px-2 py-1"
                  placeholder="key (lowercase, a-z0-9_-)"
                  value={nodeKey}
                  onChange={(e) => setNodeKey(slugify(e.target.value))}
                />
                <input
                  className="border rounded px-2 py-1"
                  placeholder="title"
                  value={nodeTitle}
                  onChange={(e) => setNodeTitle(e.target.value)}
                />
                <button
                  className="px-3 py-1 rounded border"
                  onClick={() => setPickerOpen(true)}
                >
                  Pick
                </button>
                <select
                  className="border rounded px-2 py-1"
                  value={graph && graph.nodes.length === 0 ? "start" : nodeType}
                  disabled={!!graph && graph.nodes.length === 0}
                  onChange={(e) => setNodeType(e.target.value as any)}
                  title={
                    graph && graph.nodes.length === 0
                      ? "The first node is always start"
                      : undefined
                  }
                >
                  <option value="normal">normal</option>
                  <option value="start">start</option>
                  <option value="end">end</option>
                </select>
                <button
                  className="px-3 py-1 rounded bg-blue-600 text-white"
                  onClick={addNode}
                  disabled={
                    !nodeKey ||
                    !!graph.nodes.find((n) => n.key === slugify(nodeKey))
                  }
                  title={
                    graph.nodes.find((n) => n.key === slugify(nodeKey))
                      ? "Duplicate key"
                      : ""
                  }
                >
                  Add
                </button>
              </div>
              <ul
                className={
                  nodesMultiColumn ? "text-sm contents" : "text-sm space-y-1"
                }
              >
                {pagedNodes.map((n) => (
                  <li
                    key={n.key}
                    className="border rounded px-2 py-1 flex items-center justify-between"
                  >
                    <span>
                      <b>{n.key}</b> — {n.title}
                    </span>
                    <div className="flex items-center gap-2">
                      <label className="text-xs text-gray-500">Type:</label>
                      <select
                        className="border rounded px-1 py-0.5 text-xs"
                        value={(n as any).type || "normal"}
                        onChange={(e) => {
                          const t = e.target.value as
                            | "start"
                            | "normal"
                            | "end";
                          setGraph({
                            ...graph,
                            nodes: graph.nodes.map((x) =>
                              x.key === n.key ? { ...x, type: t } : x,
                            ),
                          });
                        }}
                      >
                        <option value="normal">normal</option>
                        <option value="start">start</option>
                        <option value="end">end</option>
                      </select>
                      <button
                        className="px-2 py-0.5 rounded border"
                        onClick={() => startEditNode(n.key)}
                      >
                        Edit
                      </button>
                      <button
                        className="px-2 py-0.5 rounded border text-red-600 border-red-300"
                        onClick={() => deleteNode(n.key)}
                        title="Delete node"
                      >
                        Delete
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </CollapsibleSection>
            <CollapsibleSection title="Edges" defaultOpen={true}>
              {/* Панель управления списком рёбер: поиск, размер страницы, пагинация */}
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <input
                  className="border rounded px-2 py-1"
                  placeholder="Search edges…"
                  value={edgesQuery}
                  onChange={(e) => {
                    setEdgesQuery(e.target.value);
                    setEdgesPage(1);
                  }}
                />
                <label className="text-sm text-gray-600 flex items-center gap-1">
                  per page
                  <select
                    className="border rounded px-1 py-0.5"
                    value={edgesPageSize}
                    onChange={(e) => {
                      setEdgesPageSize(Number(e.target.value));
                      setEdgesPage(1);
                    }}
                  >
                    <option value={20}>20</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </label>
                <div className="ml-auto flex items-center gap-2">
                  <button
                    className="px-2 py-1 rounded border disabled:opacity-50"
                    onClick={() => setEdgesPage((p) => Math.max(1, p - 1))}
                    disabled={edgesPage <= 1}
                  >
                    Prev
                  </button>
                  <span className="text-sm text-gray-600">
                    {edgesPage} / {edgesPageCount}
                  </span>
                  <button
                    className="px-2 py-1 rounded border disabled:opacity-50"
                    onClick={() =>
                      setEdgesPage((p) => Math.min(edgesPageCount, p + 1))
                    }
                    disabled={edgesPage >= edgesPageCount}
                  >
                    Next
                  </button>
                </div>
              </div>

              <div className="flex gap-2 mb-2">
                <select
                  className="border rounded px-2 py-1"
                  value={edgeFrom}
                  onChange={(e) => setEdgeFrom(e.target.value)}
                >
                  <option value="">from…</option>
                  {graph.nodes.map((n) => (
                    <option key={`f-${n.key}`} value={n.key}>
                      {n.key}
                    </option>
                  ))}
                </select>
                <select
                  className="border rounded px-2 py-1"
                  value={edgeTo}
                  onChange={(e) => setEdgeTo(e.target.value)}
                >
                  <option value="">to…</option>
                  {graph.nodes.map((n) => (
                    <option key={`t-${n.key}`} value={n.key}>
                      {n.key}
                    </option>
                  ))}
                </select>
                <button
                  className="px-3 py-1 rounded bg-blue-600 text-white"
                  onClick={addEdge}
                  disabled={!edgeFrom || !edgeTo || edgeFrom === edgeTo}
                >
                  Add
                </button>
              </div>
              <ul className="text-sm space-y-1">
                {pagedEdges.map((e, i) => {
                  // Индекс в исходном массиве нужен для редактирования/удаления
                  const idx = filteredEdges.indexOf(e);
                  return (
                    <li
                      key={`${e.from_node_key}->${e.to_node_key}-${i}`}
                      className="border rounded px-2 py-1 flex items-center gap-2"
                    >
                      <select
                        className="border rounded px-1 py-0.5 text-xs"
                        value={e.from_node_key}
                        onChange={(ev) => {
                          const val = ev.target.value;
                          setGraph({
                            ...graph,
                            edges: graph.edges.map((x, j) =>
                              j === idx ? { ...x, from_node_key: val } : x,
                            ),
                          });
                        }}
                      >
                        {graph.nodes.map((n) => (
                          <option key={`ef-${n.key}`} value={n.key}>
                            {n.key}
                          </option>
                        ))}
                      </select>
                      <span>→</span>
                      <select
                        className="border rounded px-1 py-0.5 text-xs"
                        value={e.to_node_key}
                        onChange={(ev) => {
                          const val = ev.target.value;
                          setGraph({
                            ...graph,
                            edges: graph.edges.map((x, j) =>
                              j === idx ? { ...x, to_node_key: val } : x,
                            ),
                          });
                        }}
                      >
                        {graph.nodes.map((n) => (
                          <option key={`et-${n.key}`} value={n.key}>
                            {n.key}
                          </option>
                        ))}
                      </select>
                      <button
                        className="ml-auto px-2 py-0.5 rounded border text-red-600 border-red-300"
                        onClick={() => {
                          setGraph({
                            ...graph,
                            edges: graph.edges.filter((_, j) => j !== idx),
                          });
                        }}
                        title="Delete edge"
                      >
                        Delete
                      </button>
                    </li>
                  );
                })}
              </ul>
            </CollapsibleSection>
          </div>
          <div className="col-span-1">
            <CollapsibleSection title="Validation report">
              <div className="mb-2 flex items-center gap-2">
                <button
                  className="px-2 py-1 rounded border"
                  onClick={async () => {
                    if (!id) return;
                    try {
                      const res = await validateVersion(id);
                      setValidate(res);
                    } catch (e) {
                      addToast({
                        title: e instanceof Error ? e.message : String(e),
                        variant: "error",
                      });
                    }
                  }}
                >
                  Validate
                </button>
                {validate && (
                  <>
                    <span className="text-sm">
                      Errors: <b>{validate.errors.length}</b>
                    </span>
                    <span className="text-sm">
                      Warnings: <b>{validate.warnings.length}</b>
                    </span>
                  </>
                )}
              </div>
              {validate ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <div className="font-semibold mb-1">Errors</div>
                    <ul className="list-disc pl-5 text-red-700">
                      {validate.errors.map((e, i) => (
                        <li key={i}>{e}</li>
                      ))}
                      {validate.errors.length === 0 && (
                        <li className="text-gray-500">None</li>
                      )}
                    </ul>
                  </div>
                  <div>
                    <div className="font-semibold mb-1">Warnings</div>
                    <ul className="list-disc pl-5 text-yellow-700">
                      {validate.warnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                      {validate.warnings.length === 0 && (
                        <li className="text-gray-500">None</li>
                      )}
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-gray-500">
                  Run validation to see the report
                </div>
              )}
            </CollapsibleSection>
          </div>

          <div className="col-span-1">
            <CollapsibleSection title="Live checks">
              {clientErrors.length === 0 && clientWarnings.length === 0 ? (
                <div className="text-sm text-gray-500">No issues</div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <div className="font-semibold mb-1">Errors</div>
                    <ul className="list-disc pl-5 text-red-700">
                      {clientErrors.map((e, i) => (
                        <li key={i}>{e}</li>
                      ))}
                      {clientErrors.length === 0 && (
                        <li className="text-gray-500">None</li>
                      )}
                    </ul>
                  </div>
                  <div>
                    <div className="font-semibold mb-1">Warnings</div>
                    <ul className="list-disc pl-5 text-yellow-700">
                      {clientWarnings.map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                      {clientWarnings.length === 0 && (
                        <li className="text-gray-500">None</li>
                      )}
                    </ul>
                  </div>
                </div>
              )}
            </CollapsibleSection>
          </div>

          {/* Холст графа */}
          <div className="col-span-3">
            <div
              className="rounded border"
              style={{ maxHeight: "70vh", overflow: "auto" }}
            >
              <GraphCanvas
                nodes={graph.nodes.map((n) => ({
                  key: n.key,
                  title: n.title,
                  type: (n as any).type || "normal",
                }))}
                edges={graph.edges}
                onNodeDoubleClick={(k) => startEditNode(k)}
                onCreateEdge={(from, to) => {
                  setGraph((g) => {
                    if (!g) return g;
                    if (from === to) return g;
                    if (
                      g.edges.some(
                        (e) => e.from_node_key === from && e.to_node_key === to,
                      )
                    )
                      return g;
                    return {
                      ...g,
                      edges: [
                        ...g.edges,
                        {
                          from_node_key: from,
                          to_node_key: to,
                          label: null,
                          condition: null,
                        },
                      ],
                    };
                  });
                }}
                height={520}
              />
            </div>
          </div>
          {showSim && (
            <div className="col-span-3">
              <PlaythroughPanel
                graph={graph}
                onOpenNode={(k) => startEditNode(k)}
              />
            </div>
          )}
        </div>
      )}
      {pickerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white w-full max-w-lg">
            <ContentPicker
              onSelect={(item) => {
                setNodeKey(item.slug);
                setNodeTitle(item.title || item.slug);
                setPickerOpen(false);
              }}
              onClose={() => setPickerOpen(false)}
            />
          </div>
        </div>
      )}
      {editorOpen && editorNode && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white w-full max-w-[95vw] md:max-w-7xl max-h-[92vh] flex flex-col">
            <ContentEditor
              nodeId={editorNode.id}
              data-node="node"
              title={editorNode.title || "Node"}
              statuses={["draft"]}
              versions={[1]}
              toolbar={
                <div className="flex gap-2">
                  <button
                    type="button"
                    className="px-2 py-1 border rounded"
                    disabled={savingNode}
                    onClick={() => commitEditor("save")}
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    className="px-2 py-1 border rounded"
                    onClick={() => setEditorOpen(false)}
                  >
                    Close
                  </button>
                </div>
              }
              general={{
                title: editorNode.title,
                slug: editorNode.slug,
                tags: editorNode.tags.map((t) => t.slug),
                cover: editorNode.coverUrl,
                onTitleChange: (v) =>
                  setEditorNode((p) => (p ? { ...p, title: v } : p)),
                onSlugChange: (v: string) =>
                  setEditorNode((p) => (p ? { ...p, slug: v } : p)),
                onTagsChange: (t: string[]) =>
                  setEditorNode((p) =>
                    p
                      ? {
                          ...p,
                          tags: t.map((s) => ({
                            id: s,
                            slug: s,
                            name: s,
                            count: 0,
                          })),
                        }
                      : p,
                  ),
                onCoverChange: (url) =>
                  setEditorNode((p) => (p ? { ...p, coverUrl: url } : p)),
              }}
                content={{
                  initial: editorNode.contentData,
                  onSave: (d) =>
                    setEditorNode((p) =>
                      p ? { ...p, contentData: d } : p,
                    ),
                }}
              />
          </div>
        </div>
      )}
      </PageLayout>
    </ErrorBoundary>
  );
}

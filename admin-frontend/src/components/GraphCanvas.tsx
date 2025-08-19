import { useCallback, useEffect, useMemo, useRef, useState } from "react";

export type GraphNode = {
  key: string;
  title: string;
  type?: "start" | "normal" | "end";
};

export type GraphEdge = {
  from_node_key: string;
  to_node_key: string;
  label?: string | null;
};

export interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeDoubleClick?: (nodeKey: string) => void;
  onCreateEdge?: (fromKey: string, toKey: string) => void;
  height?: number; // px
}

// Простой layered-лейаут: уровни по расстоянию от стартового узла, fallback — топологическая раскладка
function computeLayout(nodes: GraphNode[], edges: GraphEdge[]) {
  const map = new Map(nodes.map((n) => [n.key, n]));
  const adj = new Map<string, string[]>();
  nodes.forEach((n) => adj.set(n.key, []));
  edges.forEach((e) => {
    if (adj.has(e.from_node_key)) adj.get(e.from_node_key)!.push(e.to_node_key);
  });

  const start = nodes.find((n) => n.type === "start") || nodes[0];
  const level = new Map<string, number>();
  const queue: string[] = [];
  if (start) {
    level.set(start.key, 0);
    queue.push(start.key);
  }
  while (queue.length) {
    const cur = queue.shift()!;
    const next = adj.get(cur) || [];
    for (const to of next) {
      if (!map.has(to)) continue;
      if (!level.has(to)) {
        level.set(to, (level.get(cur) || 0) + 1);
        queue.push(to);
      }
    }
  }
  // Невиданные — ниже всех
  const maxSeen = Math.max(0, ...Array.from(level.values()));
  nodes.forEach((n) => {
    if (!level.has(n.key)) level.set(n.key, maxSeen + 1);
  });

  const byLevel: Record<number, GraphNode[]> = {};
  nodes.forEach((n) => {
    const l = level.get(n.key) || 0;
    if (!byLevel[l]) byLevel[l] = [];
    byLevel[l].push(n);
  });

  const positions = new Map<string, { x: number; y: number }>();
  const colWidth = 220;
  const rowHeight = 140;
  const paddingX = 80;
  const paddingY = 80;
  Object.keys(byLevel)
    .map((k) => Number(k))
    .sort((a, b) => a - b)
    .forEach((l) => {
      const arr = byLevel[l];
      arr.forEach((n, i) => {
        positions.set(n.key, {
          x: paddingX + i * colWidth,
          y: paddingY + l * rowHeight,
        });
      });
    });

  // Габариты холста
  const maxX = Math.max(...Array.from(positions.values()).map((p) => p.x), 0) + 200;
  const maxY = Math.max(...Array.from(positions.values()).map((p) => p.y), 0) + 160;

  return { positions, width: Math.max(maxX, 800), height: Math.max(maxY, 600) };
}

export default function GraphCanvas({ nodes, edges, onNodeDoubleClick, onCreateEdge, height = 560 }: GraphCanvasProps) {
  const { positions, width: contentW, height: contentH } = useMemo(() => computeLayout(nodes, edges), [nodes, edges]);

  // Пан/зум
  const [scale, setScale] = useState(1);
  const [tx, setTx] = useState(0);
  const [ty, setTy] = useState(0);

  // Режим соединения узлов
  const [connectMode, setConnectMode] = useState(false);
  const [connectFrom, setConnectFrom] = useState<string | null>(null);
  const dragging = useRef<{ x: number; y: number; tx: number; ty: number } | null>(null);
  const outerRef = useRef<HTMLDivElement>(null);

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = -e.deltaY;
    const factor = delta > 0 ? 1.1 : 0.9;
    const newScale = Math.min(2.0, Math.max(0.2, scale * factor));
    setScale(newScale);
  };

  const onMouseDown = (e: React.MouseEvent) => {
    // В режиме соединения узлов перетаскивание холста отключаем,
    // чтобы клики по узлам гарантированно проходили.
    if (connectMode) return;
    const rect = outerRef.current?.getBoundingClientRect();
    dragging.current = {
      x: e.clientX - (rect?.left ?? 0),
      y: e.clientY - (rect?.top ?? 0),
      tx,
      ty,
    };
  };
  const onMouseMove = (e: React.MouseEvent) => {
    if (!dragging.current) return;
    const rect = outerRef.current?.getBoundingClientRect();
    const cx = e.clientX - (rect?.left ?? 0);
    const cy = e.clientY - (rect?.top ?? 0);
    const dx = cx - dragging.current.x;
    const dy = cy - dragging.current.y;
    setTx(dragging.current.tx + dx);
    setTy(dragging.current.ty + dy);
  };
  const onMouseUp = () => {
    dragging.current = null;
  };

  const fitToView = useCallback(() => {
    const boxW = outerRef.current?.clientWidth ?? 1;
    const boxH = outerRef.current?.clientHeight ?? 1;
    const sx = boxW / (contentW + 80);
    const sy = boxH / (contentH + 80);
    const s = Math.min(1.5, Math.max(0.2, Math.min(sx, sy)));
    setScale(s);
    setTx((boxW - contentW * s) / 2);
    setTy((boxH - contentH * s) / 2);
  }, [contentW, contentH]);

  useEffect(() => {
    // Авто fit при изменении графа
    fitToView();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes.length, edges.length]);

  // Мини-карта
  const miniW = 160;
  const miniH = Math.max(80, (miniW * contentH) / contentW);
  const viewW = (outerRef.current?.clientWidth ?? 1) / scale;
  const viewH = (outerRef.current?.clientHeight ?? 1) / scale;
  const viewX = -tx / scale;
  const viewY = -ty / scale;

  return (
    <div className="relative border rounded" style={{ height }} ref={outerRef} onWheel={onWheel} onMouseDown={onMouseDown} onMouseMove={onMouseMove} onMouseUp={onMouseUp} onMouseLeave={onMouseUp}>
      <div className="absolute top-2 left-2 z-10 flex gap-2">
        <button className="px-2 py-1 rounded border bg-white/80" onClick={fitToView}>Fit</button>
        <button className="px-2 py-1 rounded border bg-white/80" onClick={() => { setScale(1); setTx(0); setTy(0); }}>Reset</button>
        <button
          className={`px-2 py-1 rounded border ${connectMode ? "bg-blue-600 text-white" : "bg-white/80"}`}
          onClick={() => {
            setConnectMode((v) => !v);
            setConnectFrom(null);
          }}
          title="Create edge by clicking source and target nodes"
        >
          {connectMode ? "Connecting…" : "Connect"}
        </button>
        {connectMode && (
          <span className="px-2 py-1 rounded bg-white/80 border">
            {connectFrom ? `from: ${connectFrom} → click target` : "click source node"}
          </span>
        )}
      </div>

      <svg
        className="absolute inset-0"
        width="100%"
        height="100%"
        style={{ background: "transparent" }}
      >
        <g transform={`translate(${tx}, ${ty}) scale(${scale})`}>
          {/* Ребра */}
          {edges.map((e, i) => {
            const a = positions.get(e.from_node_key);
            const b = positions.get(e.to_node_key);
            if (!a || !b) return null;
            const x1 = a.x + 120;
            const y1 = a.y + 40;
            const x2 = b.x + 120;
            const y2 = b.y + 40;
            const midY = (y1 + y2) / 2;
            return (
              <g key={i}>
                {/* Ломаная под 90°: вниз до середины, затем к x2, затем вниз до y2 */}
                <path d={`M ${x1} ${y1} L ${x1} ${midY} L ${x2} ${midY} L ${x2} ${y2}`} stroke="#8ba3c7" fill="none" strokeWidth={1.5} />
                {e.label && (
                  <text x={(x1 + x2) / 2} y={midY - 6} textAnchor="middle" fontSize="10" fill="#567" >{e.label}</text>
                )}
              </g>
            );
          })}

          {/* Узлы */}
          {nodes.map((n) => {
            const pos = positions.get(n.key);
            if (!pos) return null;
            const w = 240;
            const h = 80;
            const rx = 8;
            const color =
              n.type === "start" ? "#15a34a" : n.type === "end" ? "#7c3aed" : "#2563eb";
            const highlight = connectMode && (connectFrom === null || connectFrom === n.key);
            return (
              <g
                key={n.key}
                transform={`translate(${pos.x}, ${pos.y})`}
                style={{ cursor: "pointer" }}
                onMouseDown={(e) => e.stopPropagation()}
                onDoubleClick={() => onNodeDoubleClick?.(n.key)}
                onClick={() => {
                  if (!connectMode) return;
                  if (!connectFrom) {
                    setConnectFrom(n.key);
                  } else if (connectFrom && n.key === connectFrom) {
                    // повторный клик по источнику — отменяем выбор
                    setConnectFrom(null);
                  } else if (connectFrom && n.key !== connectFrom) {
                    onCreateEdge?.(connectFrom, n.key);
                    setConnectFrom(null);
                    setConnectMode(false);
                  }
                }}
              >
                <rect width={w} height={h} rx={rx} ry={rx} fill={highlight ? "#eef2ff" : "#fff"} stroke={color} strokeWidth={2} />
                <rect x={0} y={0} width={6} height={h} fill={color} />
                <text x={16} y={22} fontSize="12" fontWeight={700} fill="#0f172a">{n.key}</text>
                <text x={16} y={42} fontSize="13" fill="#334155">{n.title}</text>
                <text x={16} y={62} fontSize="11" fill="#64748b">{n.type || "normal"}</text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Мини-карта */}
      <div className="absolute bottom-2 right-2 bg-white/90 rounded shadow p-2">
        <svg width={miniW} height={miniH}>
          {/* фон мини-карты */}
          <rect x={0} y={0} width={miniW} height={miniH} fill="#f8fafc" stroke="#cbd5e1" />
          {/* узлы */}
          {nodes.map((n) => {
            const p = positions.get(n.key);
            if (!p) return null;
            const mx = (p.x / contentW) * miniW;
            const my = (p.y / contentH) * miniH;
            const mw = (240 / contentW) * miniW;
            const mh = (80 / contentH) * miniH;
            const fill =
              n.type === "start" ? "#86efac" : n.type === "end" ? "#ddd6fe" : "#bfdbfe";
            return <rect key={n.key} x={mx} y={my} width={mw} height={mh} fill={fill} stroke="#94a3b8" />;
          })}
          {/* видимая область */}
          <rect
            x={(viewX / contentW) * miniW}
            y={(viewY / contentH) * miniH}
            width={(viewW / contentW) * miniW}
            height={(viewH / contentH) * miniH}
            fill="none"
            stroke="#0ea5e9"
            strokeWidth={1.5}
          />
        </svg>
      </div>
    </div>
  );
}

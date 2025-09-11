// @ts-nocheck
import { useEffect, useMemo, useState } from 'react';

import type {
  GraphEdgeOutput as GraphEdge,
  GraphNodeOutput as GraphNode,
  VersionGraphOutput as VersionGraph,
} from '../openapi';

function buildAdj(edges: GraphEdge[]): Record<string, { to: string; label?: string | null }[]> {
  const m: Record<string, { to: string; label?: string | null }[]> = {};
  for (const e of edges) {
    if (!m[e.from_node_key]) m[e.from_node_key] = [];
    m[e.from_node_key].push({ to: e.to_node_key, label: e.label });
  }
  return m;
}

function findStart(nodes: GraphNode[]): GraphNode | null {
  if (!nodes || nodes.length === 0) return null;
  const start = nodes.find((n) => n.type === 'start');
  return start || nodes[0];
}

export default function PlaythroughPanel({
  graph,
  onOpenNode,
}: {
  graph: VersionGraph;
  onOpenNode?: (key: string) => void;
}) {
  const adj = useMemo(() => buildAdj(graph.edges || []), [graph.edges]);
  const nodesByKey = useMemo(() => {
    const m: Record<string, GraphNode> = {};
    for (const n of graph.nodes || []) m[n.key] = n;
    return m;
  }, [graph.nodes]);

  const start = useMemo(() => findStart(graph.nodes || []), [graph.nodes]);

  const [current, setCurrent] = useState<string | null>(start ? start.key : null);
  const [path, setPath] = useState<string[]>(current ? [current] : []);

  useEffect(() => {
    const s = findStart(graph.nodes || []);
    const key = s ? s.key : null;
    setCurrent(key);
    setPath(key ? [key] : []);
  }, [graph]);

  const outgoing = useMemo(() => (current ? adj[current] || [] : []), [adj, current]);
  const node = current ? nodesByKey[current] : null;
  const isEnd = node
    ? node.type === 'end' || (outgoing.length === 0 && node.type !== 'start')
    : false;

  const moveTo = (nextKey: string) => {
    setCurrent(nextKey);
    setPath((arr) => [...arr, nextKey]);
  };

  const reset = () => {
    const key = start ? start.key : null;
    setCurrent(key);
    setPath(key ? [key] : []);
  };

  const back = () => {
    setPath((arr) => {
      if (arr.length <= 1) return arr;
      const next = arr.slice(0, arr.length - 1);
      setCurrent(next[next.length - 1] || null);
      return next;
    });
  };

  const randomStep = () => {
    if (outgoing.length === 0) return;
    const i = Math.floor(Math.random() * outgoing.length);
    moveTo(outgoing[i].to);
  };

  return (
    <div className="rounded border p-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Playthrough</h3>
        <div className="flex items-center gap-2">
          <button className="px-2 py-1 rounded border" onClick={reset} disabled={!start}>
            Reset
          </button>
          <button
            className="px-2 py-1 rounded border"
            onClick={back}
            disabled={(path.length || 0) <= 1}
          >
            Back
          </button>
          <button
            className="px-2 py-1 rounded border"
            onClick={randomStep}
            disabled={outgoing.length === 0}
          >
            Random
          </button>
        </div>
      </div>

      <div className="mt-3 text-sm">
        <div className="mb-2">
          <span className="text-gray-600">Path:</span>{' '}
          {path.length === 0 ? (
            <i className="text-gray-500">—</i>
          ) : (
            <span className="font-mono">
              {path.map((k, i) => (
                <span key={`${k}-${i}`}>
                  {i > 0 ? ' › ' : ''}
                  <button className="underline" onClick={() => setCurrent(k)}>
                    {k}
                  </button>
                </span>
              ))}
            </span>
          )}
        </div>
        {node ? (
          <div className="mb-3">
            <div className="flex items-center gap-2">
              <div className="font-semibold">{node.title || node.key}</div>
              <span className="text-xs px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-800">
                {node.type || 'normal'}
              </span>
              {isEnd && (
                <span className="text-xs px-2 py-0.5 rounded bg-green-200 text-green-800">END</span>
              )}
              {onOpenNode && (
                <button className="text-xs underline" onClick={() => onOpenNode(node.key)}>
                  open
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="text-gray-500">No current node</div>
        )}

        <div>
          <div className="text-gray-600 mb-1">Choices:</div>
          {outgoing.length === 0 ? (
            <div className="text-gray-500">No outgoing edges</div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {outgoing.map((e, i) => (
                <button
                  key={`${e.to}-${i}`}
                  className="px-2 py-1 rounded border"
                  onClick={() => moveTo(e.to)}
                  title={e.to}
                >
                  {e.label || nodesByKey[e.to]?.title || e.to}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

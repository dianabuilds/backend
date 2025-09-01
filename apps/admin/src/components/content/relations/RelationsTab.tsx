import { useEffect, useState } from "react";

import { listTransitions, type Transition } from "../../../api/transitions";
import { getVersion } from "../../../api/questEditor";
import type {
  GraphEdgeOutput,
  GraphNodeOutput,
} from "../../../openapi";

interface RelationsTabProps {
  nodeId?: number;
  slug: string;
  nodeType?: string;
}

export default function RelationsTab({
  nodeId,
  slug,
  nodeType,
}: RelationsTabProps) {
  const [outgoing, setOutgoing] = useState<Transition[]>([]);
  const [incoming, setIncoming] = useState<Transition[]>([]);
  const [nodes, setNodes] = useState<GraphNodeOutput[]>([]);
  const [edges, setEdges] = useState<GraphEdgeOutput[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!slug) return;
      try {
        const [out, inc] = await Promise.all([
          listTransitions({ from_slug: slug, limit: 50 }),
          listTransitions({ to_slug: slug, limit: 50 }),
        ]);
        setOutgoing(out);
        setIncoming(inc);
        if (nodeType === "quest" && nodeId !== undefined) {
          try {
            const graph = await getVersion(String(nodeId));
            setNodes(graph.nodes || []);
            setEdges(graph.edges || []);
          } catch (e) {
            // eslint-disable-next-line no-console
            console.error(e);
          }
        } else {
          setNodes([]);
          setEdges([]);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    };
    load();
  }, [slug, nodeId, nodeType]);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="font-semibold mb-2">Transitions</h2>
        <div className="flex gap-8 flex-wrap">
          <div>
            <h3 className="font-medium">Outgoing</h3>
            <ul className="list-disc pl-4">
              {outgoing.length === 0 && (
                <li className="text-gray-500">none</li>
              )}
              {outgoing.map((t) => (
                <li key={t.id}>
                  {t.to_slug}
                  {t.label ? ` (${t.label})` : ""}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="font-medium">Incoming</h3>
            <ul className="list-disc pl-4">
              {incoming.length === 0 && (
                <li className="text-gray-500">none</li>
              )}
              {incoming.map((t) => (
                <li key={t.id}>
                  {t.from_slug}
                  {t.label ? ` (${t.label})` : ""}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
      {nodeType === "quest" && (
        <div>
          <h2 className="font-semibold mb-2">Quest graph</h2>
          <div className="flex gap-8 flex-wrap">
            <div>
              <h3 className="font-medium">Nodes</h3>
              <ul className="list-disc pl-4">
                {nodes.length === 0 && (
                  <li className="text-gray-500">none</li>
                )}
                {nodes.map((n) => (
                  <li key={n.key}>
                    {n.key}: {n.title}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-medium">Transitions</h3>
              <ul className="list-disc pl-4">
                {edges.length === 0 && (
                  <li className="text-gray-500">none</li>
                )}
                {edges.map((e, i) => (
                  <li key={i}>
                    {e.from_node_key} → {e.to_node_key}
                    {e.label ? ` (${e.label})` : ""}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
      {error && <p className="text-red-600">{error}</p>}
    </div>
  );
}


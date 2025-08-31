import { useEffect, useState } from 'react';
import { listNavigationProblems, type NavigationProblem } from '../api/navigationProblems';
import { listTransitions } from '../api/transitions';
import GraphCanvas from '../components/GraphCanvas';
import type { GraphEdge, GraphNode } from '../components/GraphCanvas.helpers';

export default function NavigationProblems() {
  const [items, setItems] = useState<NavigationProblem[]>([]);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);

  useEffect(() => {
    listNavigationProblems().then(setItems).catch((e) => {
      // eslint-disable-next-line no-console
      console.error(e);
    });
  }, []);

  const openGraph = async (slug: string) => {
    const transitions = await listTransitions({ from_slug: slug, limit: 50 });
    const gNodes: GraphNode[] = [{ key: slug, title: slug }];
    const gEdges: GraphEdge[] = [];
    const seen = new Set([slug]);
    for (const t of transitions) {
      const to = t.to_slug || '';
      if (!seen.has(to)) {
        gNodes.push({ key: to, title: to });
        seen.add(to);
      }
      gEdges.push({ from_node_key: slug, to_node_key: to, label: t.label });
    }
    setNodes(gNodes);
    setEdges(gEdges);
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Navigation problems</h1>
      <table className="min-w-full text-sm border">
        <thead>
          <tr className="bg-gray-50">
            <th className="p-2 text-left">Slug</th>
            <th className="p-2 text-left">CTR</th>
            <th className="p-2 text-left">Dead end</th>
            <th className="p-2 text-left">Cycle</th>
            <th className="p-2"></th>
          </tr>
        </thead>
        <tbody>
          {items.map((p) => (
            <tr key={p.node_id} className="border-t">
              <td className="p-2">{p.slug}</td>
              <td className="p-2">{(p.ctr * 100).toFixed(1)}%</td>
              <td className="p-2">{p.dead_end ? 'Yes' : ''}</td>
              <td className="p-2">{p.cycle ? 'Yes' : ''}</td>
              <td className="p-2 text-right">
                <button
                  onClick={() => openGraph(p.slug)}
                  className="px-2 py-1 text-sm bg-blue-600 text-white rounded"
                >
                  Open graph
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {nodes.length > 0 && (
        <GraphCanvas nodes={nodes} edges={edges} height={400} />
      )}
    </div>
  );
}

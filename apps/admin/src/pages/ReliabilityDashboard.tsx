import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import KpiCard from "../components/KpiCard";
import GraphCanvas from "../components/GraphCanvas";
import type { GraphEdge, GraphNode } from "../components/GraphCanvas.helpers";
import { getReliabilityMetrics, type ReliabilityMetrics } from "../api/metrics";
import { useWorkspace } from "../workspace/WorkspaceContext";

export default function ReliabilityDashboard() {
  const { workspaceId } = useWorkspace();

  const { data, isLoading, error } = useQuery({
    queryKey: ["reliability-metrics", workspaceId],
    queryFn: () => getReliabilityMetrics(workspaceId),
    enabled: !!workspaceId,
    refetchInterval: 15000,
  });

  const metrics: ReliabilityMetrics = data || {
    rps: 0,
    p95: 0,
    errors_4xx: 0,
    errors_5xx: 0,
    no_route_percent: 0,
    fallback_percent: 0,
  };

  const { nodes, edges } = useMemo(() => {
    const nodes: GraphNode[] = [
      { key: "root", title: "Metrics", type: "start" },
      { key: "rps", title: `RPS: ${metrics.rps.toFixed(2)}` },
      { key: "p95", title: `p95: ${metrics.p95.toFixed(2)}ms` },
      { key: "4xx", title: `4xx: ${metrics.errors_4xx.toFixed(2)}` },
      { key: "5xx", title: `5xx: ${metrics.errors_5xx.toFixed(2)}` },
      {
        key: "no_route",
        title: `No route: ${metrics.no_route_percent.toFixed(2)}%`,
      },
      {
        key: "fallback",
        title: `Fallback: ${metrics.fallback_percent.toFixed(2)}%`,
      },
    ];
    const edges: GraphEdge[] = nodes
      .filter((n) => n.key !== "root")
      .map((n) => ({ from_node_key: "root", to_node_key: n.key }));
    return { nodes, edges };
  }, [metrics]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Reliability</h1>
      <div className="flex flex-wrap items-end gap-2">
        <span className="text-sm text-gray-600">
          Workspace: {workspaceId || "(none)"}
        </span>
      </div>
      {isLoading && <div className="text-sm text-gray-500">Loading…</div>}
      {error && (
        <div className="text-sm text-red-600">{(error as any).message}</div>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        <KpiCard title="RPS" value={metrics.rps.toFixed(2)} />
        <KpiCard title="p95 latency" value={`${metrics.p95.toFixed(2)} ms`} />
        <KpiCard title="4xx/min" value={metrics.errors_4xx.toFixed(2)} />
        <KpiCard title="5xx/min" value={metrics.errors_5xx.toFixed(2)} />
        <KpiCard
          title="No route %"
          value={`${metrics.no_route_percent.toFixed(2)}%`}
        />
        <KpiCard
          title="Fallback %"
          value={`${metrics.fallback_percent.toFixed(2)}%`}
        />
      </div>
      <GraphCanvas nodes={nodes} edges={edges} height={400} />
    </div>
  );
}


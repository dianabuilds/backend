import { useQuery } from "@tanstack/react-query";

import { getEventCounters } from "../api/metrics";

export default function WorkspaceMetrics() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["workspace-metrics"],
    queryFn: getEventCounters,
    refetchInterval: 10000,
  });

  const counters = data || {};

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Workspace Metrics</h1>
      {isLoading && <div className="text-sm text-gray-500">Loading…</div>}
      {error && (
        <div className="text-sm text-red-600">{(error as any).message}</div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left">
              <th className="px-2 py-1">Workspace</th>
              <th className="px-2 py-1">Node visits</th>
              <th className="px-2 py-1">Publishes</th>
              <th className="px-2 py-1">Achievements</th>
              <th className="px-2 py-1">Compass</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(counters).map(([ws, evs]) => (
              <tr key={ws} className="border-t">
                <td className="px-2 py-1">{ws}</td>
                <td className="px-2 py-1">{evs["node_visit"] || 0}</td>
                <td className="px-2 py-1">{evs["publish"] || 0}</td>
                <td className="px-2 py-1">{evs["achievement"] || 0}</td>
                <td className="px-2 py-1">{evs["compass"] || 0}</td>
              </tr>
            ))}
            {Object.keys(counters).length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="px-2 py-3 text-gray-500 text-center"
                >
                  No data
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

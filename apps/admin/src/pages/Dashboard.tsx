import { useQuery } from "@tanstack/react-query";
import KpiCard from "../components/KpiCard";
import { api } from "../api/client";

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: async () => (await api.get("/admin/dashboard")).data,
  });

  const kpi = data?.kpi || {};
  const subsChange = kpi.active_subscriptions_change_pct ?? 0;
  const subsChangeColor = subsChange >= 0 ? "text-green-600" : "text-red-600";

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-2 text-sm">
          <span className="rounded bg-green-100 px-2 py-1 text-green-800 dark:bg-green-900 dark:text-green-100">
            System OK
          </span>
          <span className="rounded bg-blue-100 px-2 py-1 text-blue-800 dark:bg-blue-900 dark:text-blue-100">
            Global
          </span>
          <span className="rounded bg-gray-100 px-2 py-1 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
            active
          </span>
        </div>
      </header>

      {isLoading && <div className="text-sm text-gray-500">Loading…</div>}
      {!isLoading && (
        <div className="grid gap-4 md:grid-cols-5">
          <KpiCard title="Active users (24h)" value={kpi.active_users_24h ?? 0} />
          <KpiCard title="New registrations (24h)" value={kpi.new_registrations_24h ?? 0} />
          <KpiCard title="Active premium" value={kpi.active_premium ?? 0} />
          <KpiCard
            title="Active subscriptions"
            value={
              <>
                {kpi.active_subscriptions ?? 0}
                <span className={`ml-1 text-sm ${subsChangeColor}`}>
                  {subsChange >= 0 ? "+" : ""}
                  {subsChange.toFixed(1)}%
                </span>
              </>
            }
          />
          <KpiCard title="Nodes (24h)" value={kpi.nodes_24h ?? 0} />
          <KpiCard title="Quests (24h)" value={kpi.quests_24h ?? 0} />
          <KpiCard
            title="Incidents (24h)"
            value={
              <span className={kpi.incidents_24h ? "text-red-600" : ""}>
                {kpi.incidents_24h ?? 0}
              </span>
            }
          />
        </div>
      )}
    </div>
  );
}


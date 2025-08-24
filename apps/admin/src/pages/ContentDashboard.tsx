import { useQuery } from "@tanstack/react-query";

import { createNode, listNodes } from "../api/client";
import KpiCard from "../components/KpiCard";

interface DashboardData {
  drafts: number;
  reviews: number;
  published: number;
  latest: { id: string; type: string; status: string }[];
  validation_errors: { id: string; type: string; errors: number }[];
}

export default function ContentDashboard() {
  const { data, refetch, isLoading } = useQuery({
    queryKey: ["content", "dashboard"],
    queryFn: async () => {
      const items = await listNodes();
      const drafts = items.filter((i: any) => i.status === "draft").length;
      const reviews = items.filter((i: any) => i.status === "review").length;
      const published = items.filter(
        (i: any) => i.status === "published",
      ).length;
      return {
        drafts,
        reviews,
        published,
        latest: items
          .slice(0, 5)
          .map((i: any) => ({ id: i.id, type: i.type, status: i.status })),
        validation_errors: [],
      } as DashboardData;
    },
  });

  const createItem = async (type: string) => {
    await createNode(type);
    refetch();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Content Dashboard</h1>
      {isLoading && <div className="text-sm text-gray-500">Loading…</div>}
      {data && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <KpiCard title="Drafts" value={data.drafts} />
            <KpiCard title="Review" value={data.reviews} />
            <KpiCard title="Published" value={data.published} />
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold">Quick actions</h2>
            <div className="flex gap-2">
              <button
                className="rounded border px-2 py-1 text-sm"
                onClick={() => createItem("quest")}
              >
                New quest
              </button>
              <button
                className="rounded border px-2 py-1 text-sm"
                onClick={() => createItem("world")}
              >
                New world
              </button>
              <button
                className="rounded border px-2 py-1 text-sm"
                onClick={() => createItem("other")}
              >
                New other
              </button>
            </div>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold">Latest changes</h2>
            <ul className="space-y-1 text-sm">
              {data.latest.length > 0 ? (
                data.latest.map((item) => (
                  <li key={item.id}>
                    {item.type} – {item.status}
                  </li>
                ))
              ) : (
                <li>No items</li>
              )}
            </ul>
          </div>

          <div>
            <h2 className="mb-2 text-lg font-semibold">Validation errors</h2>
            <ul className="space-y-1 text-sm">
              {data.validation_errors.length > 0 ? (
                data.validation_errors.map((v) => (
                  <li key={v.id}>
                    {v.type} – {v.errors} errors
                  </li>
                ))
              ) : (
                <li>No errors</li>
              )}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}

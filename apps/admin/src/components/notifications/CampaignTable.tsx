import { useQuery } from "@tanstack/react-query";
import { type Campaign, listBroadcasts } from "../../api/notifications";

export default function CampaignTable() {
  const { data, isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => listBroadcasts(),
    refetchInterval: 10000,
  });

  if (isLoading) return <p>Loading…</p>;

  const campaigns = data || [];

  return (
    <table className="min-w-full text-sm">
      <thead>
        <tr className="border-b">
          <th className="p-2 text-left">Title</th>
          <th className="p-2 text-left">Type</th>
          <th className="p-2 text-left">Status</th>
          <th className="p-2 text-left">Progress</th>
          <th className="p-2 text-left">Created</th>
          <th className="p-2 text-left">Started</th>
          <th className="p-2 text-left">Finished</th>
        </tr>
      </thead>
      <tbody>
        {campaigns.map((c: Campaign) => (
          <tr key={c.id} className="border-b">
            <td className="p-2">{c.title}</td>
            <td className="p-2">{c.type}</td>
            <td className="p-2">{c.status}</td>
            <td className="p-2">
              {c.sent} / {c.total}
            </td>
            <td className="p-2">
              {c.created_at ? new Date(c.created_at).toLocaleString() : "-"}
            </td>
            <td className="p-2">
              {c.started_at ? new Date(c.started_at).toLocaleString() : "-"}
            </td>
            <td className="p-2">
              {c.finished_at ? new Date(c.finished_at).toLocaleString() : "-"}
            </td>
          </tr>
        ))}
        {campaigns.length === 0 && (
          <tr>
            <td className="p-2 text-gray-500" colSpan={7}>
              No campaigns
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}

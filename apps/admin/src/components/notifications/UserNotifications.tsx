import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listNotifications,
  markNotificationRead,
  type NotificationItem,
} from "../../api/notifications";
import { useToast } from "../ToastProvider";

export default function UserNotifications() {
  const { addToast } = useToast();
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => listNotifications(),
    refetchInterval: 30000,
  });

  const handleRead = async (id: string) => {
    try {
      await markNotificationRead(id);
      qc.invalidateQueries({ queryKey: ["notifications"] });
    } catch (e) {
      addToast({
        title: "Failed to mark as read",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  if (isLoading) return <p>Loading…</p>;
  if (error) return <p className="text-red-600">{(error as Error).message}</p>;

  const items = data || [];

  return (
    <table className="min-w-full text-sm">
      <thead>
        <tr className="border-b">
          <th className="p-2 text-left">Title</th>
          <th className="p-2 text-left">Message</th>
          <th className="p-2 text-left">Type</th>
          <th className="p-2 text-left">Created</th>
          <th className="p-2 text-left">Read</th>
          <th className="p-2 text-left">Actions</th>
        </tr>
      </thead>
      <tbody>
        {items.map((n: NotificationItem) => (
          <tr key={n.id} className="border-b">
            <td className="p-2">{n.title}</td>
            <td className="p-2">{n.message}</td>
            <td className="p-2">{n.type ?? "system"}</td>
            <td className="p-2">{new Date(n.created_at).toLocaleString()}</td>
            <td className="p-2">
              {n.read_at ? new Date(n.read_at).toLocaleString() : "-"}
            </td>
            <td className="p-2">
              {!n.read_at && (
                <button
                  className="px-2 py-1 rounded border"
                  onClick={() => handleRead(n.id)}
                >
                  Mark read
                </button>
              )}
            </td>
          </tr>
        ))}
        {items.length === 0 && (
          <tr>
            <td className="p-2 text-gray-500" colSpan={6}>
              No notifications
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}

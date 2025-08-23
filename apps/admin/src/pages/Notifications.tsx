import { useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { useToast } from "../components/ToastProvider";
import { useAuth } from "../auth/AuthContext";
import { createBroadcast, listBroadcasts, type BroadcastCreate, type Campaign } from "../api/notifications";

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type?: string | null;
  read_at?: string | null;
  created_at: string;
}

function ensureArray<T = any>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as any;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (Array.isArray(obj.data)) return obj.data as T[];
  }
  return [];
}

async function fetchMyNotifications(): Promise<NotificationItem[]> {
  const res = await api.get("/notifications");
  return ensureArray<NotificationItem>(res.data);
}

async function markRead(id: string) {
  await api.post(`/notifications/${id}/read`, {});
}

async function sendNotification(payload: { user_id: string; title: string; message: string; type: string }) {
  await api.post("/admin/notifications", payload);
}

export default function Notifications() {
  const { user } = useAuth();
  const { addToast } = useToast();
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["notifications"],
    queryFn: fetchMyNotifications,
    refetchInterval: 30000,
  });

  const [targetUser, setTargetUser] = useState("");
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [type, setType] = useState("system");

  useEffect(() => {
    if (user && !targetUser) setTargetUser(user.id);
  }, [user]);

  const handleSend = async () => {
    try {
      await sendNotification({ user_id: targetUser, title, message, type });
      addToast({ title: "Notification sent", variant: "success" });
      setMessage("");
      setTitle("");
    } catch (e) {
      addToast({ title: "Failed to send notification", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const handleRead = async (id: string) => {
    try {
      await markRead(id);
      qc.invalidateQueries({ queryKey: ["notifications"] });
    } catch (e) {
      addToast({ title: "Failed to mark as read", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  // Broadcast state
  const [bType, setBType] = useState<"system" | "info" | "warning" | "quest">("system");
  const [bTitle, setBTitle] = useState("");
  const [bMessage, setBMessage] = useState("");
  const [role, setRole] = useState<string>("");
  const [isActive, setIsActive] = useState<string>("any"); // any|true|false
  const [isPremium, setIsPremium] = useState<string>("any"); // any|true|false
  const [createdFrom, setCreatedFrom] = useState<string>("");
  const [createdTo, setCreatedTo] = useState<string>("");
  const [estimate, setEstimate] = useState<number | null>(null);

  const payloadFilters = useMemo(() => {
    const f: any = {};
    if (role) f.role = role;
    if (isActive !== "any") f.is_active = isActive === "true";
    if (isPremium !== "any") f.is_premium = isPremium === "true";
    if (createdFrom) f.created_from = new Date(createdFrom).toISOString();
    if (createdTo) f.created_to = new Date(createdTo).toISOString();
    return f;
  }, [role, isActive, isPremium, createdFrom, createdTo]);

  const doDryRun = async () => {
    try {
      const res = await createBroadcast({
        title: bTitle,
        message: bMessage,
        type: bType,
        filters: payloadFilters,
        dry_run: true,
      } as BroadcastCreate);
      setEstimate((res as any).total_estimate ?? 0);
      addToast({ title: "Estimated recipients", description: String((res as any).total_estimate ?? 0), variant: "info" });
    } catch (e) {
      addToast({ title: "Dry-run failed", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const doStart = async () => {
    try {
      await createBroadcast({
        title: bTitle,
        message: bMessage,
        type: bType,
        filters: payloadFilters,
      } as BroadcastCreate);
      setEstimate(null);
      setBMessage("");
      setBTitle("");
      addToast({ title: "Broadcast started", variant: "success" });
      qc.invalidateQueries({ queryKey: ["campaigns"] });
    } catch (e) {
      addToast({ title: "Failed to start broadcast", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const { data: campaigns } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => listBroadcasts(),
    refetchInterval: 10000,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Notifications</h1>

      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">Broadcast</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Title</label>
            <input className="border rounded px-2 py-1" value={bTitle} onChange={(e) => setBTitle(e.target.value)} />
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Type</label>
            <select className="border rounded px-2 py-1" value={bType} onChange={(e) => setBType(e.target.value as any)}>
              <option value="system">system</option>
              <option value="info">info</option>
              <option value="warning">warning</option>
              <option value="quest">quest</option>
            </select>
          </div>
          <div className="md:col-span-2 flex flex-col">
            <label className="text-sm text-gray-600">Message</label>
            <textarea className="border rounded px-2 py-1" rows={3} value={bMessage} onChange={(e) => setBMessage(e.target.value)} />
          </div>

          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Role</label>
            <select className="border rounded px-2 py-1" value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="">any</option>
              <option value="user">user</option>
              <option value="moderator">moderator</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Active</label>
            <select className="border rounded px-2 py-1" value={isActive} onChange={(e) => setIsActive(e.target.value)}>
              <option value="any">any</option>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Premium</label>
            <select className="border rounded px-2 py-1" value={isPremium} onChange={(e) => setIsPremium(e.target.value)}>
              <option value="any">any</option>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Created from</label>
            <input type="datetime-local" className="border rounded px-2 py-1" value={createdFrom} onChange={(e) => setCreatedFrom(e.target.value)} />
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Created to</label>
            <input type="datetime-local" className="border rounded px-2 py-1" value={createdTo} onChange={(e) => setCreatedTo(e.target.value)} />
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <button className="px-3 py-1 rounded border" onClick={doDryRun}>Estimate</button>
          <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={doStart}>Start broadcast</button>
          {estimate !== null && <span className="text-sm text-gray-600">Estimated recipients: {estimate}</span>}
        </div>
      </section>

      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">Campaigns</h2>
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
            {(campaigns || []).map((c: Campaign) => (
              <tr key={c.id} className="border-b">
                <td className="p-2">{c.title}</td>
                <td className="p-2">{c.type}</td>
                <td className="p-2">{c.status}</td>
                <td className="p-2">{c.sent} / {c.total}</td>
                <td className="p-2">{c.created_at ? new Date(c.created_at).toLocaleString() : "-"}</td>
                <td className="p-2">{c.started_at ? new Date(c.started_at).toLocaleString() : "-"}</td>
                <td className="p-2">{c.finished_at ? new Date(c.finished_at).toLocaleString() : "-"}</td>
              </tr>
            ))}
            {(!campaigns || campaigns.length === 0) && <tr><td className="p-2 text-gray-500" colSpan={7}>No campaigns</td></tr>}
          </tbody>
        </table>
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-2">Send notification</h2>
        <div className="flex flex-wrap items-end gap-2">
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">User ID</label>
            <input className="border rounded px-2 py-1 w-80" value={targetUser} onChange={(e) => setTargetUser(e.target.value)} placeholder="UUID" />
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-600">Type</label>
            <select className="border rounded px-2 py-1" value={type} onChange={(e) => setType(e.target.value)}>
              <option value="system">system</option>
              <option value="info">info</option>
              <option value="warning">warning</option>
              <option value="quest">quest</option>
            </select>
          </div>
          <div className="flex-1 flex flex-col min-w-[220px]">
            <label className="text-sm text-gray-600">Title</label>
            <input className="border rounded px-2 py-1" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div className="flex-1 flex flex-col min-w-[220px]">
            <label className="text-sm text-gray-600">Message</label>
            <input className="border rounded px-2 py-1" value={message} onChange={(e) => setMessage(e.target.value)} />
          </div>
          <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={handleSend}>Send</button>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-lg font-semibold mb-2">My notifications</h2>
        {isLoading && <p>Loading…</p>}
        {error && <p className="text-red-600">{(error as Error).message}</p>}
        {!isLoading && !error && (
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
              {(data || []).map((n) => (
                <tr key={n.id} className="border-b">
                  <td className="p-2">{n.title}</td>
                  <td className="p-2">{n.message}</td>
                  <td className="p-2">{n.type ?? "system"}</td>
                  <td className="p-2">{new Date(n.created_at).toLocaleString()}</td>
                  <td className="p-2">{n.read_at ? new Date(n.read_at).toLocaleString() : "-"}</td>
                  <td className="p-2">
                    {!n.read_at && (
                      <button className="px-2 py-1 rounded border" onClick={() => handleRead(n.id)}>
                        Mark read
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {(!data || data.length === 0) && (
                <tr><td className="p-2 text-gray-500" colSpan={6}>No notifications</td></tr>
              )}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

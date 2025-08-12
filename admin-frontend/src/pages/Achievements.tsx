import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { useToast } from "../components/ToastProvider";

interface AchievementItem {
  id: string;
  code: string;
  title: string;
  description?: string | null;
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

async function fetchAchievements(): Promise<AchievementItem[]> {
  const res = await api.get("/achievements");
  return ensureArray<AchievementItem>(res.data);
}

async function grantAchievement(id: string, user_id: string) {
  await api.post(`/admin/achievements/${id}/grant`, { user_id });
}

async function revokeAchievement(id: string, user_id: string) {
  await api.post(`/admin/achievements/${id}/revoke`, { user_id });
}

export default function Achievements() {
  const { addToast } = useToast();
  const qc = useQueryClient();
  const [userId, setUserId] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["achievements"],
    queryFn: fetchAchievements,
  });

  const handleGrant = async (id: string) => {
    if (!userId) return;
    try {
      await grantAchievement(id, userId);
      addToast({ title: "Achievement granted", variant: "success" });
      qc.invalidateQueries({ queryKey: ["achievements"] });
    } catch (e) {
      addToast({ title: "Failed to grant", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const handleRevoke = async (id: string) => {
    if (!userId) return;
    try {
      await revokeAchievement(id, userId);
      addToast({ title: "Achievement revoked", variant: "success" });
      qc.invalidateQueries({ queryKey: ["achievements"] });
    } catch (e) {
      addToast({ title: "Failed to revoke", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Achievements</h1>
      <div className="mb-4 flex items-center gap-2">
        <input
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="User ID"
          className="border rounded px-2 py-1 font-mono"
        />
      </div>
      {isLoading && <p>Loading…</p>}
      {error && <p className="text-red-600">{(error as Error).message}</p>}
      {!isLoading && !error && (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">Code</th>
              <th className="p-2 text-left">Title</th>
              <th className="p-2 text-left">Description</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(data || []).map((a) => (
              <tr key={a.id} className="border-b">
                <td className="p-2 font-mono">{a.code}</td>
                <td className="p-2">{a.title}</td>
                <td className="p-2">{a.description ?? ""}</td>
                <td className="p-2 space-x-2">
                  <button
                    className="px-2 py-1 rounded border"
                    disabled={!userId}
                    onClick={() => handleGrant(a.id)}
                  >
                    Grant
                  </button>
                  <button
                    className="px-2 py-1 rounded border"
                    disabled={!userId}
                    onClick={() => handleRevoke(a.id)}
                  >
                    Revoke
                  </button>
                </td>
              </tr>
            ))}
            {(!data || data.length === 0) && (
              <tr>
                <td className="p-2 text-gray-500" colSpan={4}>
                  No achievements
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}


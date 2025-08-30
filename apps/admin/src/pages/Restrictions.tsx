import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../api/client";
import { ensureArray } from "../shared/utils";

interface Restriction {
  id: string;
  user_id: string;
  type: string;
  reason?: string | null;
  expires_at?: string | null;
  issued_by?: string | null;
  created_at: string;
}

async function fetchRestrictions(): Promise<Restriction[]> {
  const res = await api.get("/admin/restrictions");
  return ensureArray<Restriction>(res.data);
}

export default function Restrictions() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["restrictions"],
    queryFn: fetchRestrictions,
  });

  const [userId, setUserId] = useState("");
  const [type, setType] = useState("ban");
  const [reason, setReason] = useState("");
  const [expires, setExpires] = useState("");

  const createMutation = useMutation({
    mutationFn: async () => {
      await api.post("/admin/restrictions", {
        user_id: userId,
        type,
        reason: reason || undefined,
        expires_at: expires ? new Date(expires).toISOString() : undefined,
      });
    },
    onSuccess: () => {
      setUserId("");
      setReason("");
      setExpires("");
      queryClient.invalidateQueries({ queryKey: ["restrictions"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (payload: {
      id: string;
      reason: string;
      expires_at: string | null;
    }) => {
      await api.patch(`/admin/restrictions/${payload.id}`, {
        reason: payload.reason || null,
        expires_at: payload.expires_at,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["restrictions"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.del(`/admin/restrictions/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["restrictions"] });
    },
  });

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editReason, setEditReason] = useState("");
  const [editExpires, setEditExpires] = useState("");

  const startEdit = (r: Restriction) => {
    setEditingId(r.id);
    setEditReason(r.reason ?? "");
    setEditExpires(
      r.expires_at ? new Date(r.expires_at).toISOString().slice(0, 16) : "",
    );
  };

  const saveEdit = () => {
    if (!editingId) return;
    updateMutation.mutate({
      id: editingId,
      reason: editReason,
      expires_at: editExpires ? new Date(editExpires).toISOString() : null,
    });
    setEditingId(null);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Restrictions</h1>
      <div className="mb-4 space-x-2">
        <input
          className="border rounded px-2 py-1"
          placeholder="User ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
        />
        <select
          className="border rounded px-2 py-1"
          value={type}
          onChange={(e) => setType(e.target.value)}
        >
          <option value="ban">ban</option>
          <option value="post_restrict">post_restrict</option>
        </select>
        <input
          className="border rounded px-2 py-1"
          placeholder="Reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
        <input
          type="datetime-local"
          className="border rounded px-2 py-1"
          value={expires}
          onChange={(e) => setExpires(e.target.value)}
        />
        <button
          className="bg-blue-500 text-white px-3 py-1 rounded"
          onClick={() => createMutation.mutate()}
        >
          Apply
        </button>
      </div>
      {isLoading && <p>Loading...</p>}
      {error && (
        <p className="text-red-500">
          {error instanceof Error ? error.message : String(error)}
        </p>
      )}
      {!isLoading && !error && (
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="border-b">
              <th className="p-2">User</th>
              <th className="p-2">Type</th>
              <th className="p-2">Expires</th>
              <th className="p-2">Reason</th>
              <th className="p-2">Moderator</th>
              <th className="p-2">Created</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((r) => (
              <tr
                key={r.id}
                className="border-b hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <td className="p-2 font-mono">{r.user_id}</td>
                <td className="p-2">{r.type}</td>
                <td className="p-2">
                  {r.expires_at ? new Date(r.expires_at).toLocaleString() : "-"}
                </td>
                <td className="p-2">
                  {editingId === r.id ? (
                    <input
                      className="border rounded px-1 py-0.5"
                      value={editReason}
                      onChange={(e) => setEditReason(e.target.value)}
                    />
                  ) : (
                    (r.reason ?? "")
                  )}
                </td>
                <td className="p-2 font-mono">{r.issued_by ?? ""}</td>
                <td className="p-2">
                  {new Date(r.created_at).toLocaleString()}
                </td>
                <td className="p-2 space-x-2">
                  {editingId === r.id ? (
                    <>
                      <input
                        type="datetime-local"
                        className="border rounded px-1 py-0.5"
                        value={editExpires}
                        onChange={(e) => setEditExpires(e.target.value)}
                      />
                      <button
                        className="bg-green-500 text-white px-2 py-1 rounded"
                        onClick={saveEdit}
                      >
                        Save
                      </button>
                      <button
                        className="bg-gray-500 text-white px-2 py-1 rounded"
                        onClick={() => setEditingId(null)}
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        className="bg-blue-500 text-white px-2 py-1 rounded"
                        onClick={() => startEdit(r)}
                      >
                        Edit
                      </button>
                      <button
                        className="bg-red-500 text-white px-2 py-1 rounded"
                        onClick={() => deleteMutation.mutate(r.id)}
                      >
                        Remove
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

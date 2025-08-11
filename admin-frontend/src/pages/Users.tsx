import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

interface Restriction {
  id: string;
  type: string;
  expires_at?: string | null;
}

interface AdminUser {
  id: string;
  email?: string | null;
  username?: string | null;
  role: string;
  is_active: boolean;
  is_premium: boolean;
  premium_until?: string | null;
  created_at: string;
  wallet_address?: string | null;
  restrictions: Restriction[];
}

async function fetchUsers(search: string): Promise<AdminUser[]> {
  const params = new URLSearchParams();
  if (search) params.set("q", search);
  const token = localStorage.getItem("token") || "";
  const resp = await fetch(`/admin/users?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const text = await resp.text();
  if (!resp.ok) {
    throw new Error(text || "Failed to load users");
  }
  try {
    return JSON.parse(text) as AdminUser[];
  } catch {
    throw new Error("Invalid JSON in response");
  }
}

async function updateRole(id: string, role: string) {
  const token = localStorage.getItem("token") || "";
  const resp = await fetch(`/admin/users/${id}/role`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ role }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || "Failed to update role");
  }
}

export default function Users() {
  const [search, setSearch] = useState("");
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["users", search],
    queryFn: () => fetchUsers(search),
  });

  const handleRoleChange = async (id: string, role: string) => {
    await updateRole(id, role);
    queryClient.invalidateQueries({ queryKey: ["users"] });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Users</h1>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by email or username"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border rounded px-3 py-1 w-64"
        />
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
              <th className="p-2">ID</th>
              <th className="p-2">Email</th>
              <th className="p-2">Username</th>
              <th className="p-2">Role</th>
              <th className="p-2">Active</th>
              <th className="p-2">Premium until</th>
              <th className="p-2">Created</th>
              <th className="p-2">Wallet</th>
              <th className="p-2">Restrictions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((u) => (
              <tr key={u.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="p-2 font-mono">{u.id}</td>
                <td className="p-2">{u.email ?? ""}</td>
                <td className="p-2">{u.username ?? ""}</td>
                <td className="p-2">
                  <select
                    value={u.role}
                    onChange={(e) => handleRoleChange(u.id, e.target.value)}
                    className="border rounded px-2 py-1"
                  >
                    <option value="user">user</option>
                    <option value="moderator">moderator</option>
                    <option value="admin">admin</option>
                  </select>
                </td>
                <td className="p-2">{u.is_active ? "yes" : "no"}</td>
                <td className="p-2">{u.premium_until ? new Date(u.premium_until).toLocaleDateString() : "-"}</td>
                <td className="p-2">{new Date(u.created_at).toLocaleDateString()}</td>
                <td className="p-2">{u.wallet_address ?? ""}</td>
                <td className="p-2">
                  {u.restrictions.length > 0
                    ? u.restrictions.map((r) => r.type).join(", ")
                    : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

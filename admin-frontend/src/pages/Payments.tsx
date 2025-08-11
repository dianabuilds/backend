import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

interface Payment {
  id: string;
  user_id: string;
  source: string;
  days: number;
  status: string;
  created_at: string;
}

async function fetchPayments(): Promise<Payment[]> {
  const token = localStorage.getItem("token") || "";
  const resp = await fetch("/admin/payments", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || "Failed to load payments");
  }
  return (await resp.json()) as Payment[];
}

async function reverifyPayment(id: string) {
  const token = localStorage.getItem("token") || "";
  const resp = await fetch(`/admin/payments/${id}/reverify`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || "Failed to reverify");
  }
}

async function showPayload(id: string) {
  const token = localStorage.getItem("token") || "";
  const resp = await fetch(`/admin/payments/${id}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || "Failed to load payload");
  }
  const data = await resp.json();
  alert(JSON.stringify(data, null, 2));
}

async function grantPremium(userId: string, days: number) {
  const token = localStorage.getItem("token") || "";
  const resp = await fetch(`/admin/users/${userId}/premium`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ days }),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || "Failed to grant premium");
  }
}

export default function Payments() {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["payments"],
    queryFn: fetchPayments,
  });

  const [userId, setUserId] = useState("");
  const [days, setDays] = useState(0);

  const handleGrant = async () => {
    await grantPremium(userId, days);
    setUserId("");
    setDays(0);
    queryClient.invalidateQueries({ queryKey: ["payments"] });
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Payments</h1>
      <div className="mb-4 flex gap-2 items-center">
        <input
          type="text"
          placeholder="User ID"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <input
          type="number"
          placeholder="Days"
          value={days}
          onChange={(e) => setDays(parseInt(e.target.value))}
          className="border rounded px-2 py-1 w-24"
        />
        <button
          onClick={handleGrant}
          className="px-3 py-1 bg-blue-600 text-white rounded"
        >
          Grant
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
              <th className="p-2">ID</th>
              <th className="p-2">User</th>
              <th className="p-2">Source</th>
              <th className="p-2">Days</th>
              <th className="p-2">Status</th>
              <th className="p-2">Created</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((p) => (
              <tr key={p.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="p-2 font-mono">{p.id}</td>
                <td className="p-2">{p.user_id}</td>
                <td className="p-2">{p.source}</td>
                <td className="p-2">{p.days}</td>
                <td className="p-2">{p.status}</td>
                <td className="p-2">{new Date(p.created_at).toLocaleString()}</td>
                <td className="p-2 space-x-2">
                  <button
                    onClick={async () => {
                      await reverifyPayment(p.id);
                      queryClient.invalidateQueries({ queryKey: ["payments"] });
                    }}
                    className="px-2 py-0.5 bg-gray-200 rounded"
                  >
                    Reverify
                  </button>
                  <button
                    onClick={() => showPayload(p.id)}
                    className="px-2 py-0.5 bg-gray-200 rounded"
                  >
                    Payload
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

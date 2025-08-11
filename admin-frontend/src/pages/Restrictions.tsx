import { useQuery } from "@tanstack/react-query";

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
  const token = localStorage.getItem("token") || "";
  const resp = await fetch("/admin/restrictions", {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || "Failed to load restrictions");
  }
  return (await resp.json()) as Restriction[];
}

export default function Restrictions() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["restrictions"],
    queryFn: fetchRestrictions,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Restrictions</h1>
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
            </tr>
          </thead>
          <tbody>
            {data?.map((r) => (
              <tr key={r.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="p-2 font-mono">{r.user_id}</td>
                <td className="p-2">{r.type}</td>
                <td className="p-2">
                  {r.expires_at ? new Date(r.expires_at).toLocaleString() : "-"}
                </td>
                <td className="p-2">{r.reason ?? ""}</td>
                <td className="p-2 font-mono">{r.issued_by ?? ""}</td>
                <td className="p-2">
                  {new Date(r.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

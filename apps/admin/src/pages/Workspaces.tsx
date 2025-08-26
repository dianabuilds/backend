import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Workspace } from "../api/types";
import type { WorkspaceMemberOut } from "../openapi";
import { useToast } from "../components/ToastProvider";
import PageLayout from "./_shared/PageLayout";

function ensureArray(data: unknown): Workspace[] {
  if (Array.isArray(data)) return data as Workspace[];
  if (
    data &&
    typeof data === "object" &&
    Array.isArray((data as any).workspaces)
  ) {
    return (data as any).workspaces as Workspace[];
  }
  return [];
}

export default function Workspaces() {
  const { addToast } = useToast();

  const { data, isLoading, error } = useQuery({
    queryKey: ["workspaces-list"],
    queryFn: async () => {
      const res = await api.get<Workspace[] | { workspaces: Workspace[] }>(
        "/admin/workspaces",
      );
      return ensureArray(res.data);
    },
  });

  const [memberCounts, setMemberCounts] = useState<Record<string, number>>({});
  useEffect(() => {
    if (!data) return;
    Promise.all(
      data.map(async (ws) => {
        const res = await api.get<WorkspaceMemberOut[]>(
          `/admin/workspaces/${ws.id}/members`,
        );
        return [ws.id, res.data.length] as [string, number];
      }),
    ).then((entries) => setMemberCounts(Object.fromEntries(entries)));
  }, [data]);

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const filtered = (data || [])
    .filter(
      (ws) =>
        ws.name.toLowerCase().includes(search.toLowerCase()) ||
        ws.slug.toLowerCase().includes(search.toLowerCase()),
    )
    .filter((ws) => !typeFilter || ws.type === typeFilter);

  useEffect(() => {
    if (error) {
      addToast({
        title: "Failed to load workspaces",
        description: String(error),
        variant: "error",
      });
    }
  }, [error, addToast]);

  return (
    <PageLayout title="Workspaces">
      <div className="flex gap-2 mb-4">
        <input
          className="border rounded px-2 py-1"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="border rounded px-2 py-1"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All types</option>
          <option value="team">team</option>
          <option value="personal">personal</option>
          <option value="global">global</option>
        </select>
      </div>
      {isLoading && <div>Loading...</div>}
      {!isLoading && !error && (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">Name</th>
              <th className="p-2 text-left">Type</th>
              <th className="p-2 text-left">Participants</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((ws) => (
              <tr key={ws.id} className="border-b hover:bg-gray-50">
                <td className="p-2">{ws.name}</td>
                <td className="p-2 capitalize">{ws.type}</td>
                <td className="p-2">{memberCounts[ws.id] ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PageLayout>
  );
}


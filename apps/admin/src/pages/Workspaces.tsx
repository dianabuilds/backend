import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { baseApi } from "../api/baseApi";
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
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["workspaces-list"],
    queryFn: async () => {
      const res = await baseApi.get<Workspace[] | { workspaces: Workspace[] }>(
        "/admin/workspaces",
      );
      return ensureArray(res);
    },
  });

  const [memberCounts, setMemberCounts] = useState<Record<string, number>>({});
  useEffect(() => {
    if (!data) return;
    Promise.all(
      data.map(async (ws) => {
        const res = await baseApi.get<WorkspaceMemberOut[]>(
          `/admin/workspaces/${ws.id}/members`,
        );
        return [ws.id, res.length] as [string, number];
      }),
    ).then((entries) => setMemberCounts(Object.fromEntries(entries)));
  }, [data]);

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["workspaces-list"] });

  const handleCreate = async () => {
    const name = prompt("Workspace name?");
    if (!name) return;
    const slug =
      prompt("Slug?", name.toLowerCase().replace(/[^a-z0-9]+/g, "-")) || "";
    const type =
      (prompt("Type (team/personal/global)?", "team") as
        | "team"
        | "personal"
        | "global"
        | null) || "team";
    try {
      await baseApi.post("/admin/workspaces", { name, slug, type });
      refresh();
      addToast({ title: "Workspace created", variant: "success" });
    } catch (e) {
      addToast({
        title: "Failed to create workspace",
        description: String(e),
        variant: "error",
      });
    }
  };

  const handleEdit = async (ws: Workspace) => {
    const name = prompt("Workspace name?", ws.name);
    if (!name) return;
    const slug = prompt("Slug?", ws.slug) || ws.slug;
    const type =
      (prompt("Type (team/personal/global)?", ws.type) as
        | "team"
        | "personal"
        | "global"
        | null) || ws.type;
    try {
      await baseApi.patch(`/admin/workspaces/${ws.id}`, { name, slug, type });
      refresh();
      addToast({ title: "Workspace updated", variant: "success" });
    } catch (e) {
      addToast({
        title: "Failed to update workspace",
        description: String(e),
        variant: "error",
      });
    }
  };

  const handleDelete = async (ws: Workspace) => {
    if (!confirm(`Delete workspace "${ws.name}"?`)) return;
    try {
      await baseApi.del(`/admin/workspaces/${ws.id}`);
      refresh();
      addToast({ title: "Workspace deleted", variant: "success" });
    } catch (e) {
      addToast({
        title: "Failed to delete workspace",
        description: String(e),
        variant: "error",
      });
    }
  };

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
        <button
          className="px-2 py-1 bg-blue-500 text-white rounded"
          onClick={handleCreate}
        >
          New workspace
        </button>
      </div>
      {isLoading && <div>Loading...</div>}
      {!isLoading && !error && (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">Name</th>
              <th className="p-2 text-left">Type</th>
              <th className="p-2 text-left">Participants</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((ws) => (
              <tr key={ws.id} className="border-b hover:bg-gray-50">
                <td className="p-2">{ws.name}</td>
                <td className="p-2 capitalize">{ws.type}</td>
                <td className="p-2">{memberCounts[ws.id] ?? "-"}</td>
                <td className="p-2">
                  <button
                    className="text-blue-600 hover:underline mr-2"
                    onClick={() => handleEdit(ws)}
                  >
                    Edit
                  </button>
                  <button
                    className="text-red-600 hover:underline"
                    onClick={() => handleDelete(ws)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PageLayout>
  );
}


import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Workspace } from "../api/types";
import type { WorkspaceMemberOut } from "../openapi";
import { useToast } from "../components/ToastProvider";
import PageLayout from "./_shared/PageLayout";
import { ensureArray } from "../shared/utils";
import { confirmDialog, promptDialog } from "../shared/ui";

export default function Workspaces() {
  const { addToast } = useToast();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["workspaces-list", search, typeFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (search) params.set("q", search);
      if (typeFilter) params.set("type", typeFilter);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await api.get<Workspace[] | { workspaces: Workspace[] }>(
        `/admin/workspaces${qs}`,
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
        return [ws.id, (res.data ?? []).length] as [string, number];
      }),
    ).then((entries) => setMemberCounts(Object.fromEntries(entries)));
  }, [data]);

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["workspaces-list"] });

  const handleCreate = async () => {
    const name = await promptDialog("Workspace name?");
    if (!name) return;
    const slug =
      (await promptDialog(
        "Slug?",
        name.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
      )) || "";
    const type =
      ((await promptDialog("Type (team/personal/global)?", "team")) as
        | "team"
        | "personal"
        | "global"
        | null) || "team";
    try {
      await api.post("/admin/workspaces", { name, slug, type });
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
    const name = await promptDialog("Workspace name?", ws.name);
    if (!name) return;
    const slug = (await promptDialog("Slug?", ws.slug)) || ws.slug;
    const type =
      ((await promptDialog("Type (team/personal/global)?", ws.type)) as
        | "team"
        | "personal"
        | "global"
        | null) || ws.type;
    try {
      await api.patch(`/admin/workspaces/${ws.id}`, { name, slug, type });
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
    if (!(await confirmDialog(`Delete workspace "${ws.name}"?`))) return;
    try {
      await api.del(`/admin/workspaces/${ws.id}`);
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


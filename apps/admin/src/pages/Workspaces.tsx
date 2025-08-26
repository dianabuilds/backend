import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

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
  const navigate = useNavigate();

  const { data, isLoading, error, refetch } = useQuery({
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

  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [type, setType] = useState<Workspace["type"]>("team");

  const submitCreate = async () => {
    if (!name.trim() || !slug.trim()) return;
    try {
      await api.post("/admin/workspaces", {
        name: name.trim(),
        slug: slug.trim(),
        type,
      });
      addToast({
        title: "Workspace created",
        description: `${name} (${slug})`,
        variant: "success",
      });
      setName("");
      setSlug("");
      setType("team");
      setCreating(false);
      await refetch();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      addToast({
        title: "Failed to create workspace",
        description: msg,
        variant: "error",
      });
    }
  };

  const remove = async (id: string) => {
    if (!confirm("Delete workspace?")) return;
    try {
      await api.del(`/admin/workspaces/${id}`);
      addToast({ title: "Workspace deleted", variant: "success" });
      await refetch();
    } catch (e) {
      addToast({
        title: "Failed to delete",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  const [editing, setEditing] = useState<Workspace | null>(null);
  const [editName, setEditName] = useState("");
  const [editSlug, setEditSlug] = useState("");
  const [editType, setEditType] = useState<Workspace["type"]>("team");

  const openEdit = (ws: Workspace) => {
    setEditing(ws);
    setEditName(ws.name);
    setEditSlug(ws.slug);
    setEditType(ws.type);
  };

  const submitEdit = async () => {
    if (!editing) return;
    try {
      await api.patch(`/admin/workspaces/${editing.id}`, {
        name: editName.trim(),
        slug: editSlug.trim(),
        type: editType,
      });
      addToast({ title: "Workspace updated", variant: "success" });
      setEditing(null);
      await refetch();
    } catch (e) {
      addToast({
        title: "Failed to update",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

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
    <PageLayout
      title="Workspaces"
      actions={
        creating ? (
          <div className="flex gap-2">
            <input
              className="border rounded px-2 py-1"
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <input
              className="border rounded px-2 py-1"
              placeholder="Slug"
              value={slug}
              onChange={(e) => setSlug(e.target.value)}
            />
            <select
              className="border rounded px-2 py-1"
              value={type}
              onChange={(e) => setType(e.target.value as Workspace["type"])}
            >
              <option value="team">team</option>
              <option value="personal">personal</option>
              <option value="global">global</option>
            </select>
            <button
              className="px-3 py-1 rounded bg-blue-600 text-white"
              onClick={submitCreate}
              type="button"
            >
              Save
            </button>
            <button
              className="px-3 py-1 rounded border"
              onClick={() => {
                setCreating(false);
                setName("");
                setSlug("");
                setType("team");
              }}
              type="button"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            className="px-3 py-1 rounded bg-blue-600 text-white"
            onClick={() => setCreating(true)}
          >
            Create workspace
          </button>
        )
      }
    >
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
              <th className="p-2 text-left">Slug</th>
              <th className="p-2 text-left">Type</th>
              <th className="p-2 text-left">Participants</th>
              <th className="p-2" />
            </tr>
          </thead>
          <tbody>
            {filtered.map((ws) => (
              <tr key={ws.id} className="border-b hover:bg-gray-50">
                <td className="p-2">
                  <Link to={`/workspaces/${ws.id}`}>{ws.name}</Link>
                </td>
                <td className="p-2 font-mono">{ws.slug}</td>
                <td className="p-2 capitalize">{ws.type}</td>
                <td className="p-2">
                  {memberCounts[ws.id] ?? "-"}
                </td>
                <td className="p-2 space-x-2 text-xs">
                  <button
                    className="text-blue-600"
                    onClick={() => openEdit(ws)}
                  >
                    Edit
                  </button>
                  <button
                    className="text-green-600"
                    onClick={() => navigate(`/workspaces/${ws.id}?tab=Members`)}
                  >
                    Members
                  </button>
                  <button
                    className="text-red-600"
                    onClick={() => remove(ws.id)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {editing && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div className="bg-white dark:bg-gray-900 rounded p-4 w-80 space-y-3">
            <h3 className="font-semibold">Edit workspace</h3>
            <input
              className="border rounded px-2 py-1 w-full"
              placeholder="Name"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
            />
            <input
              className="border rounded px-2 py-1 w-full"
              placeholder="Slug"
              value={editSlug}
              onChange={(e) => setEditSlug(e.target.value)}
            />
            <select
              className="border rounded px-2 py-1 w-full"
              value={editType}
              onChange={(e) => setEditType(e.target.value as Workspace["type"])}
            >
              <option value="team">team</option>
              <option value="personal">personal</option>
              <option value="global">global</option>
            </select>
            <div className="flex justify-end gap-2 pt-2">
              <button
                className="px-2 py-1"
                onClick={() => setEditing(null)}
              >
                Cancel
              </button>
              <button
                className="px-2 py-1 border rounded"
                onClick={submitEdit}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </PageLayout>
  );
}


import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api } from "../api/client";
import RoleBadge from "../components/RoleBadge";
import { useToast } from "../components/ToastProvider";
import type { WorkspaceOut } from "../openapi";
import PageLayout from "./_shared/PageLayout";

function ensureArray(data: unknown): WorkspaceOut[] {
  if (Array.isArray(data)) return data as WorkspaceOut[];
  if (
    data &&
    typeof data === "object" &&
    Array.isArray((data as any).workspaces)
  ) {
    return (data as any).workspaces as WorkspaceOut[];
  }
  return [];
}

export default function Workspaces() {
  const { addToast } = useToast();
  const navigate = useNavigate();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["workspaces-list"],
    queryFn: async () => {
      const res = await api.get<
        WorkspaceOut[] | { workspaces: WorkspaceOut[] }
      >("/admin/workspaces");
      return ensureArray(res.data);
    },
  });

  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");

  const submitCreate = async () => {
    if (!name.trim() || !slug.trim()) return;
    try {
      await api.post("/admin/workspaces", { name: name.trim(), slug: slug.trim() });
      addToast({
        title: "Workspace created",
        description: `${name} (${slug})`,
        variant: "success",
      });
      setName("");
      setSlug("");
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

  const archive = async (id: string) => {
    if (!confirm("Archive workspace?")) return;
    try {
      await api.del(`/admin/workspaces/${id}`);
      addToast({ title: "Workspace archived", variant: "success" });
      await refetch();
    } catch (e) {
      addToast({
        title: "Failed to archive",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  const makeDefault = async (id: string) => {
    try {
      await api.patch(`/admin/workspaces/${id}`, { is_default: true });
      addToast({ title: "Workspace set as default", variant: "success" });
      await refetch();
    } catch (e) {
      addToast({
        title: "Failed to set default",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  const copySettings = async (ws: WorkspaceOut) => {
    try {
      await navigator.clipboard.writeText(
        JSON.stringify(ws.settings, null, 2),
      );
      addToast({ title: "Settings copied", variant: "success" });
    } catch (e) {
      addToast({
        title: "Failed to copy settings",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  const openMetrics = (id: string) => {
    navigate(`/tools/workspace-metrics?workspace=${id}`);
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
      {isLoading && <div>Loading...</div>}
      {!isLoading && !error && (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">ID</th>
              <th className="p-2 text-left">Name</th>
              <th className="p-2 text-left">Role</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((ws) => (
              <tr key={ws.id} className="border-b hover:bg-gray-50">
                <td className="p-2 font-mono">
                  <Link to={`/workspaces/${ws.id}`}>{ws.id}</Link>
                </td>
                <td className="p-2">
                  <Link to={`/workspaces/${ws.id}`}>{ws.name}</Link>
                </td>
                <td className="p-2">
                  {ws.role ? <RoleBadge role={ws.role} /> : null}
                </td>
                <td className="p-2 space-x-2 text-xs">
                  <button
                    className="text-red-600"
                    onClick={() => archive(ws.id)}
                  >
                    Archive
                  </button>
                  <button
                    className="text-blue-600"
                    onClick={() => makeDefault(ws.id)}
                  >
                    Default
                  </button>
                  <button
                    className="text-gray-600"
                    onClick={() => copySettings(ws)}
                  >
                    Copy
                  </button>
                  <button
                    className="text-green-600"
                    onClick={() => openMetrics(ws.id)}
                  >
                    Metrics
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

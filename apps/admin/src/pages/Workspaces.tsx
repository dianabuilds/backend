import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link } from "react-router-dom";

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
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["workspaces-list"],
    queryFn: async () => {
      const res = await api.get<
        WorkspaceOut[] | { workspaces: WorkspaceOut[] }
      >("/admin/workspaces");
      return ensureArray(res.data);
    },
  });

  const onCreate = async () => {
    const name = prompt("Workspace name:")?.trim();
    if (!name) return;
    const slug = prompt("Workspace slug:")?.trim();
    if (!slug) return;
    try {
      await api.post("/admin/workspaces", { name, slug });
      addToast({
        title: "Workspace created",
        description: `${name} (${slug})`,
        variant: "success",
      });
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
        <button
          className="px-3 py-1 rounded bg-blue-600 text-white"
          onClick={onCreate}
        >
          Create workspace
        </button>
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
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PageLayout>
  );
}

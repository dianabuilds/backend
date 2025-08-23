import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import PageLayout from "./_shared/PageLayout";
import { api } from "../api/client";
import type { WorkspaceOut } from "../openapi";
import { useToast } from "../components/ToastProvider";
import RoleBadge from "../components/RoleBadge";

function ensureArray(data: unknown): WorkspaceOut[] {
  if (Array.isArray(data)) return data as WorkspaceOut[];
  if (data && typeof data === "object" && Array.isArray((data as any).workspaces)) {
    return (data as any).workspaces as WorkspaceOut[];
  }
  return [];
}

export default function Workspaces() {
  const { addToast } = useToast();
  const { data, isLoading, error } = useQuery({
    queryKey: ["workspaces-list"],
    queryFn: async () => {
      const res = await api.get<WorkspaceOut[] | { workspaces: WorkspaceOut[] }>("/admin/workspaces");
      return ensureArray(res.data);
    },
  });

  useEffect(() => {
    if (error) {
      addToast({ title: "Failed to load workspaces", description: String(error), variant: "error" });
    }
  }, [error, addToast]);

  return (
    <PageLayout title="Workspaces">
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
                <td className="p-2">{ws.role ? <RoleBadge role={ws.role} /> : null}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PageLayout>
  );
}

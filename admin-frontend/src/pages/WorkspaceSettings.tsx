import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import PageLayout from "./_shared/PageLayout";
import { api } from "../api/client";

interface Workspace {
  id: string;
  name: string;
}

export default function WorkspaceSettings() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ["workspace", id],
    enabled: !!id,
    queryFn: async () => {
      const res = await api.get<Workspace>(`/admin/workspaces/${id}`);
      return res.data as Workspace;
    },
  });

  return (
    <PageLayout title="Workspace settings">
      {!id && <div>Select workspace</div>}
      {id && isLoading && <div>Loading...</div>}
      {id && error && <div className="text-red-600">{String(error)}</div>}
      {id && data && (
        <div className="text-sm">
          <div><b>ID:</b> {data.id}</div>
          <div><b>Name:</b> {data.name}</div>
        </div>
      )}
    </PageLayout>
  );
}

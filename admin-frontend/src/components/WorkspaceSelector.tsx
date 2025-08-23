import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { api } from "../api/client";
import { useWorkspace } from "../workspace/WorkspaceContext";

interface Workspace {
  id: string;
  name: string;
}

export default function WorkspaceSelector() {
  const { workspaceId, setWorkspaceId } = useWorkspace();

  const { data } = useQuery({
    queryKey: ["workspaces"],
    queryFn: async () => {
      const res = await api.get<{ workspaces: Workspace[] }>("/admin/workspaces");
      return res.data?.workspaces || [];
    },
  });

  useEffect(() => {
    if (!workspaceId && data && data.length > 0) {
      setWorkspaceId(data[0].id);
    }
  }, [workspaceId, data, setWorkspaceId]);

  return (
    <select
      value={workspaceId}
      onChange={(e) => setWorkspaceId(e.target.value)}
      className="px-2 py-1 border rounded mr-4 text-sm"
    >
      <option value="">Select workspace</option>
      {data?.map((ws) => (
        <option key={ws.id} value={ws.id}>
          {ws.name}
        </option>
      ))}
    </select>
  );
}

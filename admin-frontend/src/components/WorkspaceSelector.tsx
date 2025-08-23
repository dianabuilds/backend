import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Settings } from "lucide-react";
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
    <div className="flex items-center gap-2 mr-4">
      <select
        value={workspaceId}
        onChange={(e) => setWorkspaceId(e.target.value)}
        className="px-2 py-1 border rounded text-sm"
      >
        <option value="">Select workspace</option>
        {data?.map((ws) => (
          <option key={ws.id} value={ws.id}>
            {ws.name}
          </option>
        ))}
      </select>
      {workspaceId && (
        <Link
          to={`/workspaces/${workspaceId}`}
          className="text-gray-600 hover:text-gray-900"
          title="Workspace settings"
        >
          <Settings className="w-4 h-4" />
        </Link>
      )}
    </div>
  );
}

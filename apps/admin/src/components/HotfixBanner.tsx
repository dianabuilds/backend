import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router-dom";
import { api } from "../api/client";
import { useWorkspace } from "../workspace/WorkspaceContext";

interface Workspace {
  id: string;
  type: string;
}

export default function HotfixBanner() {
  const { workspaceId } = useWorkspace();
  const location = useLocation();
  const { data } = useQuery<Workspace | null>({
    queryKey: ["workspace-info", workspaceId],
    queryFn: async () => {
      if (!workspaceId) return null;
      const res = await api.get<Workspace>(`/admin/workspaces/${workspaceId}`);
      return res.data as Workspace;
    },
    enabled: !!workspaceId,
  });

  const isEditor = location.pathname.includes("editor");
  if (data?.type === "global" && isEditor) {
    return (
      <div className="mb-4 p-2 bg-yellow-200 text-yellow-900 text-sm rounded">
        Hotfix mode
      </div>
    );
  }
  return null;
}

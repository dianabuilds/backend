import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router-dom";

import { api } from "../api/client";
import type { Workspace } from "../api/types";
import { useWorkspace } from "../workspace/WorkspaceContext";

export default function HotfixBanner() {
  const { workspaceId } = useWorkspace();
  const location = useLocation();
  const isEditor = location.pathname.includes("editor");
  const { data } = useQuery<Workspace>({
    queryKey: ["workspace-info", workspaceId],
    queryFn: async () => {
      const res = await api.get<Workspace>(`/admin/workspaces/${workspaceId}`);
      return res.data;
    },
    enabled: !!workspaceId && isEditor,
  });

  if (data?.type === "global" && isEditor) {
    return (
      <div className="mb-4 p-2 bg-yellow-200 text-yellow-900 text-sm rounded">
        Hotfix mode
      </div>
    );
  }
  return null;
}

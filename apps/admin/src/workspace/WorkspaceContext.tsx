/* eslint react-refresh/only-export-components: off */
import { createContext, type ReactNode, useContext, useState } from "react";

import { setWorkspaceId as persistWorkspaceId } from "../api/client";
import type { Workspace } from "../api/types";

interface WorkspaceContextType {
  workspaceId: string;
  setWorkspace: (workspace: Workspace | undefined) => void;
}

const WorkspaceContext = createContext<WorkspaceContextType>({
  workspaceId: "",
  setWorkspace: () => {},
});

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [workspaceId, setWorkspaceIdState] = useState<string>(() => {
    if (typeof localStorage === "undefined") return "";
    const stored = localStorage.getItem("workspaceId") || "";
    const fallback = localStorage.getItem("defaultWorkspaceId") || "";
    const initial = stored || fallback;
    persistWorkspaceId(initial || null);
    return initial;
  });

  const setWorkspace = (ws: Workspace | undefined) => {
    const id = ws?.id ?? "";
    setWorkspaceIdState(id);
    persistWorkspaceId(id || null);
  };

  return (
    <WorkspaceContext.Provider value={{ workspaceId, setWorkspace }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}

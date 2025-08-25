/* eslint react-refresh/only-export-components: off */
import { createContext, type ReactNode, useContext, useState } from "react";

import { setWorkspaceId as persistWorkspaceId } from "../api/client";
import type { Workspace } from "../api/types";

interface WorkspaceContextType {
  workspaceId: string;
  branch: string;
  setWorkspace: (workspace: Workspace | undefined) => void;
  setBranch: (branch: string) => void;
}

const WorkspaceContext = createContext<WorkspaceContextType>({
  workspaceId: "",
  branch: "",
  setWorkspace: () => {},
  setBranch: () => {},
});

export function WorkspaceBranchProvider({ children }: { children: ReactNode }) {
  const [workspaceId, setWorkspaceIdState] = useState<string>(() => {
    if (typeof localStorage === "undefined") return "";
    const stored = localStorage.getItem("workspaceId") || "";
    const fallback = localStorage.getItem("defaultWorkspaceId") || "";
    const initial = stored || fallback;
    persistWorkspaceId(initial || null);
    return initial;
  });

  const [branch, setBranchState] = useState<string>(() => {
    if (typeof localStorage === "undefined") return "";
    return localStorage.getItem("branch") || "";
  });

  const setWorkspace = (ws: Workspace | undefined) => {
    const id = ws?.id ?? "";
    setWorkspaceIdState(id);
    persistWorkspaceId(id || null);
  };

  const setBranch = (b: string) => {
    setBranchState(b);
    if (typeof localStorage !== "undefined") {
      if (b) localStorage.setItem("branch", b);
      else localStorage.removeItem("branch");
    }
  };

  return (
    <WorkspaceContext.Provider value={{ workspaceId, branch, setWorkspace, setBranch }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}

/* eslint react-refresh/only-export-components: off */
import { createContext, type ReactNode, useContext, useEffect, useState } from "react";

import { setWorkspaceId as persistWorkspaceId } from "../api/client";
import type { Workspace } from "../api/types";
import { safeLocalStorage } from "../utils/safeStorage";

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
    const stored = safeLocalStorage.getItem("workspaceId") || "";
    const fallback = safeLocalStorage.getItem("defaultWorkspaceId") || "";
    return stored || fallback;
  });

  useEffect(() => {
    persistWorkspaceId(workspaceId || null);
  }, [workspaceId]);

  const [branch, setBranchState] = useState<string>(() => {
    return safeLocalStorage.getItem("branch") || "";
  });

  const setWorkspace = (ws: Workspace | undefined) => {
    const id = ws?.id ?? "";
    setWorkspaceIdState(id);
    persistWorkspaceId(id || null);
  };

  const setBranch = (b: string) => {
    setBranchState(b);
    if (b) safeLocalStorage.setItem("branch", b);
    else safeLocalStorage.removeItem("branch");
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

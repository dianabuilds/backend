/* eslint react-refresh/only-export-components: off */
import { createContext, type ReactNode, useContext, useEffect, useState } from "react";

import type { Workspace } from "../api/types";
import { safeLocalStorage } from "../utils/safeStorage";

function persistWorkspaceId(id: string | null) {
  if (id) safeLocalStorage.setItem("workspaceId", id);
  else safeLocalStorage.removeItem("workspaceId");
}

interface WorkspaceContextType {
  workspaceId: string;
  setWorkspace: (workspace: Workspace | undefined) => void;
}

const WorkspaceContext = createContext<WorkspaceContextType>({
  workspaceId: "",
  setWorkspace: () => {},
});

function updateUrl(id: string) {
  try {
    const url = new URL(window.location.href);
    if (id) url.searchParams.set("workspace_id", id);
    else url.searchParams.delete("workspace_id");
    window.history.replaceState({}, "", url.pathname + url.search + url.hash);
  } catch {
    // ignore
  }
}

export function WorkspaceBranchProvider({ children }: { children: ReactNode }) {
  const [workspaceId, setWorkspaceIdState] = useState<string>(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const fromUrl = params.get("workspace_id") || "";
      const stored = safeLocalStorage.getItem("workspaceId") || "";
      const fallback = safeLocalStorage.getItem("defaultWorkspaceId") || "";
      return fromUrl || stored || fallback;
    } catch {
      return "";
    }
  });

  useEffect(() => {
    persistWorkspaceId(workspaceId || null);
    updateUrl(workspaceId);
  }, [workspaceId]);

  const setWorkspace = (ws: Workspace | undefined) => {
    const id = ws?.id ?? "";
    setWorkspaceIdState(id);
    persistWorkspaceId(id || null);
    updateUrl(id);
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

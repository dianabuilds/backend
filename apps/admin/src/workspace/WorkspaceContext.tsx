/* eslint react-refresh/only-export-components: off */
import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react";

import { api } from "../api/client";
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
      return fromUrl || stored;
    } catch {
      return "";
    }
  });

  const setWorkspace = useCallback((ws: Workspace | undefined) => {
    const id = ws?.id ?? "";
    setWorkspaceIdState(id);
    persistWorkspaceId(id || null);
    updateUrl(id);
  }, []);

  useEffect(() => {
    persistWorkspaceId(workspaceId || null);
    updateUrl(workspaceId);
  }, [workspaceId]);

  useEffect(() => {
    if (workspaceId) return;
    (async () => {
      try {
        const me = await api.get<{ default_workspace_id: string | null }>(
          "/users/me",
        );
        const defId = me.data?.default_workspace_id;
        if (defId) {
          setWorkspaceIdState(defId);
          persistWorkspaceId(defId);
          updateUrl(defId);
          return;
        }
      } catch {
        // ignore
      }
      try {
        const res = await api.get<Workspace[] | { workspaces: Workspace[] }>(
          "/workspaces",
        );
        const payload = Array.isArray(res.data)
          ? res.data
          : res.data?.workspaces || [];
        const globalWs = payload.find(
          (ws) => ws.type === "global" || ws.slug === "global",
        );
        if (globalWs) {
          setWorkspaceIdState(globalWs.id);
          persistWorkspaceId(globalWs.id);
          updateUrl(globalWs.id);
        }
      } catch {
        // ignore
      }
    })();
  }, [workspaceId]);

  return (
    <WorkspaceContext.Provider value={{ workspaceId, setWorkspace }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}

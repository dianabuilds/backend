/* eslint react-refresh/only-export-components: off */
import { createContext, useContext, useState, type ReactNode } from "react";
import { setWorkspaceId as persistWorkspaceId } from "../api/client";

interface WorkspaceContextType {
  workspaceId: string;
  setWorkspaceId: (id: string) => void;
}

const WorkspaceContext = createContext<WorkspaceContextType>({
  workspaceId: "",
  setWorkspaceId: () => {},
});

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [workspaceId, setWorkspaceIdState] = useState<string>(() => {
    const stored =
      (typeof localStorage !== "undefined" && localStorage.getItem("workspaceId")) || "";
    persistWorkspaceId(stored || null);
    return stored;
  });

  const setWorkspaceId = (id: string) => {
    setWorkspaceIdState(id);
    persistWorkspaceId(id || null);
  };

  return (
    <WorkspaceContext.Provider value={{ workspaceId, setWorkspaceId }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  return useContext(WorkspaceContext);
}

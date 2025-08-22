import { createContext, useContext, useState, ReactNode } from "react";
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
  const [workspaceId, setWorkspaceIdState] = useState<string>(
    () => sessionStorage.getItem("workspaceId") || "",
  );

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

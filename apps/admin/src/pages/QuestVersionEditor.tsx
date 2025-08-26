import { Navigate, useParams } from "react-router-dom";
import WorkspaceSelector from "../components/WorkspaceSelector";
import { useWorkspace } from "../workspace/WorkspaceContext";

export default function QuestVersionEditor() {
  const { id } = useParams<{ id: string }>();
  const { workspaceId } = useWorkspace();
  if (!workspaceId) {
    return (
      <div className="p-4">
        <p className="mb-4">Выберите воркспейс, чтобы создать контент</p>
        <WorkspaceSelector />
      </div>
    );
  }
  return <Navigate to={`/nodes/${id ?? ""}`} replace />;
}


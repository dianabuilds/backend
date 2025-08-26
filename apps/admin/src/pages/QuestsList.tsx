import Nodes from "./Nodes";
import WorkspaceSelector from "../components/WorkspaceSelector";
import { useWorkspace } from "../workspace/WorkspaceContext";

export default function QuestsList() {
  const { workspaceId } = useWorkspace();
  if (!workspaceId) {
    return (
      <div className="p-4">
        <p className="mb-4">Выберите воркспейс, чтобы создать контент</p>
        <WorkspaceSelector />
      </div>
    );
  }
  return <Nodes initialType="quest" />;
}

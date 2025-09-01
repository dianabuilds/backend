import { useNavigate, useParams } from "react-router-dom";

import { Button } from "../../../shared/ui";
import { useWorkspace } from "../../../workspace/WorkspaceContext";
import NodeSidebar from "../components/NodeSidebar";
import useNodeEditor from "../hooks/useNodeEditor";

export default function NodeEditorPage() {
  const { id = "new" } = useParams<{ id?: string }>();
  const { workspaceId } = useWorkspace();
  const navigate = useNavigate();
  const { node, update, save, loading, error, isSaving } = useNodeEditor(
    workspaceId || "",
    id,
  );

  if (!workspaceId) return <div>Workspace not selected</div>;
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error loading node</div>;

  const handleSave = async () => {
    const res = (await save()) as { id?: string } | undefined;
    if (id === "new" && res?.id) {
      navigate(`/nodes/${res.id}?workspace_id=${workspaceId}`);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <main className="flex-1 flex flex-col">
        <header className="sticky top-0 bg-white border-b flex justify-between items-center px-6 py-3 z-10">
          <div className="flex items-center space-x-3">
            <input
              value={node.title}
              onChange={(e) => update({ title: e.target.value })}
              className="text-lg font-bold bg-transparent focus:outline-none"
              placeholder="Untitled"
            />
          </div>
          <div className="space-x-2">
            <Button onClick={() => navigate(-1)}>Close</Button>
            <Button
              onClick={handleSave}
              disabled={isSaving}
              className="bg-green-500 text-white border-green-500"
            >
              Save
            </Button>
          </div>
        </header>

        <div className="flex flex-1 overflow-hidden">
          <div className="flex-1 p-6 overflow-y-auto" />
          <aside className="w-72 bg-gray-50 border-l p-4 space-y-4 overflow-y-auto">
            <NodeSidebar node={node} onChange={update} />
          </aside>
        </div>
      </main>
    </div>
  );
}

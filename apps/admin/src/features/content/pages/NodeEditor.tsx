import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { PageLayout, Button } from "../../../shared/ui";
import { useWorkspace } from "../../../workspace/WorkspaceContext";
import NodeSidebar from "../components/NodeSidebar";
import ContentTab from "../components/ContentTab";
import GeneralTab from "../components/GeneralTab";
import NodeEditorModal from "../components/NodeEditorModal";
import useNodeEditor from "../hooks/useNodeEditor";

export default function NodeEditorPage() {
  const { type = "article", id = "new" } = useParams<{ type?: string; id?: string }>();
  const { workspaceId } = useWorkspace();
  const navigate = useNavigate();
  const { node, update, save, loading, error, isSaving, isNew } = useNodeEditor(
    workspaceId || "",
    type,
    id,
  );
  const [tab, setTab] = useState<"content" | "general">("content");

  if (!workspaceId) return <div>Workspace not selected</div>;
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error loading node</div>;

  const handleSave = async () => {
    const res = await save();
    if (isNew && res) {
      navigate(`/nodes/${type}/${res.id}?workspace_id=${workspaceId}`);
    }
  };

  if (isNew) {
    return (
      <NodeEditorModal
        open={true}
        node={node}
        onChange={update}
        onSave={handleSave}
        onClose={() => navigate(-1)}
      />
    );
  }

  return (
    <PageLayout
      title="Node editor"
      actions={<Button onClick={handleSave} disabled={isSaving}>Save</Button>}
    >
      <div className="flex gap-4">
        <div className="flex-1">
          <div className="mb-4 flex gap-4 border-b">
            <button
              className={`px-2 py-1 ${tab === "content" ? "border-b-2" : ""}`}
              onClick={() => setTab("content")}
            >
              Content
            </button>
            <button
              className={`px-2 py-1 ${tab === "general" ? "border-b-2" : ""}`}
              onClick={() => setTab("general")}
            >
              General
            </button>
          </div>
          {tab === "content" ? (
            <ContentTab node={node} onChange={update} />
          ) : (
            <GeneralTab node={node} onChange={update} />
          )}
        </div>
        <div className="w-64">
          <NodeSidebar node={node} onChange={update} />
        </div>
      </div>
    </PageLayout>
  );
}

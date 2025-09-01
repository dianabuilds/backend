import { useNavigate, useParams } from "react-router-dom";

import EditorJSEmbed from "../../../components/EditorJSEmbed";
import FieldCover from "../../../components/fields/FieldCover";
import FieldTags from "../../../components/fields/FieldTags";
import { Button } from "../../../shared/ui";
import { useWorkspace } from "../../../workspace/WorkspaceContext";
import NodeSidebar from "../components/NodeSidebar";
import useNodeEditor from "../hooks/useNodeEditor";

export default function NodeEditorPage() {
  const { type = "article", id = "new" } = useParams<{ type?: string; id?: string }>();
  const { workspaceId } = useWorkspace();
  const navigate = useNavigate();
  const idParam = id === 'new' ? 'new' : Number(id);
  const { node, update, save, loading, error, isSaving } = useNodeEditor(
    workspaceId,
    idParam as any,
  );

  if (!workspaceId) return <div>Workspace not selected</div>;
  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error instanceof Error ? error.message : String(error)}</div>;

  const handleSave = async () => {
    const res = (await save()) as { id?: string } | undefined;
    if (id === "new" && res?.id) {
      navigate(`/nodes/${type}/${res.id}?workspace_id=${workspaceId}`);
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
            <span
              className={`px-2 py-1 text-xs rounded ${
                node.isPublic ? "bg-green-200 text-green-800" : "bg-yellow-200 text-yellow-800"
              }`}
            >
              {node.isPublic ? "Published" : "Draft"}
            </span>
          </div>
          <div className="space-x-2">
            <Button onClick={() => navigate(-1)}>Close</Button>
            <Button
              onClick={() => {
                const base = type ? `/nodes/${type}/${id}` : `/nodes/${id}`;
                const qs = workspaceId ? `?workspace_id=${workspaceId}` : '';
                navigate(`${base}/preview${qs}`);
              }}
            >
              Preview
            </Button>
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
          <div className="flex-1 p-6 space-y-6 overflow-y-auto">
            <FieldCover
              value={node.coverUrl ?? null}
              onChange={(url) => update({ coverUrl: url })}
            />
            <FieldTags value={node.tags} onChange={(tags) => update({ tags })} />
            <div className="border rounded bg-white">
              <EditorJSEmbed
                value={node.content}
                onChange={(data) => update({ content: data })}
                minHeight={400}
              />
            </div>
          </div>
          <aside className="w-72 bg-gray-50 border-l p-4 space-y-4 overflow-y-auto">
            <NodeSidebar node={node} onChange={update} />
          </aside>
        </div>
      </main>
    </div>
  );
}

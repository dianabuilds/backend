import PublishControls from "../../../components/publish/PublishControls";
import { Button, TextInput } from "../../../shared/ui";
import type { NodeEditorData } from "../model/node";

interface NodeSidebarProps {
  node: NodeEditorData;
  workspaceId: string;
  onChange: (patch: Partial<NodeEditorData>) => void;
  onPublishChange?: () => void;
}

export default function NodeSidebar({
  node,
  workspaceId,
  onChange,
  onPublishChange,
}: NodeSidebarProps) {
  return (
    <div className="space-y-6">
      {node.id ? (
        <PublishControls
          workspaceId={workspaceId}
          nodeId={node.id}
          onChanged={onPublishChange}
        />
      ) : null}
      <section>
        <h3 className="font-semibold text-gray-700">Metadata</h3>
        <details className="mt-2">
          <summary className="cursor-pointer text-sm text-gray-500">System</summary>
          <div className="mt-2 space-y-2 text-xs text-gray-600">
            {node.id ? <div>ID: {node.id}</div> : null}
            <div>
              <label className="block text-xs mb-1">Slug</label>
              <TextInput
                value={node.slug || ""}
                onChange={(e) => onChange({ slug: e.target.value })}
                className="w-full"
                placeholder="slug"
              />
            </div>
          </div>
        </details>
      </section>

      <section>
        <h3 className="font-semibold text-gray-700">Validation</h3>
        <Button className="mt-2 bg-blue-500 text-white">
          Run validation
        </Button>
      </section>

      <details>
        <summary className="cursor-pointer font-semibold text-gray-700">
          Advanced
        </summary>
        <p className="mt-2 text-xs text-gray-400">Extra options...</p>
      </details>
    </div>
  );
}

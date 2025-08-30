import { TextInput } from "../../../shared/ui";
import type { NodeEditorData } from "../model/node";

interface NodeSidebarProps {
  node: NodeEditorData;
  onChange: (patch: Partial<NodeEditorData>) => void;
}

export function NodeSidebar({ node, onChange }: NodeSidebarProps) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm mb-1">Slug</label>
        <TextInput
          value={node.slug || ""}
          onChange={(e) => onChange({ slug: e.target.value })}
          className="w-full"
          placeholder="slug"
        />
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={node.isPublic}
          onChange={(e) => onChange({ isPublic: e.target.checked })}
        />
        <span>Public</span>
      </label>
    </div>
  );
}

export default NodeSidebar;

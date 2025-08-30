import { TextInput } from "../../../shared/ui";
import type { NodeEditorData } from "../model/node";

interface GeneralTabProps {
  node: NodeEditorData;
  onChange: (patch: Partial<NodeEditorData>) => void;
}

export function GeneralTab({ node, onChange }: GeneralTabProps) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm mb-1">Title</label>
        <TextInput
          value={node.title}
          onChange={(e) => onChange({ title: e.target.value })}
          className="w-full"
          placeholder="title"
        />
      </div>
    </div>
  );
}

export default GeneralTab;

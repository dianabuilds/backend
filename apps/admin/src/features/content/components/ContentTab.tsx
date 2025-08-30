import type { NodeEditorData } from "../model/node";

interface ContentTabProps {
  node: NodeEditorData;
  onChange: (patch: Partial<NodeEditorData>) => void;
}

export function ContentTab({ node, onChange }: ContentTabProps) {
  return (
    <textarea
      className="border rounded w-full h-64 p-2"
      value={node.content}
      onChange={(e) => onChange({ content: e.target.value })}
      placeholder="Content"
    />
  );
}

export default ContentTab;

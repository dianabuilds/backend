import { Modal, Button, TextInput } from "../../../shared/ui";
import type { NodeEditorData } from "../model/node";

interface NodeEditorModalProps {
  open: boolean;
  node: NodeEditorData;
  onChange: (patch: Partial<NodeEditorData>) => void;
  onSave: () => void;
  onClose: () => void;
}

export function NodeEditorModal({ open, node, onChange, onSave, onClose }: NodeEditorModalProps) {
  return (
    <Modal isOpen={open} onClose={onClose} title="New node">
      <div className="space-y-3">
        <TextInput
          value={node.title}
          onChange={(e) => onChange({ title: e.target.value })}
          placeholder="Title"
          className="w-full"
        />
        <TextInput
          value={node.slug || ""}
          onChange={(e) => onChange({ slug: e.target.value })}
          placeholder="Slug"
          className="w-full"
        />
        <textarea
          value={node.content}
          onChange={(e) => onChange({ content: e.target.value })}
          className="border rounded w-full h-40 p-2"
        />
        <div className="flex justify-end gap-2">
          <Button onClick={onClose}>Cancel</Button>
          <Button onClick={onSave}>Save</Button>
        </div>
      </div>
    </Modal>
  );
}

export default NodeEditorModal;

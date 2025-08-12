import { memo } from "react";
import EditorJSEmbed from "./EditorJSEmbed";
import ImageDropzone from "./ImageDropzone";

export interface NodeEditorData {
  id: string;
  title: string;
  subtitle?: string;
  cover_image?: string | null;
  tags?: string[];
  allow_comments?: boolean;
  is_premium_only?: boolean;
  contentData: any;
}

interface Props {
  open: boolean;
  node: NodeEditorData | null;
  onChange: (patch: Partial<NodeEditorData>) => void;
  onClose: () => void;
  onCommit: (action: "save" | "next") => void;
}

function NodeEditorModalImpl({ open, node, onChange, onClose, onCommit }: Props) {
  if (!open || !node) return null;

  const tagsText = (node.tags || []).join(", ");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-900 rounded shadow-xl w-full max-w-6xl max-h-[92vh] flex flex-col">
        <div className="px-4 py-3 border-b flex items-center justify-between">
          <h2 className="text-lg font-semibold">Edit node</h2>
          <button className="px-2 py-1 text-sm rounded border" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="p-4 overflow-auto flex-1">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <div className="md:col-span-2">
              <input
                className="w-full text-2xl font-bold mb-2 outline-none border-b pb-2 bg-transparent"
                placeholder="Node title"
                value={node.title}
                onChange={(e) => onChange({ title: e.target.value })}
              />
              <input
                className="w-full text-base mb-2 outline-none border-b pb-2 bg-transparent"
                placeholder="Subtitle (optional)"
                value={node.subtitle || ""}
                onChange={(e) => onChange({ subtitle: e.target.value })}
              />
            </div>
            <div className="space-y-3">
              <ImageDropzone
                value={node.cover_image || null}
                onChange={(dataUrl) => onChange({ cover_image: dataUrl })}
                height={150}
              />
              <input
                className="w-full border rounded px-2 py-1"
                placeholder="Tags (comma separated)"
                value={tagsText}
                onChange={(e) => onChange({ tags: e.target.value.split(",").map(s => s.trim()).filter(Boolean) })}
              />
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={!!node.allow_comments}
                    onChange={(e) => onChange({ allow_comments: e.target.checked })}
                  />
                  <span>Allow comments</span>
                </label>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={!!node.is_premium_only}
                    onChange={(e) => onChange({ is_premium_only: e.target.checked })}
                  />
                  <span>Premium only</span>
                </label>
              </div>
            </div>
          </div>

          <EditorJSEmbed
            key={node.id}
            value={node.contentData}
            onChange={(data) => onChange({ contentData: data })}
            className="border rounded"
            minHeight={460}
          />
        </div>

        <div className="px-4 py-3 border-t flex gap-2 justify-end">
          <button className="px-3 py-1 rounded border" onClick={onClose}>
            Cancel
          </button>
          <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={() => onCommit("save")}>
            Save
          </button>
          <button className="px-3 py-1 rounded bg-emerald-600 text-white" onClick={() => onCommit("next")}>
            Save & add next
          </button>
        </div>
      </div>
    </div>
  );
}

const NodeEditorModal = memo(NodeEditorModalImpl);
export default NodeEditorModal;

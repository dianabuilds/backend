import { Button, TextInput } from "../../../shared/ui";
import type { NodeEditorData } from "../model/node";

interface NodeSidebarProps {
  node: NodeEditorData;
  onChange: (patch: Partial<NodeEditorData>) => void;
}

export default function NodeSidebar({ node, onChange }: NodeSidebarProps) {
  return (
    <div className="space-y-6">
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
        <h3 className="font-semibold text-gray-700">Publication</h3>
        <div className="mt-2 flex flex-col space-y-1 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={node.isPublic}
              onChange={(e) => onChange({ isPublic: e.target.checked })}
            />
            <span>Published</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={node.premiumOnly}
              onChange={(e) => onChange({ premiumOnly: e.target.checked })}
            />
            <span>Premium only</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={node.allowComments}
              onChange={(e) => onChange({ allowComments: e.target.checked })}
            />
            <span>Allow comments</span>
          </label>
        </div>
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

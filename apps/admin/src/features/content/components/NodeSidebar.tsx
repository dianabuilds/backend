import PublishControls from "../../../components/publish/PublishControls";
import { TextInput } from "../../../shared/ui";
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
        <h3 className="font-semibold text-gray-700">Access</h3>
        <div className="mt-2 space-y-4 text-sm">
          <div>
            <label className="block text-xs mb-1">Space</label>
            <select
              value={node.space || ""}
              onChange={(e) => onChange({ space: e.target.value })}
              className="w-full border rounded px-2 py-1"
              data-testid="space-selector"
            >
              <option value="">default</option>
              <option value="alpha">alpha</option>
              <option value="beta">beta</option>
            </select>
          </div>
          <div>
            <label className="block text-xs mb-1">Roles</label>
            <div className="space-y-1">
              {['reader', 'editor', 'admin'].map((r) => (
                <label key={r} className="flex items-center space-x-2 text-xs">
                  <input
                    type="checkbox"
                    checked={node.roles?.includes(r) || false}
                    onChange={(e) => {
                      const roles = new Set(node.roles ?? []);
                      if (e.target.checked) roles.add(r);
                      else roles.delete(r);
                      onChange({ roles: Array.from(roles) });
                    }}
                    data-testid={`role-${r}`}
                  />
                  <span>{r}</span>
                </label>
              ))}
            </div>
          </div>
          <label className="flex items-center space-x-2 text-xs">
            <input
              type="checkbox"
              checked={node.override || false}
              onChange={(e) => onChange({ override: e.target.checked })}
              data-testid="override-toggle"
            />
            <span>Override</span>
          </label>
        </div>
      </section>
    </div>
  );
}

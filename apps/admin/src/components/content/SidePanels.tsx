import { useAuth } from "../../auth/AuthContext";

interface SidePanelsProps {
  node: {
    id: string;
    slug: string;
    author_id: string;
    is_public: boolean;
    node_type: string;
  };
  onSlugChange?: (slug: string) => void;
}

export default function SidePanels({ node, onSlugChange }: SidePanelsProps) {
  const { user } = useAuth();
  const role = user?.role;
  const canModerate = role === "admin" || role === "moderator";
  const canEditSlug = role === "admin";
  return (
    <div className="w-64 border-l p-4 overflow-y-auto space-y-4">
      <details open>
        <summary className="cursor-pointer font-semibold">Metadata</summary>
        <div className="mt-2 space-y-1 text-sm">
          <div>ID: {node.id}</div>
          <div>
            Slug: {canEditSlug && onSlugChange ? (
              <input
                className="w-full border rounded px-1 py-0.5 text-xs"
                value={node.slug}
                onChange={(e) => onSlugChange(e.target.value)}
              />
            ) : (
              node.slug || "-"
            )}
          </div>
          <div>Author: {node.author_id || "-"}</div>
        </div>
      </details>
      <details open>
        <summary className="cursor-pointer font-semibold">Auto-links</summary>
        <div className="mt-2 text-sm text-gray-500">No auto-links.</div>
      </details>
      <details open>
        <summary className="cursor-pointer font-semibold">Publication</summary>
        <div className="mt-2 space-y-1 text-sm">
          <div>Status: {node.is_public ? "Published" : "Draft"}</div>
          <div>Scheduling: —</div>
        </div>
      </details>
      <details open>
        <summary className="cursor-pointer font-semibold">Validation</summary>
        <div className="mt-2 text-sm text-gray-500">No validation errors.</div>
      </details>
      {canModerate ? (
        <details>
          <summary className="cursor-pointer font-semibold">Advanced</summary>
          <div className="mt-2 space-y-1 text-sm">
            <div>Type: {node.node_type}</div>
          </div>
        </details>
      ) : null}
    </div>
  );
}


interface SidePanelsProps {
  node: {
    id: string;
    slug: string;
    author_id: string;
    is_public: boolean;
    node_type: string;
  };
}

export default function SidePanels({ node }: SidePanelsProps) {
  return (
    <div className="w-64 border-l p-4 overflow-y-auto space-y-4">
      <details open>
        <summary className="cursor-pointer font-semibold">Metadata</summary>
        <div className="mt-2 space-y-1 text-sm">
          <div>ID: {node.id}</div>
          <div>Slug: {node.slug || "-"}</div>
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
      <details>
        <summary className="cursor-pointer font-semibold">Advanced</summary>
        <div className="mt-2 space-y-1 text-sm">
          <div>Type: {node.node_type}</div>
        </div>
      </details>
    </div>
  );
}


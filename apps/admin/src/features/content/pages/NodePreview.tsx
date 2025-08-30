import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { getNode } from "../../../api/nodes";
import { useWorkspace } from "../../../workspace/WorkspaceContext";
import AdminNodePreview, { Doc } from "../components/AdminNodePreview";

export default function NodePreview() {
  const { type = "article", id = "" } = useParams<{ type?: string; id?: string }>();
  const { workspaceId } = useWorkspace();
  const [doc, setDoc] = useState<Doc | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!workspaceId || !id) return;
    (async () => {
      try {
        const n = await getNode(workspaceId, type, id);
        const blocks = Array.isArray((n.content as any)?.blocks)
          ? (n.content as any).blocks
          : [];
        setDoc({
          title: n.title || "",
          cover: n.coverUrl || undefined,
          tags: n.tags || [],
          reactions: n.reactions || {},
          blocks,
        });
      } catch {
        setError("Failed to load node");
      } finally {
        setLoading(false);
      }
    })();
  }, [workspaceId, type, id]);

  if (!workspaceId) return <div>Workspace not selected</div>;
  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;
  if (!doc) return <div>No data</div>;

  return <AdminNodePreview doc={doc} />;
}

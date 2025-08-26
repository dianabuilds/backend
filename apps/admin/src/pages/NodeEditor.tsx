import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { createNode, getNode, patchNode } from "../api/nodes";
import ContentEditor from "../components/content/ContentEditor";
import { useToast } from "../components/ToastProvider";
import type { TagOut } from "../components/tags/TagPicker";
import type { OutputData } from "../types/editorjs";
import PageLayout from "./_shared/PageLayout";
import WorkspaceSelector from "../components/WorkspaceSelector";
import { useWorkspace } from "../workspace/WorkspaceContext";

interface NodeEditorData {
  id: string;
  title: string;
  slug: string;
  cover_url: string | null;
  tags: TagOut[];
  allow_comments: boolean;
  is_premium_only: boolean;
  contentData: OutputData;
  node_type: string;
}

export default function NodeEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const { workspaceId } = useWorkspace();

  if (!workspaceId) {
    return (
      <PageLayout>
        <p className="mb-4">Выберите воркспейс, чтобы создать контент</p>
        <WorkspaceSelector />
      </PageLayout>
    );
  }

  const [node, setNode] = useState<NodeEditorData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!workspaceId) return;
    const load = async () => {
      if (!id) return;
      if (id === "new") {
        try {
          const n = await createNode("quest");
          navigate(`/nodes/${n.id}`, { replace: true });
        } catch (e) {
          setError(e instanceof Error ? e.message : String(e));
          setLoading(false);
        }
        return;
      }
      try {
        const n = await getNode(id);
        setNode({
          id: n.id,
          title: n.title ?? "",
          slug: n.slug ?? "",
          cover_url: n.coverUrl ?? null,
          tags: (n.tags || []).map((t) => ({ id: t, slug: t, name: t, count: 0 })),
          allow_comments: n.allow_feedback ?? true,
          is_premium_only: n.premium_only ?? false,
          contentData: (n.content as OutputData) || {
            time: Date.now(),
            blocks: [],
            version: "2.30.7",
          },
          node_type: (n as any).type ?? (n as any).node_type ?? "node",
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id, navigate, workspaceId]);

  const handleSave = async () => {
    if (!node) return;
    setSaving(true);
    try {
      await patchNode(node.id, {
        title: node.title,
        slug: node.slug,
        coverUrl: node.cover_url,
        tags: node.tags.map((t) => t.slug),
        content: node.contentData,
        allow_feedback: node.allow_comments,
        premium_only: node.is_premium_only,
      });
      addToast({ title: "Node saved", variant: "success" });
      if (typeof localStorage !== "undefined") {
         try {
           localStorage.removeItem(`node-content-${node.id}`);
         } catch { /* ignore */ }
      }
    } catch (e) {
      addToast({
        title: "Failed to save node",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <PageLayout>
        <p>Loading…</p>
      </PageLayout>
    );
  }
  if (error) {
    return (
      <PageLayout>
        <p className="text-red-600">{error}</p>
      </PageLayout>
    );
  }
  if (!node) return null;

  return (
    <PageLayout>
      <ContentEditor
        nodeId={node.id}
        node_type={node.node_type}
        title={node.title || "Node"}
        statuses={["draft"]}
        versions={[1]}
        onSave={handleSave}
        toolbar={
          <div className="flex gap-2">
            {node.slug && (
              <a
                href={`/nodes/${node.slug}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-2 py-1 border rounded"
              >
                Preview
              </a>
            )}
            <button
              type="button"
              className="px-2 py-1 border rounded"
              disabled={saving}
              onClick={handleSave}
            >
              Save
            </button>
          </div>
        }
        general={{
          title: node.title,
          slug: node.slug,
          tags: node.tags,
          cover: node.cover_url,
          onTitleChange: (v) => setNode({ ...node, title: v }),
          onSlugChange: (v) => setNode({ ...node, slug: v }),
          onTagsChange: (t) => setNode({ ...node, tags: t }),
          onCoverChange: (url) => setNode({ ...node, cover_url: url }),
        }}
        content={{
          initial: node.contentData,
          onSave: (d) => setNode({ ...node, contentData: d }),
          storageKey: `node-content-${node.id}`,
        }}
      />
    </PageLayout>
  );
}


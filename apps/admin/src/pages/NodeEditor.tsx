import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { createNode, getNode, patchNode } from "../api/nodes";
import ContentEditor from "../components/content/ContentEditor";
import type { TagOut } from "../components/tags/TagPicker";
import { useToast } from "../components/ToastProvider";
import WorkspaceSelector from "../components/WorkspaceSelector";
import type { OutputData } from "../types/editorjs";
import { safeLocalStorage } from "../utils/safeStorage";
import { useWorkspace } from "../workspace/WorkspaceContext";
import PageLayout from "./_shared/PageLayout";

interface NodeEditorData {
  id: string;
  title: string;
  slug: string;
  tags: TagOut[];
  allow_comments: boolean;
  is_premium_only: boolean;
  is_public: boolean;
  contentData: OutputData;
  node_type: string;
}

export default function NodeEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const { workspaceId } = useWorkspace();
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
        const raw = n as Record<string, unknown>;
        setNode({
          id: n.id,
          title: n.title ?? "",
          slug: n.slug ?? "",
          tags: Array.isArray(n.tags)
            ? n.tags.map((slug) => ({ id: slug, slug, name: slug }))
            : [],
          allow_comments: n.allow_feedback ?? true,
          is_premium_only: n.premium_only ?? false,
          is_public:
            typeof raw.is_public === "boolean"
              ? (raw.is_public as boolean)
              : Boolean(raw.isPublic),
          contentData: (n.content as OutputData) || {
            time: Date.now(),
            blocks: [],
            version: "2.30.7",
          },
          node_type:
            (raw.type as string) ?? (raw.node_type as string) ?? "node",
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id, navigate, workspaceId]);

  if (!workspaceId) {
    return (
      <PageLayout>
        <p className="mb-4">Выберите воркспейс, чтобы создать контент</p>
        <WorkspaceSelector />
      </PageLayout>
    );
  }

  const handleSave = async () => {
    if (!node) return;
    setSaving(true);
    try {
      const updated = await patchNode(node.id, {
        title: node.title,
        content: node.contentData,
        allow_feedback: node.allow_comments,
        premium_only: node.is_premium_only,
        tags: node.tags.map((t) => t.slug),
        is_public: node.is_public,
      });
      setNode({ ...node, slug: updated.slug ?? node.slug });
      const traceUrl =
        node.slug && workspaceId
          ? `/transitions/trace?start=${encodeURIComponent(node.slug)}&workspace=${workspaceId}`
          : undefined;
      addToast({
        title: "Node saved",
        variant: "success",
        description:
          traceUrl ? (
            <a
              href={traceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="underline"
            >
              Open Trace
            </a>
          ) : undefined,
      });
      try {
        safeLocalStorage.removeItem(`node-content-${node.id}`);
      } catch {
        /* ignore */
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
        statuses={[node.is_public ? "published" : "draft"]}
        versions={[1]}
        onSave={handleSave}
        toolbar={
          <div className="flex gap-2">
            {node.slug && (
              <>
                <a
                  href={`/nodes/${node.slug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-2 py-1 border rounded"
                >
                  Preview
                </a>
                {workspaceId && (
                  <a
                    href={`/transitions/trace?start=${encodeURIComponent(node.slug)}&workspace=${workspaceId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-2 py-1 border rounded"
                  >
                    Trace candidates
                  </a>
                )}
              </>
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
          tags: node.tags,
          is_public: node.is_public,
          allow_comments: node.allow_comments,
          is_premium_only: node.is_premium_only,
          onTitleChange: (v) => setNode({ ...node, title: v }),
          onTagsChange: (t) => setNode({ ...node, tags: t }),
          onIsPublicChange: (v) => setNode({ ...node, is_public: v }),
          onAllowCommentsChange: (v) =>
            setNode({ ...node, allow_comments: v }),
          onPremiumOnlyChange: (v) =>
            setNode({ ...node, is_premium_only: v }),
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


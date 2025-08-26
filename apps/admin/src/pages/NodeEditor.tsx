import { useEffect, useState, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { createNode, getNode, patchNode } from "../api/nodes";
import Breadcrumbs from "../components/Breadcrumbs";
import ContentTab from "../components/content/ContentTab";
import GeneralTab from "../components/content/GeneralTab";
import StatusBadge from "../components/StatusBadge";
import type { TagOut } from "../components/tags/TagPicker";
import { useToast } from "../components/ToastProvider";
import WorkspaceSelector from "../components/WorkspaceSelector";
import type { OutputData } from "../types/editorjs";
import { useAutosave } from "../utils/useAutosave";
import { safeLocalStorage } from "../utils/safeStorage";
import { useWorkspace } from "../workspace/WorkspaceContext";

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
  const { workspaceId } = useWorkspace();
  const [node, setNode] = useState<NodeEditorData | null>(null);
  const [loading, setLoading] = useState(true);
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
    void load();
  }, [id, navigate, workspaceId]);

  if (!workspaceId) {
    return (
      <div className="p-4">
        <p className="mb-4">Выберите воркспейс, чтобы создать контент</p>
        <WorkspaceSelector />
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-4">
        <p>Loading…</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="p-4">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }
  if (!node) return null;

  return <NodeEditorInner initialNode={node} workspaceId={workspaceId} />;
}

function NodeEditorInner({
  initialNode,
  workspaceId,
}: {
  initialNode: NodeEditorData;
  workspaceId: string;
}) {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const manualRef = useRef(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const { data: node, update: setNode, save, saving, setData } =
    useAutosave<NodeEditorData>(initialNode, async (data) => {
      try {
        const updated = await patchNode(data.id, {
          title: data.title,
          content: data.contentData,
          allow_feedback: data.allow_comments,
          premium_only: data.is_premium_only,
          tags: data.tags.map((t) => t.slug),
          is_public: data.is_public,
        });
        if (updated.slug && updated.slug !== data.slug) {
          setData((prev) => ({ ...prev, slug: updated.slug ?? prev.slug }));
        }
        setSavedAt(new Date());
        if (manualRef.current) {
          const traceUrl =
            data.slug && workspaceId
              ? `/transitions/trace?start=${encodeURIComponent(data.slug)}&workspace=${workspaceId}`
              : undefined;
          addToast({
            title: "Node saved",
            variant: "success",
            description: traceUrl ? (
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
        }
        safeLocalStorage.removeItem(`node-content-${data.id}`);
      } catch (e) {
        addToast({
          title: "Failed to save node",
          description: e instanceof Error ? e.message : String(e),
          variant: "error",
        });
      } finally {
        manualRef.current = false;
      }
    });

  const handleSave = async () => {
    manualRef.current = true;
    await save();
  };

  const handleSaveNext = async () => {
    manualRef.current = true;
    await save();
    navigate("/nodes/new");
  };

  const handleCreate = () => {
    navigate("/nodes/new");
  };

  const handleClose = () => {
    navigate("/nodes");
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b p-4">
        <Breadcrumbs />
        <div className="mt-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold">{node.title || "Node"}</h1>
            <StatusBadge status={node.is_public ? "published" : "draft"} />
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <button
              type="button"
              className="px-2 py-1 border rounded"
              onClick={handleCreate}
            >
              Create
            </button>
            <button
              type="button"
              className="px-2 py-1 border rounded"
              disabled={saving}
              onClick={handleSave}
            >
              Save
            </button>
            <button
              type="button"
              className="px-2 py-1 border rounded"
              disabled={saving}
              onClick={handleSaveNext}
            >
              Save & Next
            </button>
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
              onClick={handleClose}
            >
              Close
            </button>
            <span className="ml-2 text-gray-500">
              {saving
                ? "Saving..."
                : savedAt
                  ? `Saved ${savedAt.toLocaleTimeString()}`
                  : null}
            </span>
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-auto p-4 space-y-6">
        <GeneralTab
          title={node.title}
          tags={node.tags}
          is_public={node.is_public}
          allow_comments={node.allow_comments}
          is_premium_only={node.is_premium_only}
          onTitleChange={(v) => setNode({ ...node, title: v })}
          onTagsChange={(t) => setNode({ ...node, tags: t })}
          onIsPublicChange={(v) => setNode({ ...node, is_public: v })}
          onAllowCommentsChange={(v) =>
            setNode({ ...node, allow_comments: v })
          }
          onPremiumOnlyChange={(v) =>
            setNode({ ...node, is_premium_only: v })
          }
        />
        <ContentTab
          initial={node.contentData}
          onSave={(d) => setNode({ ...node, contentData: d })}
          storageKey={`node-content-${node.id}`}
        />
      </div>
    </div>
  );
}


import { useEffect, useState, useRef } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { createNode, getNode, patchNode } from "../api/nodes";
import { useAuth } from "../auth/AuthContext";
import ContentTab from "../components/content/ContentTab";
import GeneralTab from "../components/content/GeneralTab";
import NodeSidebar from "../components/NodeSidebar";
import StatusBadge from "../components/StatusBadge";
import type { TagOut } from "../components/tags/TagPicker";
import ErrorBanner from "../components/ErrorBanner";
import { useToast } from "../components/ToastProvider";
import WorkspaceSelector from "../components/WorkspaceSelector";
import type { OutputData } from "../types/editorjs";
import { useAutosave } from "../utils/useAutosave";
import { useUnsavedChanges } from "../utils/useUnsavedChanges";
import { useWorkspace } from "../workspace/WorkspaceContext";

interface NodeEditorData {
  id: string;
  title: string;
  slug: string;
  author_id: string;
  cover_url: string | null;
  cover_asset_id: string | null;
  cover_meta: any | null;
  cover_alt: string;
  summary: string;
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
          const path = workspaceId
            ? `/nodes/${n.id}?workspace_id=${workspaceId}`
            : `/nodes/${n.id}`;
          navigate(path, { replace: true });
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
          author_id: n.authorId,
          cover_url:
            typeof raw.cover_url === "string"
              ? (raw.cover_url as string)
              : typeof raw.coverUrl === "string"
                ? (raw.coverUrl as string)
                : null,
          cover_asset_id:
            typeof raw.cover_asset_id === "string"
              ? (raw.cover_asset_id as string)
              : typeof raw.coverAssetId === "string"
                ? (raw.coverAssetId as string)
                : null,
          cover_meta: (raw.cover_meta as any) ?? (raw.coverMeta as any) ?? null,
          cover_alt:
            typeof raw.cover_alt === "string"
              ? (raw.cover_alt as string)
              : typeof raw.coverAlt === "string"
                ? (raw.coverAlt as string)
                : "",
          summary:
            typeof raw.summary === "string" ? (raw.summary as string) : "",
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
  const { user } = useAuth();
  const canEdit = user?.role === "admin";
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [unsaved, setUnsaved] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);
  const saveCallback = canEdit
    ? async (data: NodeEditorData) => {
        try {
          const updated = await patchNode(data.id, {
            title: data.title,
            content: data.contentData,
            allow_feedback: data.allow_comments,
            premium_only: data.is_premium_only,
            tags: data.tags.map((t) => t.slug),
            is_public: data.is_public,
            cover_url: data.cover_url,
            cover_asset_id: data.cover_asset_id,
            cover_meta: data.cover_meta,
            cover_alt: data.cover_alt,
            summary: data.summary,
          });
          if (updated.slug && updated.slug !== data.slug) {
            setData((prev) => ({ ...prev, slug: updated.slug ?? prev.slug }));
          }
          setSavedAt(new Date());
          setUnsaved(false);
          if (manualRef.current) {
            addToast({
              title: "Node saved",
              variant: "success",
            });
          }
        } catch (e) {
          setSaveError(e instanceof Error ? e.message : String(e));
        } finally {
          manualRef.current = false;
        }
      }
    : undefined;
  const { data: node, update: updateNode, save, saving, setData } =
    useAutosave<NodeEditorData>(initialNode, saveCallback, 2500);
  const setNode = (next: NodeEditorData) => {
    if (canEdit) setUnsaved(true);
    updateNode(next);
  };
  useUnsavedChanges(unsaved);
  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  const handleSave = async () => {
    if (!canEdit) return;
    manualRef.current = true;
    await save();
  };

  const handleSaveNext = async () => {
    if (!canEdit) return;
    manualRef.current = true;
    await save();
    const nextId = Number(node.id);
    const nextPath = Number.isNaN(nextId)
      ? "/nodes/new"
      : `/nodes/${nextId + 1}`;
    navigate(
      workspaceId ? `${nextPath}?workspace_id=${workspaceId}` : nextPath,
    );
  };

  const handleCreate = () => {
    if (!canEdit) return;
    const path = workspaceId
      ? `/nodes/new?workspace_id=${workspaceId}`
      : "/nodes/new";
    navigate(path);
  };

  const handleClose = () => {
    navigate(workspaceId ? `/nodes?workspace_id=${workspaceId}` : "/nodes");
  };

  return (
    <div className="flex h-full flex-col">
      {saveError ? (
        <ErrorBanner
          message={saveError}
          onClose={() => setSaveError(null)}
          className="m-4"
        />
      ) : null}
      <div className="border-b p-4">
        <nav className="mb-2 text-sm text-gray-600 dark:text-gray-300">
          <ol className="flex flex-wrap items-center gap-1">
            <li>
              <Link to="/" className="hover:underline">
                Workspace
              </Link>
            </li>
            <li className="flex items-center gap-1">
              <span>/</span>
              <Link
                to={workspaceId ? `/nodes?workspace_id=${workspaceId}` : "/nodes"}
                className="hover:underline"
              >
                Nodes
              </Link>
            </li>
            <li className="flex items-center gap-1">
              <span>/</span>
              <span>{node.title || "Node"}</span>
            </li>
          </ol>
        </nav>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold">{node.title || "Node"}</h1>
            <StatusBadge status={node.is_public ? "published" : "draft"} />
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {canEdit && (
              <button
                type="button"
                className="px-2 py-1 border rounded"
                disabled={!node.title.trim()}
                onClick={handleCreate}
              >
                Create
              </button>
            )}
            {canEdit && (
              <button
                type="button"
                className="px-2 py-1 border rounded"
                disabled={saving || !unsaved}
                onClick={handleSave}
              >
                Save
              </button>
            )}
            {canEdit && (
              <button
                type="button"
                className="px-2 py-1 border rounded"
                disabled={saving || !unsaved}
                onClick={handleSaveNext}
              >
                Save & Next
              </button>
            )}
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
            {canEdit && (
              <button
                type="button"
                className="px-2 py-1 border rounded"
                onClick={() => {}}
              >
                More
              </button>
            )}
            <button
              type="button"
              className="px-2 py-1 border rounded"
              onClick={handleClose}
            >
              Close
            </button>
            {canEdit && (
              <span className="ml-2 text-gray-500">
                {saving
                  ? "Saving..."
                  : unsaved
                    ? "Unsaved changes"
                    : savedAt
                      ? `Autosaved ${savedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
                      : null}
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 overflow-auto p-4 space-y-6">
          <GeneralTab
            title={node.title}
            titleRef={titleRef}
            cover_url={node.cover_url}
            summary={node.summary}
            tags={node.tags}
            is_public={node.is_public}
            allow_comments={node.allow_comments}
            is_premium_only={node.is_premium_only}
            onTitleChange={canEdit ? (v) => setNode({ ...node, title: v }) : undefined}
            onSummaryChange={
              canEdit ? (v) => setNode({ ...node, summary: v }) : undefined
            }
            onTagsChange={canEdit ? (t) => setNode({ ...node, tags: t }) : undefined}
            onIsPublicChange={
              canEdit ? (v) => setNode({ ...node, is_public: v }) : undefined
            }
            onAllowCommentsChange={
              canEdit ? (v) => setNode({ ...node, allow_comments: v }) : undefined
            }
            onPremiumOnlyChange={
              canEdit ? (v) => setNode({ ...node, is_premium_only: v }) : undefined
            }
          />
          <ContentTab
            initial={node.contentData}
            onSave={canEdit ? (d) => setNode({ ...node, contentData: d }) : undefined}
            storageKey={`node-content-${node.id}`}
          />
        </div>
        <NodeSidebar
          node={{
            id: node.id,
            slug: node.slug,
            author_id: node.author_id,
            is_public: node.is_public,
            node_type: node.node_type,
            cover_url: node.cover_url,
            cover_asset_id: node.cover_asset_id,
            cover_alt: node.cover_alt,
            cover_meta: node.cover_meta,
          }}
          onSlugChange={(slug) => setNode({ ...node, slug })}
          onCoverChange={(c) =>
            setNode({
              ...node,
              cover_asset_id: c.assetId,
              cover_url: c.url,
              cover_alt: c.alt,
              cover_meta: c.meta,
            })
          }
        />
      </div>
    </div>
  );
}


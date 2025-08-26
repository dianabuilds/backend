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
import type { ValidateResult } from "../openapi";

interface NodeEditorData {
  id: string;
  title: string;
  slug: string;
  author_id: string;
  created_at: string;
  updated_at: string;
  cover_url: string | null;
  cover_asset_id: string | null;
  cover_meta: any | null;
  cover_alt: string;
  summary: string;
  tags: TagOut[];
  allow_comments: boolean;
  is_premium_only: boolean;
  is_public: boolean;
  hidden: boolean;
  published_at: string | null;
  contentData: OutputData;
  node_type: string;
}

interface NodeDraft {
  id: string;
  title: string;
  summary: string;
  tags: TagOut[];
  contentData: OutputData;
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
      if (!id || id === "new") return;
      try {
        const n = await getNode(id);
        const raw = n as Record<string, unknown>;
        setNode({
          id: n.id,
          title: n.title ?? "",
          slug: n.slug ?? "",
          author_id: n.authorId,
          created_at: n.createdAt,
          updated_at: n.updatedAt,
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
          hidden:
            typeof raw.hidden === "boolean"
              ? (raw.hidden as boolean)
              : typeof raw.is_visible === "boolean"
                ? !(raw.is_visible as boolean)
                : typeof raw.isVisible === "boolean"
                  ? !(raw.isVisible as boolean)
                  : false,
          published_at:
            typeof raw.published_at === "string"
              ? (raw.published_at as string)
              : typeof raw.publishedAt === "string"
                ? (raw.publishedAt as string)
                : null,
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
  }, [id, workspaceId]);

  if (!workspaceId) {
    return (
      <div className="p-4">
        <p className="mb-4">Выберите воркспейс, чтобы создать контент</p>
        <WorkspaceSelector />
      </div>
    );
  }

  if (id === "new") {
    return <NodeCreate workspaceId={workspaceId} />;
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

function NodeCreate({ workspaceId }: { workspaceId: string }) {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const titleRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const n = await createNode({ node_type: "quest", title });
      const path = workspaceId
        ? `/nodes/${n.id}?workspace_id=${workspaceId}`
        : `/nodes/${n.id}`;
      navigate(path, { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setCreating(false);
    }
  };

  const handleClose = () => {
    navigate(workspaceId ? `/nodes?workspace_id=${workspaceId}` : "/nodes");
  };

  return (
    <div className="flex h-full flex-col">
      {error ? (
        <ErrorBanner
          message={error}
          onClose={() => setError(null)}
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
              <span>New node</span>
            </li>
          </ol>
        </nav>
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold">New node</h1>
          <div className="flex items-center gap-2 text-sm">
            <button
              type="button"
              className="px-2 py-1 border rounded"
              disabled={!title.trim() || creating}
              onClick={handleCreate}
            >
              Create
            </button>
            <button
              type="button"
              className="px-2 py-1 border rounded"
              onClick={handleClose}
            >
              Close
            </button>
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-auto p-4 space-y-6">
        <GeneralTab title={title} onTitleChange={setTitle} titleRef={titleRef} />
      </div>
    </div>
  );
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
  const saveNextRef = useRef(false);
  const { user } = useAuth();
  const canEdit = user?.role === "admin";
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [unsaved, setUnsaved] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);
  const retryRef = useRef<number | null>(null);
  const saveRef = useRef<() => Promise<void>>();
  const [staleDraft, setStaleDraft] = useState<NodeDraft | null>(null);
  const [staleOpen, setStaleOpen] = useState(false);

  const [node, setNode] = useState<NodeEditorData>(initialNode);
  const [fieldErrors, setFieldErrors] = useState<{
    title: string | null;
    summary: string | null;
    cover: string | null;
  }>({ title: null, summary: null, cover: null });
  const draftInitial: NodeDraft = {
    id: initialNode.id,
    title: initialNode.title,
    summary: initialNode.summary,
    tags: initialNode.tags,
    contentData: initialNode.contentData,
  };

  const saveCallback = canEdit
    ? async (data: NodeDraft, signal?: AbortSignal) => {
        try {
          const updated = await patchNode(
            data.id,
            {
              title: data.title,
              content: data.contentData,
              tags: data.tags.map((t) => t.slug),
              summary: data.summary,
              updated_at: node.updated_at,
            },
            { signal, next: saveNextRef.current },
          );
          setNode((prev) => ({
            ...prev,
            ...data,
            slug: updated.slug ?? prev.slug,
            updated_at: updated.updatedAt ?? prev.updated_at,
          }));
          setSavedAt(new Date());
          setUnsaved(false);
          setSaveError(null);
          if (retryRef.current) {
            window.clearTimeout(retryRef.current);
            retryRef.current = null;
          }
          if (manualRef.current) {
            addToast({ title: "Node saved", variant: "success" });
          }
        } catch (e: any) {
          if (e?.response?.status === 409) {
            setStaleDraft(data);
            setStaleOpen(true);
            setSaveError("Conflict: node was updated elsewhere");
            return;
          }
          setSaveError(e instanceof Error ? e.message : String(e));
          retryRef.current = window.setTimeout(() => {
            if (saveRef.current) void saveRef.current();
          }, 10000);
          throw e;
        } finally {
          manualRef.current = false;
          saveNextRef.current = false;
        }
      }
    : undefined;

  const { data: draft, update: updateDraft, save, saving } = useAutosave<NodeDraft>(
    draftInitial,
    saveCallback,
    2500,
    `node-draft-${initialNode.id}`,
  );
  saveRef.current = save;

  const handleDraftChange = (patch: Partial<NodeDraft>) => {
    setNode((prev) => ({ ...prev, ...patch }));
    updateDraft({ ...draft, ...patch });
    setUnsaved(true);
  };

  const handleTitleChange = canEdit
    ? (v: string) => {
        handleDraftChange({ title: v });
        setFieldErrors((e) => ({
          ...e,
          title: !v.trim()
            ? "Title is required"
            : v.trim().length > 200
              ? "Max 200 characters"
              : null,
        }));
      }
    : undefined;

  const handleSummaryChange = canEdit
    ? (v: string) => {
        handleDraftChange({ summary: v });
        setFieldErrors((e) => ({
          ...e,
          summary: v.length > 300 ? "Max 300 characters" : null,
        }));
      }
    : undefined;

  const handleValidation = (res: ValidateResult) => {
    const errs = { title: null, summary: null, cover: null };
    for (const msg of res.errors) {
      const m = msg.toLowerCase();
      if (m.includes("title")) errs.title = msg;
      if (m.includes("summary")) errs.summary = msg;
      if (m.includes("cover")) errs.cover = msg;
    }
    setFieldErrors((e) => ({ ...e, ...errs }));
  };

  useEffect(() => {
    setNode((prev) => ({ ...prev, ...draft }));
  }, [draft]);

  useUnsavedChanges(unsaved);
  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  const overwrite = async () => {
    if (!staleDraft) return;
    try {
      const updated = await patchNode(staleDraft.id, {
        title: staleDraft.title,
        content: staleDraft.contentData,
        tags: staleDraft.tags.map((t) => t.slug),
        summary: staleDraft.summary,
        updated_at: node.updated_at,
      }, { force: true });
      setNode((prev) => ({
        ...prev,
        ...staleDraft,
        slug: updated.slug ?? prev.slug,
        updated_at: updated.updatedAt ?? prev.updated_at,
      }));
      setSavedAt(new Date());
      setUnsaved(false);
      setSaveError(null);
      setStaleDraft(null);
      setStaleOpen(false);
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : String(e));
    }
  };

  const openCurrent = () => {
    window.location.reload();
  };

  const openDiff = () => {
    navigate(`/nodes/${node.id}/diff`);
  };

  const handleSave = async () => {
    if (!canEdit) return;
    manualRef.current = true;
    try {
      await save();
    } catch {
      /* ignore */
    }
  };

  const handleSaveNext = async () => {
    if (!canEdit) return;
    manualRef.current = true;
    saveNextRef.current = true;
    try {
      await save();
    } catch {
      /* ignore */
    }
    const path = workspaceId
      ? `/nodes/new?workspace_id=${workspaceId}`
      : "/nodes/new";
    navigate(path);
  };

  const handleCreate = () => {
    if (!canEdit) return;
    const path = workspaceId
      ? `/nodes/new?workspace_id=${workspaceId}`
      : "/nodes/new";
    navigate(path);
  };

  const handleClose = () => {
    if (unsaved && !window.confirm("Discard unsaved changes?")) {
      return;
    }
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
            onTitleChange={handleTitleChange}
            onSummaryChange={handleSummaryChange}
            onTagsChange={
              canEdit ? (t) => handleDraftChange({ tags: t }) : undefined
            }
            onIsPublicChange={
              canEdit ? (v) => setNode({ ...node, is_public: v }) : undefined
            }
            onAllowCommentsChange={
              canEdit ? (v) => setNode({ ...node, allow_comments: v }) : undefined
            }
            onPremiumOnlyChange={
              canEdit ? (v) => setNode({ ...node, is_premium_only: v }) : undefined
            }
            titleError={fieldErrors.title}
            summaryError={fieldErrors.summary}
            coverError={fieldErrors.cover}
          />
          <ContentTab
            value={node.contentData}
            onChange={
              canEdit ? (d) => handleDraftChange({ contentData: d }) : undefined
            }
          />
        </div>
        <NodeSidebar
          node={{
            id: node.id,
            slug: node.slug,
            author_id: node.author_id,
            created_at: node.created_at,
            updated_at: node.updated_at,
            is_public: node.is_public,
            hidden: node.hidden,
            published_at: node.published_at,
            node_type: node.node_type,
            cover_url: node.cover_url,
            cover_asset_id: node.cover_asset_id,
            cover_alt: node.cover_alt,
            cover_meta: node.cover_meta,
          }}
          onSlugChange={(slug, updated) =>
            setNode({ ...node, slug, updated_at: updated ?? node.updated_at })
          }
          onCoverChange={(c) =>
            setNode({
              ...node,
              cover_asset_id: c.assetId,
              cover_url: c.url,
              cover_alt: c.alt,
              cover_meta: c.meta,
            })
          }
          onStatusChange={(is_public, updated) =>
            setNode((prev) => ({
              ...prev,
              is_public,
              updated_at: updated ?? prev.updated_at,
            }))
          }
          onScheduleChange={(published_at, updated) =>
            setNode((prev) => ({
              ...prev,
              published_at,
              updated_at: updated ?? prev.updated_at,
            }))
          }
          onHiddenChange={(hidden, updated) =>
            setNode((prev) => ({
              ...prev,
              hidden,
              updated_at: updated ?? prev.updated_at,
            }))
          }
          hasChanges={unsaved || saving}
          onValidation={handleValidation}
        />
      </div>
      {staleOpen && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50">
          <div className="bg-white p-4 rounded shadow max-w-sm space-y-3">
            <p className="text-sm">
              Эта версия устарела. Что вы хотите сделать?
            </p>
            <div className="flex flex-col gap-2">
              <button
                type="button"
                className="px-2 py-1 border rounded"
                onClick={openCurrent}
              >
                Открыть актуальную
              </button>
              <button
                type="button"
                className="px-2 py-1 border rounded"
                onClick={overwrite}
              >
                Перезаписать
              </button>
              <button
                type="button"
                className="px-2 py-1 border rounded"
                onClick={openDiff}
              >
                Сравнить diff
              </button>
              <button
                type="button"
                className="px-2 py-1 border rounded"
                onClick={() => setStaleOpen(false)}
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


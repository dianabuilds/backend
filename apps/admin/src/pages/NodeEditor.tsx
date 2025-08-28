import { useEffect, useState, useRef } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { createNode, getNode, patchNode } from "../api/nodes";
import { useAuth } from "../auth/AuthContext";
import ContentTab from "../components/content/ContentTab";
import GeneralTab from "../components/content/GeneralTab";
import NodeSidebar from "../components/NodeSidebar";
import StatusBadge from "../components/StatusBadge";
import ErrorBanner from "../components/ErrorBanner";
import { useToast } from "../components/ToastProvider";
import WorkspaceSelector from "../components/WorkspaceSelector";
import type { OutputData } from "../types/editorjs";
import { useUnsavedChanges } from "../utils/useUnsavedChanges";
import { useWorkspace } from "../workspace/WorkspaceContext";
import type { NodeOut, ValidateResult } from "../openapi";
import { usePatchQueue } from "../utils/usePatchQueue";

interface NodeEditorData extends NodeOut {
  coverAssetId: string | null;
  coverMeta: any | null;
  coverAlt: string;
  summary: string;
  publishedAt: string | null;
}

interface NodeDraft {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  content: OutputData;
}

export default function NodeEditor() {
  const { type, id } = useParams<{ type?: string; id: string }>();
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
        // Treat literal 'undefined'/'null' from malformed URLs as missing
        let nodeType =
          type && type !== "undefined" && type !== "null" && type.trim() !== ""
            ? type
            : "article";
        let n: Awaited<ReturnType<typeof getNode>>;
        // Normalize URL if we had to assume the type
        if (!type || type === "undefined" || type === "null" || type.trim() === "") {
          const qs = workspaceId ? `?workspace_id=${workspaceId}` : "";
          navigate(`/nodes/${nodeType}/${id}${qs}`, { replace: true });
        }
        n = await getNode(workspaceId, nodeType, id);

        setNode({
          ...n,
          coverAssetId: (n as any).coverAssetId ?? null,
          coverMeta: (n as any).coverMeta ?? null,
          coverAlt: (n as any).coverAlt ?? "",
          summary: (n as any).summary ?? "",
          publishedAt: (n as any).publishedAt ?? null,
          content: (n.content as OutputData) || {
            time: Date.now(),
            blocks: [],
            version: "2.30.7",
          },
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [id, workspaceId, type, navigate]);

  if (!workspaceId) {
    return (
      <div className="p-4">
        <p className="mb-4">Выберите воркспейс, чтобы создать контент</p>
        <WorkspaceSelector />
      </div>
    );
  }

  if (id === "new") {
    return <NodeCreate workspaceId={workspaceId} nodeType={type || "article"} />;
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

function NodeCreate({
  workspaceId,
  nodeType,
}: {
  workspaceId: string;
  nodeType: string;
}) {
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
      const t = nodeType === "article" || nodeType === "quest" ? nodeType : "article";
      const n = await createNode(workspaceId, { node_type: t, title });
      const path = workspaceId
        ? `/nodes/${t}/${n.id}?workspace_id=${workspaceId}`
        : `/nodes/${t}/${n.id}`;
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
    const { user } = useAuth();
    const canEdit = user?.role === "admin";
    const [savedAt, setSavedAt] = useState<Date | null>(null);
    const [saveError, setSaveError] = useState<string | null>(null);
    const titleRef = useRef<HTMLInputElement>(null);
    const titleEditRef = useRef<HTMLInputElement>(null);
    const [editingTitle, setEditingTitle] = useState(false);
    const [titleBackup, setTitleBackup] = useState("");
    const [node, setNode] = useState<NodeEditorData>(initialNode);
    const nodeRef = useRef(node);
    useEffect(() => {
      nodeRef.current = node;
    }, [node]);
    const [fieldErrors, setFieldErrors] = useState<{
      title: string | null;
      summary: string | null;
      cover: string | null;
    }>({ title: null, summary: null, cover: null });

    const { enqueue, flush, saving, pending } = usePatchQueue(
      async (patch, signal) => {
        try {
          const updated = await patchNode(
            workspaceId,
            nodeRef.current.nodeType!,
            nodeRef.current.id,
            { ...patch, updatedAt: nodeRef.current.updatedAt },
            { signal },
          );
          setNode((prev) => ({
            ...prev,
            ...patch,
            slug: updated.slug ?? prev.slug,
            updatedAt: updated.updatedAt ?? prev.updatedAt,
          }));
          setSavedAt(new Date());
          setSaveError(null);
        } catch (e: any) {
          if (e?.response?.status === 409) {
            setSaveError("Conflict: node was updated elsewhere");
          } else {
            setSaveError(e instanceof Error ? e.message : String(e));
          }
          throw e;
        }
      },
      800,
    );

    const unsaved = pending > 0 || saving;

    const handleDraftChange = (patch: Partial<NodeDraft>) => {
      setNode((prev) => ({ ...prev, ...patch }));
      enqueue(patch);
    };

    const startTitleEdit = () => {
      if (!canEdit) return;
      setTitleBackup(node.title);
      setEditingTitle(true);
      setTimeout(() => titleEditRef.current?.focus(), 0);
    };

    const stopTitleEdit = () => {
      setEditingTitle(false);
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

  useUnsavedChanges(unsaved);
  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  const handleSave = async () => {
    if (!canEdit) return;
    await flush();
    addToast({ title: "Сохранено", variant: "success" });
  };

  const handleSaveNext = async () => {
    if (!canEdit) return;
    await flush();
    const path = workspaceId
      ? `/nodes/${node.nodeType}/new?workspace_id=${workspaceId}`
      : `/nodes/${node.nodeType}/new`;
    navigate(path);
  };

  const handleCreate = () => {
    if (!canEdit) return;
    const path = workspaceId
      ? `/nodes/${node.nodeType}/new?workspace_id=${workspaceId}`
      : `/nodes/${node.nodeType}/new`;
    navigate(path);
  };

  const handleClose = () => {
    if (unsaved && !window.confirm("Discard unsaved changes?")) {
      return;
    }
    navigate(workspaceId ? `/nodes?workspace_id=${workspaceId}` : "/nodes");
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!canEdit) return;
      if (e.key === "Enter" && e.ctrlKey) {
        e.preventDefault();
        if (e.shiftKey) void handleSaveNext();
        else void handleSave();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [canEdit, handleSave, handleSaveNext]);

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
            {editingTitle ? (
              <input
                ref={titleEditRef}
                value={node.title}
                onChange={(e) => handleTitleChange?.(e.target.value)}
                onBlur={stopTitleEdit}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    stopTitleEdit();
                  } else if (e.key === "Escape") {
                    e.preventDefault();
                    handleTitleChange?.(titleBackup);
                    stopTitleEdit();
                  }
                }}
                className={`text-xl font-semibold border-b px-1 focus:outline-none ${
                  fieldErrors.title ? "border-red-500" : "border-transparent"
                }`}
              />
            ) : (
              <h1
                className={`text-xl font-semibold ${
                  fieldErrors.title ? "text-red-600" : ""
                }`}
                onDoubleClick={startTitleEdit}
              >
                {node.title || "Node"}
              </h1>
            )}
          <StatusBadge status={node.isPublic ? "published" : "draft"} />
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
                {unsaved
                  ? "несохранённые изменения"
                  : savedAt
                    ? `сохранено ${savedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
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
            coverUrl={node.coverUrl}
            summary={node.summary}
            tags={node.tags}
            isPublic={node.isPublic}
            allowFeedback={node.allowFeedback}
            premiumOnly={node.premiumOnly}
            onTitleChange={handleTitleChange}
            onSummaryChange={handleSummaryChange}
            onTagsChange={
              canEdit ? (t) => handleDraftChange({ tags: t }) : undefined
            }
            onIsPublicChange={
              canEdit ? (v) => setNode({ ...node, isPublic: v }) : undefined
            }
            onAllowFeedbackChange={
              canEdit ? (v) => setNode({ ...node, allowFeedback: v }) : undefined
            }
            onPremiumOnlyChange={
              canEdit ? (v) => setNode({ ...node, premiumOnly: v }) : undefined
            }
            titleError={fieldErrors.title}
            summaryError={fieldErrors.summary}
            coverError={fieldErrors.cover}
          />
          <ContentTab
            value={node.content as OutputData}
            onChange={
              canEdit ? (d) => handleDraftChange({ content: d }) : undefined
            }
          />
        </div>
        <NodeSidebar
          node={{
            id: node.id,
            slug: node.slug,
            authorId: node.authorId,
            createdAt: node.createdAt,
            updatedAt: node.updatedAt,
            isPublic: node.isPublic,
            isVisible: node.isVisible,
            publishedAt: node.publishedAt,
            nodeType: node.nodeType!,
            coverUrl: node.coverUrl,
            coverAssetId: node.coverAssetId,
            coverAlt: node.coverAlt,
            coverMeta: node.coverMeta,
          }}
          workspaceId={workspaceId}
          onSlugChange={(slug, updated) =>
            setNode({ ...node, slug, updatedAt: updated ?? node.updatedAt })
          }
          onCoverChange={(c) =>
            setNode({
              ...node,
              coverAssetId: c.assetId,
              coverUrl: c.url,
              coverAlt: c.alt,
              coverMeta: c.meta,
            })
          }
          onStatusChange={(isPublic, updated) =>
            setNode((prev) => ({
              ...prev,
              isPublic,
              updatedAt: updated ?? prev.updatedAt,
            }))
          }
          onScheduleChange={(publishedAt, updated) =>
            setNode((prev) => ({
              ...prev,
              publishedAt,
              updatedAt: updated ?? prev.updatedAt,
            }))
          }
          onHiddenChange={(hidden, updated) =>
            setNode((prev) => ({
              ...prev,
              isVisible: !hidden,
              updatedAt: updated ?? prev.updatedAt,
            }))
          }
          hasChanges={unsaved}
          onValidation={handleValidation}
        />
      </div>
    </div>
  );
}

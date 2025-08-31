/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { createNode, getNode, patchNode } from '../api/nodes';
import { useAuth } from '../auth/AuthContext';
import ContentTab from '../components/content/ContentTab';
import GeneralTab from '../components/content/GeneralTab';
import ErrorBanner from '../components/ErrorBanner';
import NodeSidebar from '../components/NodeSidebar';
import StatusBadge from '../components/StatusBadge';
import WorkspaceSelector from '../components/WorkspaceSelector';
import type { ValidateResult } from '../openapi';
import type { OutputData } from '../types/editorjs';
import { usePatchQueue } from '../utils/usePatchQueue';
import { useUnsavedChanges } from '../utils/useUnsavedChanges';
import { useWorkspace } from '../workspace/WorkspaceContext';

type NodeEditorData = {
  id: string;
  title: string;
  slug?: string;
  authorId?: string;
  createdAt?: string;
  updatedAt?: string;
  isPublic: boolean;
  isVisible: boolean;
  allowFeedback: boolean;
  premiumOnly: boolean;
  publishedAt: string | null;
  nodeType: string;
  coverUrl?: string | null;
  coverAssetId: string | null;
  coverMeta: any | null;
  coverAlt: string;
  content: OutputData;
  tags: string[];
};

interface NodeDraft {
  id: string;
  title: string;
  tags: string[];
  content: OutputData;
}

// Простой помощник для сравнения значений (примитивы/массивы/объекты)
function shallowEqual(a: any, b: any): boolean {
  if (a === b) return true;
  const ta = typeof a;
  const tb = typeof b;
  if (ta !== 'object' || tb !== 'object' || a === null || b === null) {
    return false;
  }
  try {
    // Быстрый путь для массивов одинаковой длины
    if (Array.isArray(a) && Array.isArray(b)) {
      if (a.length !== b.length) return false;
      for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
      }
      return true;
    }
    // Плоское сравнение ключей без глубокой рекурсии
    const ka = Object.keys(a);
    const kb = Object.keys(b);
    if (ka.length !== kb.length) return false;
    for (const k of ka) {
      if (!Object.prototype.hasOwnProperty.call(b, k)) return false;
      if (a[k] !== b[k]) return false;
    }
    return true;
  } catch {
    // Фолбэк на JSON
    try {
      return JSON.stringify(a) === JSON.stringify(b);
    } catch {
      return false;
    }
  }
}

// Нормализация полей, приходящих с бэкенда (snake_case/различные представления)
function normalizeCoverUrl(src: any): string | null {
  if (!src) return null;
  if (typeof src === 'string') return src;
  const obj = (src as any).cover ?? src;
  return (obj as any).coverUrl ?? (obj as any).cover_url ?? (obj as any).url ?? null;
}

function normalizeTags(input: any): string[] {
  if (!input) return [];
  if (Array.isArray(input)) {
    // если уже массив строк
    if (input.every((t) => typeof t === 'string')) return input as string[];
    // если массив объектов с полем slug/name
    return (input as any[])
      .map((t) => (typeof t === 'string' ? t : (t && (t.slug || t.name)) || null))
      .filter(Boolean) as string[];
  }
  // возможен вариант { tag_slugs: [...] } или { tagSlugs: [...] }
  if (Array.isArray((input as any).tag_slugs)) {
    return ((input as any).tag_slugs as any[]).map(String);
  }
  if (Array.isArray((input as any).tagSlugs)) {
    return ((input as any).tagSlugs as any[]).map(String);
  }
  return [];
}

function normalizeNodeType(src: any): string | undefined {
  if (!src) return undefined;
  return (src as any).nodeType ?? (src as any).node_type ?? undefined;
}

// Преобразуем относительный URL в абсолютный к backend origin
function resolveAssetUrl(u?: string | null): string | null {
  if (!u) return null;
  try {
    let base = '';
    const envBase = (import.meta as { env?: Record<string, string | undefined> })?.env
      ?.VITE_API_BASE as string | undefined;
    if (envBase) {
      base = envBase;
    } else if (typeof window !== 'undefined' && window.location) {
      const port = window.location.port;
      if (port && ['5173', '5174', '5175', '5176'].includes(port)) {
        base = `http://${window.location.hostname}:8000`;
      } else {
        base = `${window.location.protocol}//${window.location.host}`;
      }
    }
    const urlObj = new URL(
      u,
      base || (typeof window !== 'undefined' ? window.location.origin : undefined),
    );
    return urlObj.toString();
  } catch {
    return u;
  }
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
      if (!id || id === 'new') return;

      try {
        // Treat literal 'undefined'/'null' from malformed URLs as missing
        const nodeType =
          type && type !== 'undefined' && type !== 'null' && type.trim() !== '' ? type : 'article';
        // Normalize URL if we had to assume the type
        if (!type || type === 'undefined' || type === 'null' || type.trim() === '') {
          const qs = workspaceId ? `?workspace_id=${workspaceId}` : '';
          navigate(`/nodes/${nodeType}/${id}${qs}`, { replace: true });
        }
        const n = await getNode(workspaceId, id);

        const normalizedCover = resolveAssetUrl(normalizeCoverUrl(n));
        const normalizedTags = normalizeTags(
          (n as any).tags ?? (n as any).tag_slugs ?? (n as any).tagSlugs,
        );
        const normalizedType = normalizeNodeType(n) ?? nodeType;
        const rawContent: unknown = (n as any).content;
        let normalizedContent: OutputData;
        if (typeof rawContent === 'string') {
          try {
            normalizedContent = JSON.parse(rawContent) as OutputData;
          } catch {
            normalizedContent = {
              time: Date.now(),
              blocks: [],
              version: '2.30.7',
            };
          }
        } else if (rawContent && typeof rawContent === 'object') {
          normalizedContent = rawContent as OutputData;
        } else {
          normalizedContent = {
            time: Date.now(),
            blocks: [],
            version: '2.30.7',
          };
        }

        setNode({
          id: String((n as any).id),
          title: (n as any).title ?? '',
          slug: (n as any).slug ?? undefined,
          authorId: (n as any).authorId ?? (n as any).author_id ?? undefined,
          createdAt: (n as any).createdAt ?? (n as any).created_at ?? undefined,
          updatedAt: (n as any).updatedAt ?? (n as any).updated_at ?? undefined,
          isPublic: (n as any).isPublic ?? (n as any).is_public ?? false,
          isVisible: (n as any).isVisible ?? (n as any).is_visible ?? true,
          allowFeedback: (n as any).allowFeedback ?? (n as any).allow_feedback ?? true,
          premiumOnly: (n as any).premiumOnly ?? (n as any).premium_only ?? false,
          publishedAt: (n as any).publishedAt ?? null,
          nodeType: normalizedType || 'article',
          coverUrl: normalizedCover ?? null,
          coverAssetId: (n as any).coverAssetId ?? null,
          coverMeta: (n as any).coverMeta ?? null,
          coverAlt: (n as any).coverAlt ?? '',
          content: normalizedContent,
          tags: normalizedTags,
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

  if (id === 'new') {
    return <NodeCreate workspaceId={workspaceId} nodeType={type || 'article'} />;
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

function NodeCreate({ workspaceId, nodeType }: { workspaceId: string; nodeType: string }) {
  const navigate = useNavigate();
  const [title, setTitle] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const titleRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const t = nodeType === 'article' || nodeType === 'quest' ? nodeType : 'article';
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
    navigate(workspaceId ? `/nodes?workspace_id=${workspaceId}` : '/nodes');
  };

  return (
    <div className="flex h-full flex-col">
      {error ? (
        <ErrorBanner message={error} onClose={() => setError(null)} className="m-4" />
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
                to={workspaceId ? `/nodes?workspace_id=${workspaceId}` : '/nodes'}
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
            <button type="button" className="px-2 py-1 border rounded" onClick={handleClose}>
              Close
            </button>
          </div>
        </div>
      </div>
      <div className="flex-1 min-w-0 overflow-auto p-4 space-y-6">
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
  const { user } = useAuth();
  const canEdit = user?.role === 'admin';
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);
  const titleRef = useRef<HTMLInputElement>(null);
  const titleEditRef = useRef<HTMLInputElement>(null);
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleBackup, setTitleBackup] = useState('');
  const [node, setNode] = useState<NodeEditorData>(initialNode);
  const nodeRef = useRef(node);
  useEffect(() => {
    nodeRef.current = node;
  }, [node]);
  const titleDebounceRef = useRef<number | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{
    title: string | null;
    cover: string | null;
  }>({ title: null, cover: null });

  const { enqueue, saving, pending } = usePatchQueue(async (patch, signal) => {
    try {
      const updated = await patchNode(
        workspaceId,
        nodeRef.current.id,
        { ...patch, updatedAt: nodeRef.current.updatedAt },
        { signal },
      );

      const updatedCover = resolveAssetUrl(
        (updated as any).coverUrl ??
          (updated as any).cover_url ??
          (nodeRef.current as any).coverUrl ??
          null,
      );
      const updatedTags = normalizeTags(
        (updated as any).tags ?? (updated as any).tag_slugs ?? nodeRef.current.tags,
      );

      setNode((prev) => ({
        ...prev,
        ...patch,
        slug: (updated as any).slug ?? prev.slug,
        updatedAt: (updated as any).updatedAt ?? prev.updatedAt,
        coverUrl: updatedCover,
        tags: updatedTags,
      }));
      setSavedAt(new Date());
      setSaveError(null);
    } catch (e: any) {
      if (e?.response?.status === 409) {
        setSaveError('Conflict: node was updated elsewhere');
      } else {
        setSaveError(e instanceof Error ? e.message : String(e));
      }
      throw e;
    }
  }, 800);

  const unsaved = pending > 0 || saving;

  const handleDraftChange = (patch: Partial<NodeDraft> & Record<string, any>) => {
    // Приводим патч к формату, который гарантированно примет API (snake_case/camelCase)
    const enriched: Record<string, any> = { ...patch };

    // Подготовим локальные изменения (то, что попадёт в state)
    const localNext: Partial<NodeEditorData> = {};

    // Title
    if ('title' in patch) {
      localNext.title = String(patch.title ?? '');
    }

    // Теги: важно отправлять даже пустой массив для снятия всех тегов
    if ('tags' in patch) {
      const tags = normalizeTags(patch.tags);
      enriched.tags = tags; // camelCase
      enriched.tag_slugs = tags; // snake_case
      enriched.tagSlugs = tags; // альтернативный camelCase
      localNext.tags = tags;
    }

    // Контент
    if ('content' in patch) {
      localNext.content = patch.content as OutputData;
    }

    // Флаги: дублируем в camel и snake, чтобы сервер принял независимо от схемы
    if ('isPublic' in patch) {
      const v = !!patch.isPublic;
      enriched.isPublic = v;
      enriched.is_public = v;
      localNext.isPublic = v;
    }
    if ('isVisible' in patch) {
      const v = !!patch.isVisible;
      enriched.isVisible = v;
      enriched.is_visible = v;
      localNext.isVisible = v;
    }
    if ('allowFeedback' in patch) {
      const v = !!patch.allowFeedback;
      enriched.allowFeedback = v;
      enriched.allow_feedback = v;
      enriched.allow_comments = v; // часть старых схем
      localNext.allowFeedback = v;
    }
    if ('premiumOnly' in patch) {
      const v = !!patch.premiumOnly;
      enriched.premiumOnly = v;
      enriched.premium_only = v;
      localNext.premiumOnly = v;
    }

    // Обложка: в API отправляем исходный URL, в UI показываем резолвленный
    if ('coverUrl' in patch) {
      const raw = patch.coverUrl ?? null;
      enriched.coverUrl = raw; // camelCase
      enriched.cover_url = raw; // snake_case
      localNext.coverUrl = resolveAssetUrl(raw);
    }

    // Слаг (если меняют из сайдбара)
    if ('slug' in patch) {
      localNext.slug = String(patch.slug ?? '');
    }

    // Если локально нечего менять — проверим, действительно ли есть отличия от текущего состояния
    const prev = nodeRef.current;
    let changed = false;
    for (const [k, v] of Object.entries(localNext)) {
      // @ts-expect-error индексный доступ по ключу
      const current = (prev as any)[k];
      if (!shallowEqual(current, v)) {
        changed = true;
        break;
      }
    }

    if (changed) {
      setNode((prevState) => ({ ...prevState, ...localNext }));
    }

    // Отправляем PATCH только если есть что менять (enriched хотя бы с одним ключом)
    if (Object.keys(enriched).length > 0) {
      enqueue(enriched);
    }
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
        // Обновляем локально немедленно, чтобы не терять каретку/фокус
        setNode((prev) => ({ ...prev, title: v }));
        // Валидация
        setFieldErrors((e) => ({
          ...e,
          title: !v.trim()
            ? 'Title is required'
            : v.trim().length > 200
              ? 'Max 200 characters'
              : null,
        }));
        // Дебаунсим отправку PATCH, чтобы не дёргать сеть на каждый ввод
        if (titleDebounceRef.current) {
          window.clearTimeout(titleDebounceRef.current);
        }
        titleDebounceRef.current = window.setTimeout(() => {
          enqueue({ title: v });
        }, 1000);
      }
    : undefined;

  const handleValidation = (res: ValidateResult) => {
    const errs: { title: string | null; cover: string | null } = { title: null, cover: null };
    for (const msg of res.errors) {
      const m = msg.toLowerCase();
      if (m.includes('title')) errs.title = msg;
      if (m.includes('cover')) errs.cover = msg;
    }
    setFieldErrors((e) => ({ ...e, ...errs }));
  };

  useUnsavedChanges(unsaved);
  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  useEffect(() => {
    return () => {
      if (titleDebounceRef.current) {
        window.clearTimeout(titleDebounceRef.current);
      }
    };
  }, []);

  const handleCreate = () => {
    if (!canEdit) return;
    const path = workspaceId
      ? `/nodes/${node.nodeType}/new?workspace_id=${workspaceId}`
      : `/nodes/${node.nodeType}/new`;
    navigate(path);
  };

  const handleClose = () => {
    if (unsaved && !window.confirm('Discard unsaved changes?')) {
      return;
    }
    navigate(workspaceId ? `/nodes?workspace_id=${workspaceId}` : '/nodes');
  };

  // изменения контента из EditorJS → в очередь PATCH

  return (
    <div className="flex h-full flex-col">
      {saveError ? (
        <ErrorBanner message={saveError} onClose={() => setSaveError(null)} className="m-4" />
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
                to={workspaceId ? `/nodes?workspace_id=${workspaceId}` : '/nodes'}
                className="hover:underline"
              >
                Nodes
              </Link>
            </li>
            <li className="flex items-center gap-1">
              <span>/</span>
              <span>{node.title || 'Node'}</span>
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
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    stopTitleEdit();
                  } else if (e.key === 'Escape') {
                    e.preventDefault();
                    handleTitleChange?.(titleBackup);
                    stopTitleEdit();
                  }
                }}
                className={`text-xl font-semibold border-b px-1 focus:outline-none ${
                  fieldErrors.title ? 'border-red-500' : 'border-transparent'
                }`}
              />
            ) : (
              <h1
                className={`text-xl font-semibold ${fieldErrors.title ? 'text-red-600' : ''}`}
                onDoubleClick={startTitleEdit}
              >
                {node.title || 'Node'}
              </h1>
            )}
            <StatusBadge status={node.isPublic ? 'published' : 'draft'} />
          </div>
          <div className="flex items-center justify-between w-full">
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
              <button type="button" className="px-2 py-1 border rounded" onClick={handleClose}>
                Close
              </button>
            </div>
            {canEdit && (
              <div className="text-sm text-gray-500">
                {unsaved
                  ? 'несохранённые изменения'
                  : savedAt
                    ? `сохранено ${savedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
                    : null}
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 min-w-0 overflow-auto p-4 space-y-6">
          <GeneralTab
            title={node.title}
            titleRef={titleRef}
            coverUrl={node.coverUrl}
            tags={node.tags}
            onTitleChange={handleTitleChange}
            onTagsChange={canEdit ? (t) => handleDraftChange({ tags: t }) : undefined}
            onCoverChange={canEdit ? (url) => handleDraftChange({ coverUrl: url }) : undefined}
            titleError={fieldErrors.title}
            coverError={fieldErrors.cover}
          />
          <ContentTab
            value={node.content}
            onChange={canEdit ? (d) => handleDraftChange({ content: d }) : undefined}
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
            nodeType: node.nodeType,
            coverUrl: node.coverUrl,
            coverAssetId: node.coverAssetId,
            coverAlt: node.coverAlt,
            coverMeta: node.coverMeta,
            allowFeedback: node.allowFeedback,
            premiumOnly: node.premiumOnly,
          }}
          workspaceId={workspaceId}
          onSlugChange={(slug, updated) => {
            if (nodeRef.current.slug === slug) return;
            handleDraftChange({ slug });
            setNode((prev) => ({ ...prev, slug, updatedAt: updated ?? prev.updatedAt }));
          }}
          onCoverChange={(c) => {
            // Локально рассчитываем конечный URL для отображения
            const resolved = resolveAssetUrl(c.url);
            // Защита от зацикливания: если ничего реально не изменилось — выходим
            const prev = nodeRef.current;
            if (
              prev.coverUrl === resolved &&
              prev.coverAssetId === c.assetId &&
              prev.coverAlt === c.alt &&
              JSON.stringify(prev.coverMeta ?? null) === JSON.stringify(c.meta ?? null)
            ) {
              return;
            }
            // Обновляем локально функциональным апдейтом
            setNode((p) => ({
              ...p,
              coverAssetId: c.assetId,
              coverUrl: resolved,
              coverAlt: c.alt,
              coverMeta: c.meta,
            }));
            // Отправляем PATCH с оригинальным URL (без резолва), дублируется в cover_url внутри handleDraftChange
            handleDraftChange({ coverUrl: c.url });
          }}
          onStatusChange={(isPublic, updated) => {
            handleDraftChange({ isPublic });
            setNode((prev) => ({
              ...prev,
              isPublic,
              updatedAt: updated ?? prev.updatedAt,
            }));
          }}
          onScheduleChange={(publishedAt, updated) =>
            setNode((prev) => ({
              ...prev,
              publishedAt,
              updatedAt: updated ?? prev.updatedAt,
            }))
          }
          onHiddenChange={(hidden, updated) => {
            const isVisible = !hidden;
            handleDraftChange({ isVisible });
            setNode((prev) => ({
              ...prev,
              isVisible,
              updatedAt: updated ?? prev.updatedAt,
            }));
          }}
          onAllowFeedbackChange={(allow, updated) => {
            handleDraftChange({ allowFeedback: allow });
            setNode((prev) => ({
              ...prev,
              allowFeedback: allow,
              updatedAt: updated ?? prev.updatedAt,
            }));
          }}
          onPremiumOnlyChange={(premium, updated) => {
            handleDraftChange({ premiumOnly: premium });
            setNode((prev) => ({
              ...prev,
              premiumOnly: premium,
              updatedAt: updated ?? prev.updatedAt,
            }));
          }}
          hasChanges={unsaved}
          onValidation={handleValidation}
        />
      </div>
    </div>
  );
}

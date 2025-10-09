import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ContentLayout } from '../ContentLayout';
import { Card, Input as TInput, Switch, Button, TagInput, RichTextEditor, ImageUpload, Spinner } from '@ui';
import { apiGet, apiPatch, apiPost, apiUploadMedia } from '@shared/api/client';

type Mode = 'create' | 'edit' | 'view';

type NodeViewPayload = {
  id: number | string;
  slug?: string | null;
  author_id?: string | null;
  title?: string | null;
  tags?: string[] | null;
  content?: string | null;
  content_html?: string | null;
  cover_url?: string | null;
  is_public?: boolean | null;
  comments_disabled?: boolean | null;
  status?: string | null;
  publish_at?: string | null;
  unpublish_at?: string | null;
};

type RelatedNode = {
  id: string | number;
  title?: string | null;
  slug?: string | null;
  cover_url?: string | null;
};

type SaveResponse = {
  id: string | number;
  slug?: string | null;
};

const RELATED_LIMIT = 6;

const toLocalDateTimeInput = (value: string | null | undefined): string => {
  if (!value) return '';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
};

const toIsoOrNull = (value: string): string | null => {
  if (!value) return null;
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return null;
  return dt.toISOString();
};


const resolveMediaUrl = (value: string): string => {
  const trimmed = value.trim();
  if (!trimmed) return '';
  if (/^(blob:|data:|https?:\/\/)/i.test(trimmed)) {
    return trimmed;
  }
  const base = (import.meta as any)?.env?.VITE_API_BASE as string | undefined;
  if (!base) return trimmed;
  const normalizedBase = base.endsWith('/') ? base.slice(0, -1) : base;
  const normalizedPath = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
  return `${normalizedBase}${normalizedPath}`;
};
const normaliseTags = (value: unknown): string[] => {
  if (!Array.isArray(value)) return [];
  return value
    .map((tag) => (typeof tag === 'string' ? tag : String(tag ?? '')).trim())
    .filter(Boolean);
};

export default function NodeCreatePage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const nodeId = params.get('id');
  const modeParam = params.get('mode');
  const mode: Mode = nodeId ? (modeParam === 'view' ? 'view' : 'edit') : 'create';
  const readOnly = mode === 'view';

  const [title, setTitle] = React.useState('');
  const [tags, setTags] = React.useState<string[]>([]);
  const [content, setContent] = React.useState('');
  const [coverUrl, setCoverUrl] = React.useState('');
  const [coverFile, setCoverFile] = React.useState<File | null>(null);
  const [coverPreview, setCoverPreview] = React.useState('');
  const [isPublic, setIsPublic] = React.useState(false);
  const [commentsEnabled, setCommentsEnabled] = React.useState(true);
  const [busy, setBusy] = React.useState(false);
  const [loadingExisting, setLoadingExisting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [nodeSlug, setNodeSlug] = React.useState<string | null>(null);
  const [authorId, setAuthorId] = React.useState<string | null>(null);
  const [copied, setCopied] = React.useState(false);
  const [status, setStatus] = React.useState<string>('draft');
  const [publishAt, setPublishAt] = React.useState('');
  const [unpublishAt, setUnpublishAt] = React.useState('');
  const [related, setRelated] = React.useState<RelatedNode[]>([]);
  const [algo, setAlgo] = React.useState<'tags' | 'fts' | 'mix'>('mix');

  const submittingRef = React.useRef(false);

  const headerTitle = mode === 'view' ? 'View node' : mode === 'edit' ? 'Edit node' : 'New node';
  const submitLabel = mode === 'edit' ? 'Save changes' : 'Create node';

  const disableInputs = readOnly || busy || loadingExisting;

  React.useEffect(() => {
    if (!coverFile) {
      setCoverPreview('');
      return undefined;
    }
    const objectUrl = URL.createObjectURL(coverFile);
    setCoverPreview(objectUrl);
    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [coverFile]);

  React.useEffect(() => {
    if (!nodeId) {
      setNodeSlug(null);
      setAuthorId(null);
      setCommentsEnabled(true);
      return;
    }

    let cancelled = false;
    setLoadingExisting(true);
    setError(null);

    (async () => {
      try {
        const data = await apiGet<NodeViewPayload>(`/v1/nodes/${encodeURIComponent(nodeId)}`);
        if (cancelled) return;

        setTitle(typeof data?.title === 'string' ? data.title : '');
        setTags(normaliseTags(data?.tags));
        const html = typeof data?.content_html === 'string'
          ? data.content_html
          : typeof data?.content === 'string'
            ? data.content
            : '';
        setContent(html);
        setCoverUrl(typeof data?.cover_url === 'string' ? data.cover_url : '');
        setCoverFile(null);
        setIsPublic(Boolean(data?.is_public));
        setCommentsEnabled(!(data?.comments_disabled ?? false));
        setStatus(String(data?.status ?? (data?.is_public ? 'published' : 'draft')));
        setPublishAt(toLocalDateTimeInput(data?.publish_at ?? null));
        setUnpublishAt(toLocalDateTimeInput(data?.unpublish_at ?? null));
        setNodeSlug(data?.slug ? String(data.slug) : data?.id != null ? `node-${data.id}` : null);
        setAuthorId(data?.author_id ? String(data.author_id) : null);
      } catch (err: any) {
        if (!cancelled) {
          setError(`Failed to load node: ${err?.message || err}`);
        }
      } finally {
        if (!cancelled) {
          setLoadingExisting(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [nodeId]);

  React.useEffect(() => {
    if (!nodeId) {
      setRelated([]);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const rel = await apiGet(
          `/v1/navigation/related/${encodeURIComponent(nodeId)}?limit=${RELATED_LIMIT}&algo=${encodeURIComponent(algo)}`,
        );
        if (!cancelled) {
          const relItems = Array.isArray(rel)
            ? (rel as RelatedNode[])
            : Array.isArray((rel as any)?.items)
              ? ((rel as any).items as RelatedNode[])
              : [];
          setRelated(relItems);
        }
      } catch {
        if (!cancelled) setRelated([]);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [nodeId, algo]);

  const previewSrc = coverPreview || resolveMediaUrl(coverUrl);

  const saveNode = React.useCallback(async () => {
    if (readOnly || submittingRef.current) return;
    submittingRef.current = true;
    setBusy(true);
    setError(null);

    try {
      const body: Record<string, unknown> = {
        title: title.trim() || undefined,
        tags: tags.map((tag) => tag.trim()).filter(Boolean),
        is_public: isPublic,
        comments_disabled: !commentsEnabled,
      };

      const now = new Date();
      const scheduledPublish = publishAt ? new Date(publishAt) : null;
      const scheduledUnpublish = unpublishAt ? new Date(unpublishAt) : null;
      let computedStatus: string = isPublic ? 'published' : 'draft';
      if (scheduledPublish && scheduledPublish.getTime() > now.getTime()) {
        computedStatus = 'scheduled';
      }
      if (scheduledUnpublish && isPublic && scheduledUnpublish.getTime() > now.getTime()) {
        computedStatus = 'scheduled_unpublish';
      }
      body.status = computedStatus;
      setStatus(computedStatus);

      const publishIso = toIsoOrNull(publishAt);
      const unpublishIso = toIsoOrNull(unpublishAt);
      if (publishIso) body.publish_at = publishIso;
      else if (mode === 'edit') body.publish_at = null;
      if (unpublishIso) body.unpublish_at = unpublishIso;
      else if (mode === 'edit') body.unpublish_at = null;

      if (coverFile && !coverUrl.trim()) {
        try {
          const uploaded = await apiUploadMedia(coverFile);
          const uploadedUrl = (uploaded?.url || uploaded?.file?.url) as string | undefined;
          if (uploadedUrl) body.cover_url = uploadedUrl;
        } catch (uploadErr) {
          console.warn('Cover upload failed', uploadErr);
        }
      } else if (coverUrl.trim()) {
        body.cover_url = coverUrl.trim();
      } else if (mode === 'edit') {
        body.cover_url = null;
      }

      body.content = content;

      let response: SaveResponse;
      if (mode === 'edit' && nodeId) {
        response = (await apiPatch(`/v1/nodes/${encodeURIComponent(nodeId)}`, body)) as SaveResponse;
      } else {
        response = (await apiPost('/v1/nodes', body)) as SaveResponse;
      }

      if (response?.id) {
        navigate('/nodes/library');
      }
    } catch (err: any) {
      setError(String(err?.message || err));
    } finally {
      setBusy(false);
      submittingRef.current = false;
    }
  }, [commentsEnabled, content, coverFile, coverUrl, isPublic, mode, navigate, nodeId, publishAt, readOnly, tags, title, unpublishAt]);

  return (
    <ContentLayout context="nodes">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-gray-800 dark:text-dark-100">{headerTitle}</h2>
        <div className="flex flex-wrap items-center gap-2">
          {mode === 'view' && nodeId ? (
            <>
              <Button variant="outlined" onClick={() => navigate(`/nodes/new?id=${encodeURIComponent(nodeId)}`)}>
                Edit
              </Button>
              <Button
                variant="outlined"
                onClick={async () => {
                  try {
                    const res = await apiPost<{ node_id?: string | number }>('/v1/navigation/next', { current_node_id: Number(nodeId), strategy: 'random' });
                    const nextId = res?.node_id;
                    if (nextId) navigate(`/nodes/new?id=${encodeURIComponent(String(nextId))}&mode=view`);
                  } catch {}
                }}
              >
                Next
              </Button>
            </>
          ) : null}
          {nodeId ? (
            <Button variant="outlined" onClick={() => navigate(`/admin/nodes/${encodeURIComponent(String(nodeId))}/moderation`)}>
              Moderation
            </Button>
          ) : null}
          <Button variant="outlined" color="neutral" onClick={() => navigate('/nodes/library')}>
            Back to list
          </Button>
        </div>
      </div>

      {(loadingExisting || busy) && (
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-primary-200/60 bg-primary-50/60 px-3 py-2 text-sm text-primary-700 dark:border-dark-500 dark:bg-dark-700/40 dark:text-dark-100">
          <Spinner size="sm" />
          <span>{loadingExisting ? 'Loading node…' : 'Saving…'}</span>
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-dark-500 dark:bg-dark-700/40 dark:text-rose-200">{error}</div>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2.1fr)_minmax(0,1fr)]">
        <Card skin="shadow" padding="lg" className="space-y-6 bg-white/95 shadow-soft dark:bg-dark-800/90">
          <TInput
            label="Title"
            placeholder="Enter title"
            value={title}
            onChange={(e: any) => setTitle(e.target.value)}
            disabled={disableInputs}
          />
          <TagInput
            label="Tags"
            value={tags}
            onChange={setTags}
            placeholder="story, ai"
            disabled={disableInputs}
          />
          <div>
            <RichTextEditor
              label="Node content"
              value={content}
              onChange={setContent}
              placeholder="Type content"
              readOnly={disableInputs}
              className="mt-1"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-dark-300">Supports rich text formatting, lists, inline code and images.</p>
          </div>
        </Card>

        <div className="space-y-6">
          <Card skin="shadow" padding="lg" className="space-y-4 bg-white/95 shadow-soft dark:bg-dark-800/90">
            <div className="flex items-center justify-between">
              <h3 className="text-sm-plus font-semibold text-gray-800 dark:text-dark-100">Publishing</h3>
              {nodeId ? <span className="text-xs font-medium uppercase text-gray-400">ID {nodeId}</span> : null}
            </div>
            {nodeId && (
              <div className="rounded-xl border border-gray-200 bg-gray-50 p-3 text-xs text-gray-600 dark:border-dark-500 dark:bg-dark-700 dark:text-dark-200">
                <div className="flex flex-col gap-1">
                  <div><span className="font-semibold text-gray-700 dark:text-dark-100">Slug:</span> {nodeSlug || '-'}</div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-gray-700 dark:text-dark-100">Author:</span> {authorId || '—'}
                    {nodeSlug && (
                      <Button
                        size="xs"
                        variant="outlined"
                        onClick={async () => {
                          const url = `${window.location.origin}/n/${nodeSlug}`;
                          try {
                            await navigator.clipboard.writeText(url);
                            setCopied(true);
                            setTimeout(() => setCopied(false), 1200);
                          } catch (copyErr) {
                            console.warn('Copy link failed', copyErr);
                          }
                        }}
                      >
                        {copied ? 'Copied' : 'Copy link'}
                      </Button>
                    )}
                  </div>
                  <div><span className="font-semibold text-gray-700 dark:text-dark-100">Status:</span> {status.toUpperCase()}</div>
                </div>
              </div>
            )}
            {!readOnly && (
              <ImageUpload
                label="Cover image"
                value={coverFile}
                onChange={(file) => setCoverFile(file)}
                disabled={disableInputs}
              />
            )}
            {previewSrc && (
              <div className="overflow-hidden rounded-xl border border-gray-200 bg-gray-50 dark:border-dark-500 dark:bg-dark-700">
                {/* eslint-disable-next-line jsx-a11y/img-redundant-alt */}
                <img src={previewSrc} alt="Cover preview" className="h-36 w-full object-cover" />
              </div>
            )}
            {!readOnly && (
              <TInput
                label="Cover URL"
                placeholder="https://..."
                value={coverUrl}
                onChange={(e: any) => setCoverUrl(e.target.value)}
                disabled={disableInputs}
              />
            )}
            <div className="flex items-center justify-between rounded-xl border border-gray-200 px-4 py-3 dark:border-dark-500">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Visibility</div>
                <p className="text-sm text-gray-600 dark:text-dark-200">{isPublic ? 'Published for everyone' : 'Kept private for now'}</p>
              </div>
              <Switch checked={isPublic} onChange={(e: any) => setIsPublic(e.currentTarget.checked)} disabled={disableInputs} />
            </div>
            <div className="flex items-center justify-between rounded-xl border border-gray-200 px-4 py-3 dark:border-dark-500">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Comments</div>
                <p className="text-sm text-gray-600 dark:text-dark-200">{commentsEnabled ? 'Visitors can submit comments' : 'Comments are blocked for this node'}</p>
              </div>
              <Switch checked={commentsEnabled} onChange={(e: any) => setCommentsEnabled(e.currentTarget.checked)} disabled={disableInputs} />
            </div>
            {!readOnly && (
              <div className="grid gap-3">
                <TInput
                  label="Schedule publish at"
                  type="datetime-local"
                  value={publishAt}
                  onChange={(e: any) => setPublishAt(e.target.value)}
                  disabled={disableInputs}
                />
                <TInput
                  label="Schedule unpublish at"
                  type="datetime-local"
                  value={unpublishAt}
                  onChange={(e: any) => setUnpublishAt(e.target.value)}
                  disabled={disableInputs}
                />
              </div>
            )}
            {!readOnly && (
              <Button
                className="h-11 w-full rounded-2xl bg-primary-600 text-sm font-semibold text-white shadow-primary-500/30 transition hover:bg-primary-500 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={() => { void saveNode(); }}
                disabled={disableInputs || !title.trim()}
              >
                {submitLabel}
              </Button>
            )}
          </Card>

          {mode === 'view' && (
            <Card skin="shadow" padding="lg" className="space-y-4 bg-white/95 shadow-soft dark:bg-dark-800/90">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm-plus font-semibold text-gray-800 dark:text-dark-100">Related nodes</h3>
                  <p className="text-xs text-gray-500 dark:text-dark-300">Recommended via tags and semantic similarity.</p>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <select className="form-select h-9" value={algo} onChange={(e: any) => setAlgo(e.target.value)}>
                    <option value="mix">Smart mix</option>
                    <option value="tags">Shared tags</option>
                    <option value="fts">Semantic text</option>
                  </select>
                  <Button size="sm" variant="outlined" onClick={() => setAlgo((prev) => (prev === 'mix' ? 'tags' : prev))}>
                    Rotate
                  </Button>
                </div>
              </div>
              {related.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-gray-300 px-4 py-6 text-sm text-gray-500 dark:border-dark-600 dark:text-dark-300">
                  No recommendations yet. Publish and tag this node to see related items here.
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2">
                  {related.map((rel) => {
                    const coverSrc = rel.cover_url ? resolveMediaUrl(String(rel.cover_url)) : '';
                    return (
                      <div
                        key={rel.id}
                        className="flex h-full flex-col justify-between rounded-2xl border border-gray-200 bg-white/80 p-4 shadow-sm transition hover:border-primary-400/60 hover:shadow-md dark:border-dark-600 dark:bg-dark-800/80"
                      >
                        <div className="space-y-3">
                          <div className="truncate text-sm font-semibold text-gray-800 dark:text-dark-100">{rel.title || rel.slug || `Node ${rel.id}`}</div>
                          {coverSrc && (
                            <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-dark-600">
                              {/* eslint-disable-next-line jsx-a11y/img-redundant-alt */}
                              <img src={coverSrc} alt={rel.title || 'Related node'} className="h-28 w-full object-cover" />
                            </div>
                          )}
                        </div>
                        <div className="mt-4 flex items-center gap-2 text-sm">
                          <Button
                            size="sm"
                            variant="outlined"
                            onClick={() => navigate(`/nodes/new?id=${encodeURIComponent(String(rel.id))}&mode=view`)}
                          >
                            Inspect
                          </Button>
                          {rel.slug && (
                            <Button size="sm" variant="outlined" color="neutral" onClick={() => window.open(`/n/${rel.slug}`, '_blank')}>
                              Public view
                            </Button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </ContentLayout>
  );
}

import React from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ContentLayout } from '../ContentLayout';
import { Card, Input as TInput, Switch, Button, TagInput, RichTextEditor, ImageUpload, Spinner } from '@ui';
import { apiGet, apiPatch, apiPost, apiUploadMedia } from '../../../shared/api/client';

type Mode = 'create' | 'edit' | 'view';

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
  const [isPublic, setIsPublic] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [loadingExisting, setLoadingExisting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [nodeSlug, setNodeSlug] = React.useState<string | null>(null);
  const [authorId, setAuthorId] = React.useState<string | null>(null);
  const [copied, setCopied] = React.useState(false);
  const [status, setStatus] = React.useState<string>('draft');
  const [publishAt, setPublishAt] = React.useState<string>('');
  const [unpublishAt, setUnpublishAt] = React.useState<string>('');
  const [related, setRelated] = React.useState<any[]>([]);
  const [algo, setAlgo] = React.useState<'tags' | 'fts' | 'mix'>('mix');

  const submittingRef = React.useRef(false);

  React.useEffect(() => {
    if (!nodeId) {
      setNodeSlug(null);
      setAuthorId(null);
      return;
    }
    setLoadingExisting(true);
    setError(null);
    (async () => {
      try {
        const data = await apiGet(`/v1/nodes/${encodeURIComponent(nodeId)}`);
        setTitle(String(data?.title ?? ''));
        setTags(Array.isArray(data?.tags) ? data.tags : []);
        setContent(String(data?.content ?? data?.content_html ?? ''));
        setCoverUrl(String(data?.cover_url ?? ''));
        setCoverFile(null);
        setIsPublic(Boolean(data?.is_public));
        setStatus(String(data?.status ?? (data?.is_public ? 'published' : 'draft')));
        const pa = data?.publish_at ? String(data.publish_at) : '';
        const ua = data?.unpublish_at ? String(data.unpublish_at) : '';
        const toLocalInput = (v: string): string => {
          if (!v) return '';
          const d = new Date(v);
          if (isNaN(d.getTime())) return '';
          const pad = (n: number) => (n < 10 ? `0${n}` : String(n));
          return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
        }
        setPublishAt(toLocalInput(pa));
        setUnpublishAt(toLocalInput(ua));
        setNodeSlug(data?.slug ? String(data.slug) : data?.id != null ? `node-${data.id}` : null);
        setAuthorId(data?.author_id ? String(data.author_id) : null);
      } catch (e: any) {
        setError(`Failed to load node: ${e?.message || e}`);
      } finally {
        setLoadingExisting(false);
      }
    })();
    (async () => {
      try {
        const rel = await apiGet(`/v1/navigation/related/${encodeURIComponent(nodeId)}?limit=6&algo=${encodeURIComponent(algo)}`);
        setRelated(Array.isArray(rel) ? rel : []);
      } catch {
        setRelated([]);
      }
    })();
  }, [nodeId, algo]);

  const headerTitle = mode === 'view' ? 'View node' : mode === 'edit' ? 'Edit node' : 'New node';
  const submitLabel = mode === 'edit' ? 'Save changes' : 'Create node';

  async function saveNode() {
    if (readOnly) return;
    if (submittingRef.current) return;
    submittingRef.current = true;
    setBusy(true);
    setError(null);
      try {
        const body: any = {
          title: title.trim() || undefined,
          tags,
          is_public: isPublic,
        };
        // compute status from publish/unpublish and switch
        const now = new Date();
        const pa = publishAt ? new Date(publishAt) : null;
        const ua = unpublishAt ? new Date(unpublishAt) : null;
        let computedStatus: string | undefined = undefined;
        if (pa && pa.getTime() > now.getTime()) computedStatus = 'scheduled';
        if (ua && ua.getTime() > now.getTime() && isPublic) computedStatus = 'scheduled_unpublish';
        if (!computedStatus) computedStatus = isPublic ? 'published' : 'draft';
        body.status = computedStatus;
        body.publish_at = publishAt || undefined;
        body.unpublish_at = unpublishAt || undefined;
      if (coverFile && !coverUrl) {
        try {
          const up = await apiUploadMedia(coverFile);
          const url = (up?.url || up?.file?.url) as string | undefined;
          if (url) body.cover_url = url;
        } catch {
          // ignore upload errors, allow saving without cover
        }
      } else if (coverUrl && coverUrl.trim()) {
        body.cover_url = coverUrl.trim();
      }
      if (content && content.trim()) body.content = content;

      if (mode === 'edit' && nodeId) {
        await apiPatch(`/v1/nodes/${encodeURIComponent(nodeId)}`, body);
      } else {
        await apiPost('/v1/nodes', body);
      }
      navigate('/nodes/library');
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally {
      setBusy(false);
      submittingRef.current = false;
    }
  }

  return (
    <ContentLayout context="nodes">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-gray-800 dark:text-dark-100">{headerTitle}</h2>
        <div className="flex items-center gap-2">
          {mode === 'view' && nodeId && (
            <Button variant="outlined" onClick={() => navigate(`/nodes/new?id=${encodeURIComponent(nodeId)}`)}>
              Edit
            </Button>
          )}
          {mode === 'view' && nodeId && (
            <Button
              variant="outlined"
              onClick={async () => {
                try {
                  const res = await apiPost('/v1/navigation/next', { current_node_id: Number(nodeId), strategy: 'random' });
                  const nextId = res?.node_id;
                  if (nextId) navigate(`/nodes/new?id=${encodeURIComponent(String(nextId))}&mode=view`);
                } catch {}
              }}
            >
              Next
            </Button>
          )}
          <Button variant="outlined" color="neutral" onClick={() => navigate('/nodes/library')}>
            Back to list
          </Button>
        </div>
      </div>

      {(loadingExisting || busy) && (
        <div className="mb-3 flex items-center gap-2 text-sm text-gray-500">
          <Spinner size="sm" />
          <span>{loadingExisting ? 'Loading node...' : 'Saving...'}</span>
        </div>
      )}

      {error && <div className="mb-3 rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</div>}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="p-4 lg:col-span-2">
          <div className="space-y-3">
            <TInput
              label="Title"
              placeholder="Enter title"
              value={title}
              onChange={(e: any) => setTitle(e.target.value)}
              disabled={readOnly || busy || loadingExisting}
            />
            <TagInput
              label="Tags"
              value={tags}
              onChange={setTags}
              placeholder="story, ai"
              disabled={readOnly || busy || loadingExisting}
            />
            <RichTextEditor
              label="Node content"
              value={content}
              onChange={setContent}
              placeholder="Type content"
              readOnly={readOnly || busy || loadingExisting}
            />
          </div>
        </Card>

        <Card className="p-4 space-y-3">
          <h3 className="text-sm-plus font-semibold text-gray-800 dark:text-dark-100">Publishing</h3>
          {nodeId && (
            <div className="rounded border border-gray-200 bg-gray-50 p-3 text-xs text-gray-600 dark:border-dark-500 dark:bg-dark-700 dark:text-dark-200">
              <div className="flex flex-col gap-1">
                <div><span className="font-medium">ID:</span> {nodeId}</div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">Slug:</span>
                  <span>{nodeSlug || '-'}</span>
                  {!!nodeSlug && (
                    <button
                      type="button"
                      className="rounded bg-gray-200 px-2 py-0.5 text-xs text-gray-700 hover:bg-gray-300 dark:bg-dark-600 dark:text-dark-100"
                      onClick={async () => {
                        const url = `${window.location.origin}/n/${nodeSlug}`;
                        try { await navigator.clipboard.writeText(url); setCopied(true); setTimeout(() => setCopied(false), 1200); } catch {}
                      }}
                    >
                      Copy link
                    </button>
                  )}
                  {copied && <span className="text-green-600">Copied</span>}
                </div>
                {authorId && <div><span className="font-medium">Author:</span> {authorId}</div>}
                <div>
                  <span className="font-medium">Status:</span>{' '}
                  <span className="uppercase">{status}</span>
                </div>
              </div>
            </div>
          )}
          <div className="space-y-3">
            {!readOnly && (
              <ImageUpload
                label="Cover image"
                value={coverFile}
                onChange={(file) => setCoverFile(file)}
                disabled={readOnly || busy || loadingExisting}
              />
            )}
            {coverUrl && (
              <div className="rounded border border-gray-200 bg-gray-50 p-2 text-center dark:border-dark-500 dark:bg-dark-700">
                {/* eslint-disable-next-line jsx-a11y/img-redundant-alt */}
                <img src={coverUrl} alt="Cover" className="mx-auto max-h-48 rounded" />
              </div>
            )}
            {!readOnly && (
              <TInput
                label="Cover URL"
                placeholder="https://..."
                value={coverUrl}
                onChange={(e: any) => setCoverUrl(e.target.value)}
                disabled={readOnly || busy || loadingExisting}
              />
            )}
            <div className="flex items-center gap-3">
              <Switch
                checked={isPublic}
                onChange={(e: any) => setIsPublic(e.currentTarget.checked)}
                disabled={readOnly || busy || loadingExisting}
              />
              <span className="text-sm">Publish</span>
            </div>
            {!readOnly && (
              <div className="grid grid-cols-1 gap-2">
                <TInput
                  label="Schedule publish at"
                  type="datetime-local"
                  value={publishAt}
                  onChange={(e: any) => setPublishAt(e.target.value)}
                  disabled={readOnly || busy || loadingExisting}
                />
                <TInput
                  label="Schedule unpublish at"
                  type="datetime-local"
                  value={unpublishAt}
                  onChange={(e: any) => setUnpublishAt(e.target.value)}
                  disabled={readOnly || busy || loadingExisting}
                />
              </div>
            )}
            {!readOnly && (
              <Button disabled={busy || loadingExisting || !title.trim()} onClick={saveNode} className="w-full">
                {submitLabel}
              </Button>
            )}
          </div>
        </Card>
      </div>

      {mode === 'view' && (
        <Card className="mt-4 p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm-plus font-semibold text-gray-800 dark:text-dark-100">Explore more</h3>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-600">Algo</span>
              <select className="form-select h-8" value={algo} onChange={(e:any)=>setAlgo(e.target.value)}>
                <option value="mix">Mix</option>
                <option value="tags">Tags</option>
                <option value="fts">Text</option>
              </select>
              <Button variant="outlined" size="sm" onClick={async()=>{
                try {
                  const rel = await apiGet(`/v1/navigation/related/${encodeURIComponent(nodeId!)}?limit=6&algo=${encodeURIComponent(algo)}`);
                  setRelated(Array.isArray(rel)?rel:[]);
                } catch { setRelated([]);} 
              }}>Refresh</Button>
            </div>
          </div>
          {related.length === 0 && <div className="text-sm text-gray-500">No recommendations yet</div>}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {related.map((r) => (
              <div key={r.id} className="rounded border border-gray-200 p-3 dark:border-dark-500">
                <div className="text-sm font-medium text-gray-800 dark:text-dark-100 truncate">{r.title || r.slug || `Node ${r.id}`}</div>
                {r.cover_url && (
                  <div className="mt-2">
                    {/* eslint-disable-next-line jsx-a11y/img-redundant-alt */}
                    <img src={r.cover_url} alt="Cover" className="h-24 w-full rounded object-cover" />
                  </div>
                )}
                <div className="mt-2 flex items-center gap-2">
                  <Button variant="outlined" size="sm" onClick={() => navigate(`/nodes/new?id=${encodeURIComponent(String(r.id))}&mode=view`)}>
                    View
                  </Button>
                  {r.slug && (
                    <Button variant="outlined" size="sm" onClick={() => window.open(`/n/${r.slug}`, '_blank')}>Public</Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </ContentLayout>
  );
}


import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ContentLayout } from '../ContentLayout';
import { Card, Spinner, TablePagination } from '@ui';
import { apiGet, apiDelete } from '../../../shared/api/client';
import { EllipsisVerticalIcon, EyeIcon, PencilIcon, TrashIcon, MagnifyingGlassIcon, PlusIcon, LinkIcon } from '@heroicons/react/24/outline';

type EmbeddingStatus = 'ready' | 'pending' | 'disabled' | 'error' | 'unknown';

type NodeItem = {
  id: string;
  title?: string | null;
  slug?: string | null;
  author_name?: string | null;
  author_id?: string | null;
  is_public?: boolean;
  status?: string | null;
  updated_at?: string | null;
  embedding_status?: EmbeddingStatus | null;
  embedding_ready?: boolean;
};

type NodeStatus = 'all' | 'draft' | 'published' | 'scheduled' | 'scheduled_unpublish' | 'archived' | 'deleted';

const STATUS_OPTIONS: Array<{ value: NodeStatus; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'published', label: 'Published' },
  { value: 'draft', label: 'Draft' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'scheduled_unpublish', label: 'Scheduled Unpublish' },
  { value: 'archived', label: 'Archived' },
  { value: 'deleted', label: 'Deleted' },
];

const ALLOWED_EMBEDDING_STATUSES: ReadonlyArray<EmbeddingStatus> = ['ready', 'pending', 'disabled', 'error', 'unknown'];

function isEmbeddingStatus(value: string | null | undefined): value is EmbeddingStatus {
  if (!value) {
    return false;
  }
  return ALLOWED_EMBEDDING_STATUSES.includes(value as EmbeddingStatus);
}

function normalizeItem(raw: any): NodeItem {
  const id = raw?.id != null ? String(raw.id) : '';
  const slug = raw?.slug ? String(raw.slug) : id ? `node-${id}` : null;
  const statusRaw = typeof raw?.embedding_status === 'string' ? String(raw.embedding_status).trim().toLowerCase() : null;
  let embeddingStatus: EmbeddingStatus | null = null;
  if (isEmbeddingStatus(statusRaw)) {
    embeddingStatus = statusRaw as EmbeddingStatus;
  }
  let embeddingReady = raw?.embedding_ready === true || (Array.isArray(raw?.embedding) && raw.embedding.length > 0);
  if (embeddingStatus === 'ready') {
    embeddingReady = true;
  } else if (embeddingStatus === 'disabled') {
    embeddingReady = false;
  } else if (!embeddingStatus && embeddingReady) {
    embeddingStatus = 'ready';
  }
  return {
    id,
    title: raw?.title ?? '',
    slug,
    // prefer server-provided username; fallback only to null (avoid UUID where possible)
    author_name: raw?.author_name ?? null,
    author_id: raw?.author_id ?? null,
    is_public: typeof raw?.is_public === 'boolean' ? raw.is_public : undefined,
    status: raw?.status ?? null,
    updated_at: raw?.updated_at ?? raw?.updatedAt ?? null,
    embedding_status: embeddingStatus,
    embedding_ready: embeddingReady,
  };
}
export default function NodesPageEnhanced() {
  const navigate = useNavigate();
  const location = useLocation();
  const [items, setItems] = React.useState<NodeItem[]>([]);
  const [q, setQ] = React.useState('');
  const [slugQ, setSlugQ] = React.useState('');
  const [status, setStatus] = React.useState<NodeStatus>('all');
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [hasNext, setHasNext] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [openMenuRow, setOpenMenuRow] = React.useState<string | null>(null);
  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [sort, setSort] = React.useState<'updated_at' | 'title' | 'author' | 'status'>('updated_at');
  const [order, setOrder] = React.useState<'asc' | 'desc'>('desc');
  const [cols] = React.useState<{ slug: boolean; author: boolean; status: boolean; updated: boolean; embedding: boolean }>({ slug: true, author: true, status: true, updated: true, embedding: true });
  // Author filter (search by username, send author_id)
  const [authorId, setAuthorId] = React.useState<string>('');
  const [authorQuery, setAuthorQuery] = React.useState<string>('');
  const [userOpts, setUserOpts] = React.useState<{ id: string; username: string }[]>([]);
  const [showUserOpts, setShowUserOpts] = React.useState<boolean>(false);

  const selectedCount = selected.size;
  const embeddingStats = React.useMemo(() => {
    const counters = { ready: 0, pending: 0, disabled: 0, error: 0, unknown: 0 };
    items.forEach((item) => {
      const status = (item.embedding_status ?? 'unknown') as EmbeddingStatus | 'unknown';
      if (status === 'ready') counters.ready += 1;
      else if (status === 'pending') counters.pending += 1;
      else if (status === 'disabled') counters.disabled += 1;
      else if (status === 'error') counters.error += 1;
      else counters.unknown += 1;
    });
    const total = counters.ready + counters.pending + counters.disabled + counters.error + counters.unknown;
    return { ...counters, total };
  }, [items]);

  const columnsCount = 3 + (cols.slug ? 1 : 0) + (cols.author ? 1 : 0) + (cols.status ? 1 : 0) + (cols.updated ? 1 : 0) + (cols.embedding ? 1 : 0);
  const embeddingsDisabled = embeddingStats.total > 0 && embeddingStats.disabled === embeddingStats.total;
  const embeddingWarningMessage = React.useMemo(() => {
    if (embeddingStats.total === 0) return null;
    if (embeddingsDisabled) {
      return 'Embedding generation is disabled for this environment.';
    }
    const parts: string[] = [];
    if (embeddingStats.pending > 0) parts.push(`${embeddingStats.pending} pending`);
    if (embeddingStats.error > 0) parts.push(`${embeddingStats.error} failed`);
    if (embeddingStats.disabled > 0) parts.push(`${embeddingStats.disabled} disabled`);
    return parts.length ? `Embedding diagnostics: ${parts.join(', ')}.` : null;
  }, [embeddingStats, embeddingsDisabled]);

  const renderEmbeddingBadge = React.useCallback(
    (status?: EmbeddingStatus | null) => {
      const normalized = (status ?? 'unknown') as EmbeddingStatus | 'unknown';
      if (normalized === 'ready') return <span className="badge badge-success">Ready</span>;
      if (normalized === 'pending') return <span className="badge badge-warning">Pending</span>;
      if (normalized === 'disabled') return <span className="badge">Disabled</span>;
      if (normalized === 'error') return <span className="badge badge-error">Error</span>;
      return <span className="text-gray-500">—</span>;
    },
    [],
  );
  const headerStats = React.useMemo(() => {
    const total = items.length;
    const published = items.filter((it) => (it.status || '').toLowerCase() === 'published').length;
    const ratio = total ? Math.round((published / Math.max(total, 1)) * 100) : 0;
    const stats = [
      { label: 'Nodes in view', value: total || '--', hint: status === 'all' ? 'Current filter: all statuses' : `Filter: ${status}` },
      { label: 'Published share', value: `${ratio}%`, hint: `${published} published` },
      { label: 'Selected', value: selectedCount || 0, hint: selectedCount ? 'Bulk actions unlocked' : 'Select rows to stage actions' },
    ];
    if (embeddingStats.total > 0) {
      if (embeddingStats.disabled === embeddingStats.total) {
        stats.push({ label: 'Embeddings', value: 'Disabled', hint: 'Embedding generation flag is disabled' });
      } else {
        const parts: string[] = [];
        if (embeddingStats.pending > 0) parts.push(`${embeddingStats.pending} pending`);
        if (embeddingStats.error > 0) parts.push(`${embeddingStats.error} failed`);
        if (embeddingStats.disabled > 0) parts.push(`${embeddingStats.disabled} disabled`);
        stats.push({
          label: 'Embeddings',
          value: `${embeddingStats.ready}/${embeddingStats.total} ready`,
          hint: parts.length ? parts.join(', ') : 'All nodes have embeddings',
        });
      }
    }
    return stats;
  }, [items, selectedCount, status, embeddingStats]);

  const closeMenu = React.useCallback(() => setOpenMenuRow(null), []);

  React.useEffect(() => {
    const handler = () => setOpenMenuRow(null);
    window.addEventListener('click', handler);
    return () => window.removeEventListener('click', handler);
  }, []);

  React.useEffect(() => {
    const params = new URLSearchParams(location.search);
    const preset = params.get('status') as NodeStatus | null;
    if (preset && preset !== status && STATUS_OPTIONS.some((opt) => opt.value === preset)) {
      setStatus(preset);
      setPage(1);
    }
  }, [location.search, status]);

  const applyStatus = React.useCallback((value: NodeStatus) => {
    setStatus(value);
    setPage(1);
    const params = new URLSearchParams(location.search);
    if (value === 'all') params.delete('status');
    else params.set('status', value);
    const query = params.toString();
    navigate({ pathname: location.pathname, search: query ? `?${query}` : '' }, { replace: true });
  }, [location.pathname, location.search, navigate]);

  const isDraftFilter = status === 'draft';
  const hasCustomStatus = status !== 'all';

  function isUUIDLike(s: string | null | undefined) {
    if (!s) return false;
    return /^(?:[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/i.test(s);
  }

  async function enrichAuthorNames(list: NodeItem[]) {
    try {
      const needIds = Array.from(
        new Set(
          list
            .filter((it) => (!it.author_name || it.author_name === it.author_id || isUUIDLike(it.author_name)) && it.author_id)
            .map((it) => String(it.author_id))
        )
      );
      if (needIds.length === 0) return list;
      const cache = new Map<string, string | null>();
      for (const uid of needIds) {
        try {
          const res = await apiGet(`/v1/users/${encodeURIComponent(uid)}`);
          const u = res?.user || res?.data?.user;
          const name = (u?.username || u?.email || null) as string | null;
          cache.set(uid, name);
        } catch {
          cache.set(uid, null);
        }
      }
      return list.map((it) => ({ ...it, author_name: it.author_name || cache.get(String(it.author_id)) || it.author_name }));
    } catch {
      return list;
    }
  }

  async function load() {
    setLoading(true);
    try {
      const offset = (page - 1) * pageSize;
      const authorParam = authorId ? `&author_id=${encodeURIComponent(authorId)}` : '';
      const url = `/v1/admin/nodes/list?q=${encodeURIComponent(q)}&slug=${encodeURIComponent(slugQ)}&limit=${pageSize}&offset=${offset}&status=${status}&sort=${sort}&order=${order}${authorParam}`;
      const data = await apiGet(url);
      if (Array.isArray(data)) {
        let normalized = data.map(normalizeItem);
        // try to resolve usernames if backend didn't provide them
        normalized = await enrichAuthorNames(normalized);
        setItems(normalized);
        setHasNext(normalized.length === pageSize);
      } else {
        setItems([]);
        setHasNext(false);
      }
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    const t = setTimeout(load, 200);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, slugQ, status, page, pageSize, authorId, sort, order]);

  React.useEffect(() => {
    setSelected(new Set());
    setOpenMenuRow(null);
  }, [page, items]);

  return (
    <ContentLayout
      context="nodes"
      title="Node library"
      description="Search, refine, and orchestrate narrative nodes across every connected world."
      stats={headerStats}
    >
      <Card skin="shadow" className="relative p-4">
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="dark:text-dark-100 truncate text-base font-medium tracking-wide text-gray-800">Nodes</h2>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 dark:border-dark-500 dark:bg-dark-700">
                <MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />
                <input
                  className="h-9 w-64 bg-transparent text-sm outline-none placeholder:text-gray-400"
                  placeholder="Search title/ID..."
                  value={q}
                  onChange={(e) => {
                    setPage(1);
                    setQ(e.target.value);
                  }}
                />
              </div>
              <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 dark:border-dark-500 dark:bg-dark-700">
                <span className="text-xs text-gray-500">Slug</span>
                <input
                  className="h-9 w-56 bg-transparent text-sm outline-none placeholder:text-gray-400"
                  placeholder="16-hex"
                  value={slugQ}
                  onChange={(e) => {
                    setPage(1);
                    setSlugQ(e.target.value.trim());
                  }}
                />
              </div>
              {loading && <Spinner size="sm" />}
              <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 py-1 text-sm dark:border-dark-500 dark:bg-dark-700">
                <span className="text-xs text-gray-500">Sort</span>
                <select className="form-select h-9 w-40" value={sort} onChange={(e) => { setSort(e.target.value as any); setPage(1); }}>
                  <option value="updated_at">Updated</option>
                  <option value="title">Title</option>
                  <option value="author">Author</option>
                  <option value="status">Status</option>
                </select>
                <select className="form-select h-9 w-28" value={order} onChange={(e) => { setOrder(e.target.value as any); setPage(1); }}>
                  <option value="desc">Desc</option>
                  <option value="asc">Asc</option>
                </select>
              </div>
              <div className="relative flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 py-1 text-sm dark:border-dark-500 dark:bg-dark-700">
                <span className="text-xs text-gray-500">Author</span>
                <input
                  className="h-9 w-56 bg-transparent text-sm outline-none placeholder:text-gray-400"
                  placeholder="Search username..."
                  value={authorQuery}
                  onChange={async (e) => {
                    const v = e.target.value;
                    setAuthorQuery(v);
                    setShowUserOpts(true);
                    try {
                      const opts = await apiGet(`/v1/users/search?q=${encodeURIComponent(v)}&limit=10`);
                      if (Array.isArray(opts)) setUserOpts(opts);
                    } catch {}
                  }}
                  onFocus={async () => {
                    setShowUserOpts(true);
                    try {
                      const opts = await apiGet(`/v1/users/search?q=${encodeURIComponent(authorQuery)}&limit=10`);
                      if (Array.isArray(opts)) setUserOpts(opts);
                    } catch {}
                  }}
                />
                {authorId && (
                  <button className="rounded bg-gray-200 px-2 text-xs hover:bg-gray-300 dark:bg-dark-600" onClick={() => { setAuthorId(''); setAuthorQuery(''); setPage(1); }}>
                    Clear
                  </button>
                )}
                {showUserOpts && userOpts.length > 0 && (
                  <div className="absolute left-0 top-10 z-10 w-64 rounded border border-gray-300 bg-white shadow dark:border-dark-500 dark:bg-dark-700">
                    {userOpts.map((u) => (
                      <button
                        key={u.id}
                        className="block w-full truncate px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                        onClick={() => {
                          setAuthorId(u.id);
                          setAuthorQuery(u.username || u.id);
                          setShowUserOpts(false);
                          setPage(1);
                        }}
                      >
                        {u.username || u.id}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <button
                className="inline-flex h-9 w-9 items-center justify-center rounded hover:bg-gray-200/60 dark:hover:bg-dark-500"
                title="Create node"
                onClick={() => navigate('/nodes/new')}
              >
                <PlusIcon className="h-5 w-5 text-gray-600" />
              </button>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-sm">
            <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-1.5 dark:border-dark-500 dark:bg-dark-700">
              <span className="text-xs text-gray-500">Status</span>
              <select className="form-select h-8 w-44 text-xs" value={status} onChange={(e) => applyStatus(e.target.value as NodeStatus)}>
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <button
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${isDraftFilter ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-600/60 dark:bg-primary-900/30 dark:text-primary-300' : 'border-gray-300 text-gray-600 hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60'}`}
              onClick={() => applyStatus('draft')}
            >
              Drafts only
            </button>
            {hasCustomStatus && (
              <button
                className="rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60"
                onClick={() => applyStatus('all')}
              >
                Clear filter
              </button>
            )}
            <button
              className="rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60"
              onClick={() => navigate('/tools/import-export?scope=nodes')}
            >
              Import / export
            </button>
            <button
              className="rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60"
              onClick={() => navigate('/notifications?compose=nodes')}
            >
              Announce update
            </button>
          </div>
        </div>

        {selected.size > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-2 rounded border border-primary-200 bg-primary-50 p-3 text-sm dark:border-primary-700 dark:bg-primary-900/20">
            <span className="font-medium">Selected: {selected.size}</span>
            <button
              className="btn-base btn bg-green-600 text-white hover:bg-green-700 disabled:opacity-60"
              onClick={async () => {
                const ids = Array.from(selected).map((s) => parseInt(s, 10)).filter((n) => !isNaN(n));
                try {
                  await fetch('/v1/admin/nodes/bulk/status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids, status: 'published' }) });
                  load();
                } catch {}
              }}
            >
              Publish
            </button>
            <button
              className="btn-base btn bg-yellow-600 text-white hover:bg-yellow-700 disabled:opacity-60"
              onClick={async () => {
                const ids = Array.from(selected).map((s) => parseInt(s, 10)).filter((n) => !isNaN(n));
                try {
                  await fetch('/v1/admin/nodes/bulk/status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids, status: 'draft' }) });
                  load();
                } catch {}
              }}
            >
              Unpublish
            </button>
            <button
              className="btn-base btn bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
              onClick={async () => {
                const when = prompt('Publish at (YYYY-MM-DDTHH:mm)');
                if (!when) return;
                const ids = Array.from(selected).map((s) => parseInt(s, 10)).filter((n) => !isNaN(n));
                try {
                  await fetch('/v1/admin/nodes/bulk/status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids, status: 'scheduled', publish_at: when }) });
                  load();
                } catch {}
              }}
            >
              Schedule publish
            </button>
            <button
              className="btn-base btn bg-gray-600 text-white hover:bg-gray-700 disabled:opacity-60"
              onClick={async () => {
                const when = prompt('Unpublish at (YYYY-MM-DDTHH:mm)');
                if (!when) return;
                const ids = Array.from(selected).map((s) => parseInt(s, 10)).filter((n) => !isNaN(n));
                try {
                  await fetch('/v1/admin/nodes/bulk/status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids, status: 'scheduled_unpublish', unpublish_at: when }) });
                  load();
                } catch {}
              }}
            >
              Schedule unpublish
            </button>
            <button
              className="btn-base btn bg-slate-600 text-white hover:bg-slate-700 disabled:opacity-60"
              onClick={async () => {
                const ids = Array.from(selected).map((s) => parseInt(s, 10)).filter((n) => !isNaN(n));
                try {
                  await fetch('/v1/admin/nodes/bulk/status', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids, status: 'archived' }) });
                  load();
                } catch {}
              }}
            >
              Archive
            </button>
            <button
              className="btn-base btn bg-red-600 text-white hover:bg-red-700 disabled:opacity-60"
              onClick={async () => {
                if (!confirm(`Delete ${selected.size} selected node(s)?`)) return;
                for (const id of Array.from(selected)) {
                  try { await apiDelete(`/v1/admin/nodes/${encodeURIComponent(id)}`); } catch {}
                }
                setItems((it) => it.filter((x) => !selected.has(x.id)));
                setSelected(new Set());
              }}
            >
              Delete selected
            </button>
          </div>
        )}
        {embeddingWarningMessage && (
          <div className="mt-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-400/50 dark:bg-amber-950/30 dark:text-amber-200">
            {embeddingWarningMessage}
          </div>
        )}


        <div className="mt-4 hide-scrollbar overflow-x-auto overflow-y-visible">
          <table className="min-w-[960px] w-full text-left">
            <thead>
              <tr className="bg-gray-200 text-gray-800 uppercase">
                <th className="py-2 px-3">
                  <input
                    type="checkbox"
                    className="form-checkbox accent-primary-600 align-middle"
                    checked={items.length > 0 && items.every((i) => selected.has(i.id))}
                    onChange={(e) => {
                      const all = new Set(selected);
                      if (e.currentTarget.checked) items.forEach((i) => all.add(i.id));
                      else items.forEach((i) => all.delete(i.id));
                      setSelected(all);
                    }}
                  />
                </th>
                <th className="py-2 px-3">Title</th>
                {cols.slug && <th className="py-2 px-3">Slug</th>}
                {cols.author && <th className="py-2 px-3">Author</th>}
                {cols.status && <th className="py-2 px-3">Status</th>}
                {cols.embedding && <th className="py-2 px-3">Embedding</th>}
                {cols.updated && <th className="py-2 px-3">Updated</th>}
                <th className="py-2 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td className="py-3 px-3" colSpan={columnsCount}>Loading...</td></tr>
              )}
              {!loading && items.length === 0 && (
                <tr><td className="py-8 px-3 text-center text-sm text-gray-500" colSpan={columnsCount}>No nodes yet</td></tr>
              )}
              {!loading && items.map((row) => {
                const s = (row.status || '').toLowerCase();
                const pub = s ? s === 'published' : (row.is_public ?? false);
                const updated = row.updated_at ? String(row.updated_at).slice(0, 19).replace('T', ' ') : '-';
                return (
                  <tr key={row.id} className="border-b border-gray-200">
                    <td className="py-2 px-3">
                      <input
                        type="checkbox"
                        className="form-checkbox accent-primary-600 align-middle"
                        checked={selected.has(row.id)}
                        onChange={(e) => {
                          const s = new Set(selected);
                          if (e.currentTarget.checked) s.add(row.id);
                          else s.delete(row.id);
                          setSelected(s);
                        }}
                      />
                    </td>
                    <td className="py-2 px-3"><span className="font-medium text-gray-800">{row.title || '-'}</span></td>
                    {cols.slug && <td className="py-2 px-3">{row.slug ? (<code className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700">{row.slug}</code>) : <span className="text-gray-500">-</span>}</td>}
                    {cols.author && <td className="py-2 px-3 text-gray-700">{row.author_name || '-'}</td>}
                    {cols.status && <td className="py-2 px-3">
                      {s === 'scheduled' && <span className="badge badge-info">Scheduled</span>}
                      {s === 'scheduled_unpublish' && <span className="badge badge-info">Will unpublish</span>}
                      {s === 'archived' && <span className="badge">Archived</span>}
                      {s === 'deleted' && <span className="badge badge-error">Deleted</span>}
                      {!s && (pub ? <span className="badge badge-success">Published</span> : <span className="badge badge-warning">Draft</span>)}
                      {s && !['scheduled','scheduled_unpublish','archived','deleted'].includes(s) && (s === 'published' ? <span className="badge badge-success">Published</span> : <span className="badge badge-warning">Draft</span>)}
                    </td>}
                    {cols.embedding && (
                      <td className="py-2 px-3">{renderEmbeddingBadge(row.embedding_status)}</td>
                    )}
                    {cols.updated && <td className="py-2 px-3 text-gray-500">{updated}</td>}
                    <td className="py-2 px-3">
                      <div
                        className="relative flex items-center justify-end"
                        role="presentation"
                        tabIndex={-1}
                        onClick={(e) => e.stopPropagation()}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.stopPropagation();
                          }
                        }}
                      >
                        <button
                          className="inline-flex h-8 w-8 items-center justify-center rounded hover:bg-gray-200/60 dark:hover:bg-dark-500"
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenMenuRow((v) => (v === row.id ? null : row.id));
                          }}
                        >
                          <EllipsisVerticalIcon className="h-5 w-5 text-gray-500" />
                        </button>
                        {openMenuRow === row.id && (
                          <div className="absolute right-0 top-9 z-30 w-48 rounded-md border border-gray-200 bg-white shadow-lg dark:border-dark-500 dark:bg-dark-700">
                            <button
                              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600 disabled:opacity-50"
                              onClick={async () => {
                                const slug = row.slug || '';
                                const url = slug ? `${window.location.origin}/n/${slug}` : `${window.location.origin}/nodes/new?id=${encodeURIComponent(row.id)}&mode=view`;
                                try { await navigator.clipboard.writeText(url); } catch {}
                                closeMenu();
                              }}
                              disabled={!row.slug}
                            >
                              <LinkIcon className="h-4 w-4" /> Copy link
                            </button>
                            {s === 'deleted' && (
                              <button
                                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-green-700 hover:bg-green-50 dark:hover:bg-green-500/20"
                                onClick={async () => {
                                  closeMenu();
                                  try {
                                    await fetch(`/v1/admin/nodes/${encodeURIComponent(row.id)}/restore`, { method: 'POST' });
                                    await load();
                                  } catch {}
                                }}
                              >
                                Restore
                              </button>
                            )}
                            <button
                              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                              onClick={() => {
                                closeMenu();
                                navigate(`/nodes/new?id=${encodeURIComponent(row.id)}&mode=view`);
                              }}
                            >
                              <EyeIcon className="h-4 w-4" /> View
                            </button>
                            <button
                              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                              onClick={() => {
                                closeMenu();
                                navigate(`/nodes/new?id=${encodeURIComponent(row.id)}`);
                              }}
                            >
                              <PencilIcon className="h-4 w-4" /> Edit
                            </button>
                            <button
                              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-500/20"
                              onClick={async () => {
                                closeMenu();
                                if (!confirm('Delete this node?')) return;
                                try { await apiDelete(`/v1/admin/nodes/${encodeURIComponent(row.id)}`); } catch {}
                                setItems((it) => it.filter((x) => x.id !== row.id));
                              }}
                            >
                              <TrashIcon className="h-4 w-4" /> Delete
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <TablePagination

          page={page}

          pageSize={pageSize}

          currentCount={items.length}

          hasNext={hasNext}

          onPageChange={(p: number) => setPage(p)}

          onPageSizeChange={(size) => { setPageSize(size); setPage(1); }}

        />
      </Card>
    </ContentLayout>
  );
}










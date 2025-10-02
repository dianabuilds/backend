import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { ContentLayout } from '../ContentLayout';
import { Badge, Card, TablePagination, useToast } from '@ui';
import { apiDelete, apiGet, apiPost } from '../../../shared/api/client';
import { usePaginatedQuery } from '../../../shared/hooks/usePaginatedQuery';
import { useConfirmDialog } from '../../../shared/hooks/useConfirmDialog';
import { usePromptDialog } from '../../../shared/hooks/usePromptDialog';
import { extractErrorMessage } from '../../../shared/utils/errors';
import { translate } from '../../../shared/i18n/locale';

import { NodesFilters } from './components/NodesFilters';
import { NodesBulkActions } from './components/NodesBulkActions';
import { NodesTable } from './components/NodesTable';
import { useAuthorSearch } from './hooks/useAuthorSearch';
import type { EmbeddingStatus, NodeItem, NodeStatus, SortKey, SortOrder, UserOption } from './types';

const STATUS_OPTIONS: Array<{ value: NodeStatus; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'published', label: 'Published' },
  { value: 'draft', label: 'Draft' },
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'scheduled_unpublish', label: 'Scheduled unpublish' },
  { value: 'archived', label: 'Archived' },
  { value: 'deleted', label: 'Deleted' },
];

const EMBEDDING_STATUS_THEME: Record<EmbeddingStatus | 'missing', { color: 'success' | 'warning' | 'info' | 'error' | 'neutral'; label: string }> = {
  ready: { color: 'success', label: 'Ready' },
  pending: { color: 'info', label: 'Pending' },
  disabled: { color: 'neutral', label: 'Disabled' },
  error: { color: 'error', label: 'Error' },
  unknown: { color: 'warning', label: 'Unknown' },
  missing: { color: 'warning', label: 'Missing' },
};

const ALLOWED_EMBEDDING_STATUSES: ReadonlyArray<EmbeddingStatus> = ['ready', 'pending', 'disabled', 'error', 'unknown'];

const TOAST_COPY = {
  linkCopied: { en: 'Node link copied to clipboard', ru: '?????? ?? ???? ??????????? ? ?????' },
  restoreSuccess: { en: 'Node restored', ru: '???? ????????????' },
  restoreError: { en: 'Failed to restore node', ru: '?? ??????? ???????????? ????' },
  deleteSuccess: { en: 'Node deleted', ru: '???? ??????' },
  deleteError: { en: 'Failed to delete node', ru: '?? ??????? ??????? ????' },
  bulkPublish: { en: 'Selected nodes marked as published', ru: '????????? ???? ????????????' },
  bulkDraft: { en: 'Selected nodes moved to drafts', ru: '????????? ???? ?????????? ? ?????????' },
  bulkSchedulePublish: { en: 'Publish schedule updated', ru: '?????????? ?????????? ?????????' },
  bulkScheduleUnpublish: { en: 'Unpublish schedule updated', ru: '?????????? ?????? ? ?????????? ?????????' },
  bulkArchive: { en: 'Selected nodes archived', ru: '????????? ???? ?????????? ? ?????' },
  bulkDeleteSuccess: { en: 'Selected nodes deleted', ru: '????????? ???? ???????' },
  bulkError: { en: 'Bulk action failed', ru: '?? ??????? ????????? ???????? ????????' },
};

type NodesListMeta = {
  total?: number | null;
  published?: number | null;
  drafts?: number | null;
  pendingEmbeddings?: number | null;
};

type NodesListResponse = {
  items?: unknown[];
  data?: {
    items?: unknown[];
    total?: number | null;
    has_next?: boolean | null;
    hasNext?: boolean | null;
    stats?: Record<string, unknown>;
  };
  total?: number | null;
  has_next?: boolean | null;
  hasNext?: boolean | null;
  stats?: Record<string, unknown>;
  meta?: {
    total?: number | null;
    stats?: Record<string, unknown>;
  };
  summary?: Record<string, unknown>;
};

type NodesFetchResult = {
  source: NodesListResponse | unknown[];
  items: NodeItem[];
};

function isEmbeddingStatus(value: string | null | undefined): value is EmbeddingStatus {
  if (!value) return false;
  return ALLOWED_EMBEDDING_STATUSES.includes(value as EmbeddingStatus);
}

function isUUIDLike(value: string | null | undefined) {
  if (!value) return false;
  return /^(?:[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/i.test(value);
}

function normalizeItem(raw: any): NodeItem {
  const id = raw?.id != null ? String(raw.id) : '';
  const slug = raw?.slug ? String(raw.slug) : id ? `node-${id}` : null;
  const statusRaw = typeof raw?.embedding_status === 'string' ? String(raw.embedding_status).trim().toLowerCase() : null;
  let embeddingStatus: EmbeddingStatus | null = null;
  if (isEmbeddingStatus(statusRaw)) {
    embeddingStatus = statusRaw;
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
    author_name: raw?.author_name ?? null,
    author_id: raw?.author_id ?? null,
    is_public: typeof raw?.is_public === 'boolean' ? raw.is_public : undefined,
    status: raw?.status ?? null,
    updated_at: raw?.updated_at ?? raw?.updatedAt ?? null,
    embedding_status: embeddingStatus,
    embedding_ready: embeddingReady,
  };
}

function firstNumberCandidate(...values: Array<unknown>): number | null {
  for (const value of values) {
    if (typeof value === 'number' && Number.isFinite(value)) {
      return value;
    }
    if (typeof value === 'string') {
      const parsed = Number(value);
      if (!Number.isNaN(parsed)) {
        return parsed;
      }
    }
  }
  return null;
}

export default function NodesPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [q, setQ] = React.useState('');
  const [slugQuery, setSlugQuery] = React.useState('');
  const [status, setStatus] = React.useState<NodeStatus>('all');
  const [sort, setSort] = React.useState<SortKey>('updated_at');
  const [order, setOrder] = React.useState<SortOrder>('desc');
  const [openMenuRow, setOpenMenuRow] = React.useState<string | null>(null);
  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const columnVisibility = React.useMemo(
    () => ({ slug: true, author: true, status: true, updated: true, embedding: true }),
    [],
  );
  const [listMeta, setListMeta] = React.useState<NodesListMeta>({});
  const { confirm, confirmationElement } = useConfirmDialog();
  const { prompt, promptElement } = usePromptDialog();
  const { pushToast } = useToast();
  const {
    authorId,
    authorQuery,
    options: authorOptions,
    showOptions: showAuthorOptions,
    handleChange: changeAuthorQuery,
    handleFocus: focusAuthorField,
    handleSelect: selectAuthorOption,
    handleClear: clearAuthorSelection,
  } = useAuthorSearch();
  const authorLookupCacheRef = React.useRef(new Map<string, string | null>());

  const enrichAuthorNames = React.useCallback(
    async (list: NodeItem[]) => {
      if (!list.length) return list;
      try {
        const needIds = Array.from(
          new Set(
            list
              .filter(
                (item) =>
                  (!item.author_name ||
                    item.author_name === item.author_id ||
                    isUUIDLike(item.author_name)) &&
                  item.author_id,
              )
              .map((item) => String(item.author_id)),
          ),
        );
        if (needIds.length === 0) return list;
        const cache = authorLookupCacheRef.current;
        const missing = needIds.filter((id) => !cache.has(id));
        if (missing.length > 0) {
          await Promise.all(
            missing.map(async (uid) => {
              try {
                const res = await apiGet(`/v1/users/${encodeURIComponent(uid)}`);
                const user = res?.user || res?.data?.user;
                const rawName: string | null = (user?.username || user?.email || null) ?? null;
                cache.set(uid, rawName && rawName.trim().length ? rawName : null);
              } catch (err) {
                cache.set(uid, null);
                console.error('Failed to resolve author info', uid, err);
              }
            }),
          );
        }
        return list.map((item) => {
          if (!item.author_id || (item.author_name && item.author_name !== item.author_id && !isUUIDLike(item.author_name))) {
            return item;
          }
          const cached = cache.get(String(item.author_id));
          if (typeof cached === 'string' && cached.length) {
            return { ...item, author_name: cached };
          }
          return item;
        });
      } catch (err) {
        console.error('Failed to enrich author names', err);
        return list;
      }
    },
    [],
  );

  const {
    items,
    setItems,
    page,
    setPage,
    pageSize,
    setPageSize,
    hasNext,
    loading,
    error,
    setError,
    refresh,
  } = usePaginatedQuery<NodeItem, NodesFetchResult>({
    initialPageSize: 20,
    dependencies: [q, slugQuery, status, sort, order, authorId, enrichAuthorNames],
    debounceMs: 250,
    fetcher: async ({ page: currentPage, pageSize: currentPageSize, signal }) => {
      const params = new URLSearchParams();
      if (q.trim()) params.set('q', q.trim());
      if (slugQuery.trim()) params.set('slug', slugQuery.trim());
      params.set('limit', String(currentPageSize));
      params.set('offset', String((currentPage - 1) * currentPageSize));
      params.set('sort', sort);
      params.set('order', order);
      if (status && status !== 'all') params.set('status', status);
      if (authorId) params.set('author_id', authorId);
      const data = await apiGet<NodesListResponse | unknown[]>(
        `/v1/admin/nodes/list?${params.toString()}`,
        { signal },
      );
      const rawItems: unknown[] = Array.isArray(data)
        ? data
        : Array.isArray((data as any)?.items)
        ? (data as any)?.items
        : Array.isArray((data as any)?.data?.items)
        ? (data as any).data.items
        : [];
      const normalized = await enrichAuthorNames(rawItems.map(normalizeItem));
      return { source: data, items: normalized };
    },
    mapResponse: (result, { pageSize: currentPageSize }) => {
      const source = result.source;
      const container =
        Array.isArray(source) || !source
          ? source
          : source.data && typeof source.data === 'object'
          ? { ...source, ...source.data, items: (source.data as any)?.items ?? source.items }
          : source;
      const statsSource: Record<string, unknown> | undefined =
        (container as any)?.stats ??
        (source as any)?.stats ??
        (source as any)?.meta?.stats ??
        (source as any)?.summary ??
        undefined;

      const total = firstNumberCandidate(
        (container as any)?.total,
        (source as any)?.total,
        (source as any)?.meta?.total,
        statsSource?.total,
        (container as any)?.count,
        (container as any)?.items_count,
      );
      const published = firstNumberCandidate(
        statsSource?.published,
        statsSource?.published_count,
        statsSource?.published_total,
      );
      const drafts = firstNumberCandidate(
        statsSource?.drafts,
        statsSource?.draft_count,
        statsSource?.draft_total,
      );
      const pendingEmbeddings = firstNumberCandidate(
        statsSource?.pendingEmbeddings,
        statsSource?.pending_embeddings,
        statsSource?.embedding_pending,
        statsSource?.pending,
        statsSource?.pending_embeddings_total,
      );

      setListMeta({
        total,
        published,
        drafts,
        pendingEmbeddings,
      });

      const hasNextExplicit = (container as any)?.has_next ?? (container as any)?.hasNext ?? (source as any)?.has_next ?? (source as any)?.hasNext;
      const computedHasNext =
        typeof hasNextExplicit === 'boolean' ? hasNextExplicit : result.items.length === currentPageSize;

      return {
        items: result.items,
        hasNext: computedHasNext,
        total: typeof total === 'number' ? total : undefined,
      };
    },
    onError: (err) => extractErrorMessage(err, 'Failed to load nodes'),
  });

  React.useEffect(() => {
    const params = new URLSearchParams(location.search);
    const preset = params.get('status') as NodeStatus | null;
    if (preset && preset !== status && STATUS_OPTIONS.some((option) => option.value === preset)) {
      setStatus(preset);
      setPage(1);
    }
  }, [location.search, setPage, status]);

  React.useEffect(() => {
    setSelected(new Set());
    setOpenMenuRow(null);
  }, [page, items]);

  const handleQueryChange = React.useCallback(
    (value: string) => {
      setQ(value);
      setPage(1);
    },
    [setPage],
  );

  const handleSlugChange = React.useCallback(
    (value: string) => {
      setSlugQuery(value);
      setPage(1);
    },
    [setPage],
  );

  const handleSortChange = React.useCallback(
    (value: SortKey) => {
      setSort(value);
      setPage(1);
    },
    [setPage],
  );

  const handleOrderChange = React.useCallback(
    (value: SortOrder) => {
      setOrder(value);
      setPage(1);
    },
    [setPage],
  );

  const applyStatus = React.useCallback(
    (nextStatus: NodeStatus) => {
      setStatus(nextStatus);
      setPage(1);
      const params = new URLSearchParams(location.search);
      if (nextStatus === 'all') params.delete('status');
      else params.set('status', nextStatus);
      const query = params.toString();
      navigate({ pathname: location.pathname, search: query ? `?${query}` : '' }, { replace: true });
    },
    [location.pathname, location.search, navigate, setPage],
  );

  const handleAuthorChange = React.useCallback(
    (value: string) => {
      changeAuthorQuery(value);
      setPage(1);
    },
    [changeAuthorQuery, setPage],
  );

  const handleAuthorFocus = React.useCallback(() => {
    focusAuthorField();
  }, [focusAuthorField]);

  const handleAuthorSelect = React.useCallback(
    (option: UserOption) => {
      selectAuthorOption(option);
      setPage(1);
    },
    [selectAuthorOption, setPage],
  );

  const handleAuthorClear = React.useCallback(() => {
    clearAuthorSelection();
    setPage(1);
  }, [clearAuthorSelection, setPage]);

  const closeMenu = React.useCallback(() => setOpenMenuRow(null), []);

  const handleToggleRow = React.useCallback((id: string, checked: boolean) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }, []);

  const handleToggleAll = React.useCallback(
    (checked: boolean) => {
      if (!checked) {
        setSelected(new Set());
        return;
      }
      setSelected(new Set(items.map((item) => item.id)));
    },
    [items],
  );

  const handleCopyLink = React.useCallback(
    (row: NodeItem) => {
      if (!row.slug) return;
      const link = `${window.location.origin}/n/${row.slug}`;
      void navigator.clipboard.writeText(link);
      pushToast({ intent: 'info', description: translate(TOAST_COPY.linkCopied) });
      closeMenu();
    },
    [closeMenu, pushToast],
  );

  const handleRestore = React.useCallback(
    async (row: NodeItem) => {
      closeMenu();
      try {
        await apiPost(`/v1/admin/nodes/${encodeURIComponent(row.id)}/restore`, {});
        await refresh();
        pushToast({ intent: 'success', description: translate(TOAST_COPY.restoreSuccess) });
      } catch (err) {
        const message = extractErrorMessage(err, translate(TOAST_COPY.deleteError));
        setError(message);
        pushToast({ intent: 'error', description: message });
      }
    },
    [closeMenu, pushToast, refresh, setError],
  );

  const handleView = React.useCallback(
    (row: NodeItem) => {
      closeMenu();
      navigate(`/nodes/new?id=${encodeURIComponent(row.id)}&mode=view`);
    },
    [closeMenu, navigate],
  );

  const handleEdit = React.useCallback(
    (row: NodeItem) => {
      closeMenu();
      navigate(`/nodes/new?id=${encodeURIComponent(row.id)}`);
    },
    [closeMenu, navigate],
  );

  const handleDeleteRow = React.useCallback(
    async (row: NodeItem) => {
      closeMenu();
      const confirmed = await confirm({
        title: 'Delete node',
        description: 'Delete this node? This action cannot be undone.',
        confirmLabel: 'Delete',
        cancelLabel: 'Cancel',
        destructive: true,
      });
      if (!confirmed) return;
      try {
        await apiDelete(`/v1/admin/nodes/${encodeURIComponent(row.id)}`);
        setItems((prev) => prev.filter((item) => item.id !== row.id));
        setSelected((prev) => {
          const next = new Set(prev);
          next.delete(row.id);
          return next;
        });
        pushToast({ intent: 'success', description: translate(TOAST_COPY.deleteSuccess) });
      } catch (err) {
        const message = extractErrorMessage(err, translate(TOAST_COPY.deleteError));
        setError(message);
        pushToast({ intent: 'error', description: message });
      }
    },
    [closeMenu, confirm, pushToast, setItems, setError],
  );

  const bulkAction = React.useCallback(
    async (payload: Record<string, unknown>, successMessage: Record<'en' | 'ru', string>) => {
      const ids = Array.from(selected);
      if (!ids.length) return false;
      try {
        await apiPost('/v1/admin/nodes/bulk/status', { ids, ...payload });
        setSelected(new Set());
        await refresh();
        pushToast({ intent: 'success', description: translate(successMessage) });
        return true;
      } catch (err) {
        const message = extractErrorMessage(err, translate(TOAST_COPY.bulkError));
        setError(message);
        pushToast({ intent: 'error', description: message });
        return false;
      }
    },
    [pushToast, refresh, selected, setError],
  );

  const handleBulkPublish = React.useCallback(async () => {
    await bulkAction({ status: 'published' }, TOAST_COPY.bulkPublish);
  }, [bulkAction]);

  const handleBulkUnpublish = React.useCallback(async () => {
    await bulkAction({ status: 'draft' }, TOAST_COPY.bulkDraft);
  }, [bulkAction]);

  const handleBulkSchedulePublish = React.useCallback(async () => {
    const value = await prompt({
      title: 'Schedule publish',
      description: 'Set publish time (YYYY-MM-DDTHH:mm)',
      placeholder: '2025-10-02T10:00',
      submitLabel: 'Schedule',
      cancelLabel: 'Cancel',
    });
    if (!value) return;
    await bulkAction({ status: 'scheduled', publish_at: value }, TOAST_COPY.bulkSchedulePublish);
  }, [bulkAction, prompt]);

  const handleBulkScheduleUnpublish = React.useCallback(async () => {
    const value = await prompt({
      title: 'Schedule unpublish',
      description: 'Set unpublish time (YYYY-MM-DDTHH:mm)',
      placeholder: '2025-10-02T18:00',
      submitLabel: 'Schedule',
      cancelLabel: 'Cancel',
    });
    if (!value) return;
    await bulkAction({ status: 'scheduled_unpublish', unpublish_at: value }, TOAST_COPY.bulkScheduleUnpublish);
  }, [bulkAction, prompt]);

  const handleBulkArchive = React.useCallback(async () => {
    await bulkAction({ status: 'archived' }, TOAST_COPY.bulkArchive);
  }, [bulkAction]);

  const handleBulkDelete = React.useCallback(async () => {
    const selectedCount = selected.size;
    if (selectedCount === 0) return;
    const confirmed = await confirm({
      title: 'Delete selected nodes',
      description: `Delete ${selectedCount} selected node(s)? This action cannot be undone.`,
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
      destructive: true,
    });
    if (!confirmed) return;
    const ids = Array.from(selected);
    const idSet = new Set(ids);
    let failure: string | null = null;
    for (const id of ids) {
      try {
        await apiDelete(`/v1/admin/nodes/${encodeURIComponent(id)}`);
      } catch (err) {
        if (!failure) {
          failure = extractErrorMessage(err, translate(TOAST_COPY.deleteError));
        }
      }
    }
    setItems((prev) => prev.filter((item) => !idSet.has(item.id)));
    setSelected(new Set());
    if (failure) {
      setError(failure);
      pushToast({ intent: 'error', description: failure });
    } else {
      pushToast({ intent: 'success', description: translate(TOAST_COPY.bulkDeleteSuccess) });
    }
  }, [confirm, pushToast, selected, setError, setItems]);

  const handleCreateNode = React.useCallback(() => navigate('/nodes/new'), [navigate]);
  const handleImportExport = React.useCallback(
    () => navigate('/tools/import-export?scope=nodes'),
    [navigate],
  );
  const handleAnnounce = React.useCallback(
    () => navigate('/notifications?compose=nodes'),
    [navigate],
  );

  const renderEmbeddingBadge = React.useCallback((status?: EmbeddingStatus | null) => {
    const normalized = status ?? 'unknown';
    const theme = EMBEDDING_STATUS_THEME[normalized] ?? EMBEDDING_STATUS_THEME.unknown;
    return (
      <Badge color={theme.color} variant="soft">
        {theme.label}
      </Badge>
    );
  }, []);

  const selectedCount = selected.size;

  const columnsCount = React.useMemo(
    () =>
      1 +
      Number(columnVisibility.slug) +
      Number(columnVisibility.author) +
      Number(columnVisibility.status) +
      Number(columnVisibility.embedding) +
      Number(columnVisibility.updated) +
      1,
    [columnVisibility],
  );

  const headerStats = React.useMemo(
    () => [
      { label: 'Nodes', value: listMeta.total != null ? listMeta.total.toLocaleString() : '?' },
      { label: 'Published', value: listMeta.published != null ? listMeta.published.toLocaleString() : '?' },
      { label: 'Drafts', value: listMeta.drafts != null ? listMeta.drafts.toLocaleString() : '?' },
    ],
    [listMeta.drafts, listMeta.published, listMeta.total],
  );

  const embeddingWarningMessage = React.useMemo(() => {
    const pendingCount = listMeta.pendingEmbeddings ?? items.filter((item) => item.embedding_status === 'pending').length;
    const errorCount = items.filter((item) => item.embedding_status === 'error').length;
    if (!pendingCount && !errorCount) return null;
    if (errorCount && pendingCount) {
      return `${pendingCount} node(s) still queue embeddings and ${errorCount} failed. Refresh embeddings to keep discovery accurate.`;
    }
    if (pendingCount) {
      return `${pendingCount} node(s) still need embeddings. Queue or refresh embeddings to keep search results relevant.`;
    }
    return `${errorCount} node(s) failed to build embeddings. Retry to restore semantic search coverage.`;
  }, [items, listMeta.pendingEmbeddings]);

  return (
    <>
      <ContentLayout
        context="nodes"
        title="Node library"
        description="Search, refine, and orchestrate narrative nodes across every connected world."
        stats={headerStats}
      >
        <Card skin="shadow" className="relative p-4">
          <NodesFilters
            q={q}
            slugQuery={slugQuery}
            sort={sort}
            order={order}
            status={status}
            statusOptions={STATUS_OPTIONS}
            loading={loading}
            authorId={authorId}
            authorQuery={authorQuery}
            userOptions={authorOptions}
            showUserOptions={showAuthorOptions}
            isDraftFilter={status === 'draft'}
            hasCustomStatus={status !== 'all'}
            onQueryChange={handleQueryChange}
            onSlugChange={handleSlugChange}
            onSortChange={handleSortChange}
            onOrderChange={handleOrderChange}
            onStatusChange={applyStatus}
            onAuthorChange={handleAuthorChange}
            onAuthorFocus={handleAuthorFocus}
            onAuthorSelect={handleAuthorSelect}
            onAuthorClear={handleAuthorClear}
            onCreateNode={handleCreateNode}
            onImportExport={handleImportExport}
            onAnnounce={handleAnnounce}
          />

          <NodesBulkActions
            selectedCount={selectedCount}
            onPublish={handleBulkPublish}
            onUnpublish={handleBulkUnpublish}
            onSchedulePublish={handleBulkSchedulePublish}
            onScheduleUnpublish={handleBulkScheduleUnpublish}
            onArchive={handleBulkArchive}
            onDelete={handleBulkDelete}
          />

          {error && (
            <div className="mt-3 rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100">
              {error}
            </div>
          )}

          {embeddingWarningMessage && (
            <div className="mt-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-400/50 dark:bg-amber-950/30 dark:text-amber-200">
              {embeddingWarningMessage}
            </div>
          )}

          <NodesTable
            items={items}
            loading={loading}
            columns={columnVisibility}
            selected={selected}
            openMenuRow={openMenuRow}
            renderEmbeddingBadge={renderEmbeddingBadge}
            onToggleRow={handleToggleRow}
            onToggleAll={handleToggleAll}
            onCopyLink={handleCopyLink}
            onRestore={handleRestore}
            onView={handleView}
            onEdit={handleEdit}
            onDelete={handleDeleteRow}
            onOpenMenu={setOpenMenuRow}
            columnsCount={columnsCount}
          />

          <TablePagination
            page={page}
            pageSize={pageSize}
            currentCount={items.length}
            hasNext={hasNext}
            totalItems={listMeta.total ?? undefined}
            onPageChange={setPage}
            onPageSizeChange={(nextSize) => {
              setPageSize(nextSize);
              setPage(1);
            }}
          />
        </Card>
      </ContentLayout>

      {confirmationElement}
      {promptElement}
    </>
  );
}

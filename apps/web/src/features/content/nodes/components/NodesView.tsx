import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { ContentLayout } from '@shared/layouts/content';
import { Badge, Card, TablePagination, useToast } from '@ui';
import type { PageHeroMetric } from '@ui/patterns/PageHero';
import { usePaginatedQuery } from '@shared/hooks/usePaginatedQuery';
import { useConfirmDialog } from '@shared/hooks/useConfirmDialog';
import { usePromptDialog } from '@shared/hooks/usePromptDialog';
import { extractErrorMessage } from '@shared/utils/errors';
import { translate } from '@shared/i18n/locale';
import {
  fetchNodesList,
  restoreNode,
  deleteNode,
  bulkUpdateNodesStatus,
  fetchNodeAuthor,
  updateNodeTags,
} from '@shared/api/nodes';
import { DEV_BLOG_TAG, DEV_BLOG_HOME_TAG } from '@shared/types/nodes';
import type {
  EmbeddingStatus,
  NodeItem,
  NodeLifecycleStatus,
  NodeStatusFilter,
  NodeSortKey,
  NodeSortOrder,
  NodeUserOption,
  NodesListMeta,
  NodesListResult,
} from '@shared/types/nodes';

import { NodesFilters } from './NodesFilters';
import { NodesBulkActions } from './NodesBulkActions';
import { NodesTable } from './NodesTable';
import { useAuthorSearch } from '../hooks/useAuthorSearch';

const STATUS_OPTIONS: Array<{ value: NodeStatusFilter; label: string }> = [
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

const TOAST_COPY = {
  linkCopied: { en: 'Node link copied to clipboard', ru: 'РЎСЃС‹Р»РєР° РЅР° РЅРѕРґСѓ СЃРєРѕРїРёСЂРѕРІР°РЅР° РІ Р±СѓС„РµСЂ РѕР±РјРµРЅР°' },
  restoreSuccess: { en: 'Node restored', ru: 'РќРѕРґР° РІРѕСЃСЃС‚Р°РЅРѕРІР»РµРЅР°' },
  restoreError: { en: 'Failed to restore node', ru: 'РќРµ СѓРґР°Р»РѕСЃСЊ РІРѕСЃСЃС‚Р°РЅРѕРІРёС‚СЊ РЅРѕРґСѓ' },
  deleteSuccess: { en: 'Node deleted', ru: 'РќРѕРґР° СѓРґР°Р»РµРЅР°' },
  deleteError: { en: 'Failed to delete node', ru: 'РќРµ СѓРґР°Р»РѕСЃСЊ СѓРґР°Р»РёС‚СЊ РЅРѕРґСѓ' },
  bulkPublish: { en: 'Selected nodes marked as published', ru: 'Р’С‹Р±СЂР°РЅРЅС‹Рµ РЅРѕРґС‹ РѕРїСѓР±Р»РёРєРѕРІР°РЅС‹' },
  bulkDraft: { en: 'Selected nodes moved to drafts', ru: 'Р’С‹Р±СЂР°РЅРЅС‹Рµ РЅРѕРґС‹ РїРµСЂРµРЅРµСЃРµРЅС‹ РІ С‡РµСЂРЅРѕРІРёРєРё' },
  bulkSchedulePublish: { en: 'Publish schedule updated', ru: 'Р—Р°РїР»Р°РЅРёСЂРѕРІР°РЅР° РїСѓР±Р»РёРєР°С†РёСЏ' },
  bulkScheduleUnpublish: { en: 'Unpublish schedule updated', ru: 'Р—Р°РїР»Р°РЅРёСЂРѕРІР°РЅРѕ СЃРЅСЏС‚РёРµ СЃ РїСѓР±Р»РёРєР°С†РёРё' },
  bulkArchive: { en: 'Selected nodes archived', ru: 'Р’С‹Р±СЂР°РЅРЅС‹Рµ РЅРѕРґС‹ Р°СЂС…РёРІРёСЂРѕРІР°РЅС‹' },
  bulkDeleteSuccess: { en: 'Selected nodes deleted', ru: 'Р’С‹Р±СЂР°РЅРЅС‹Рµ РЅРѕРґС‹ СѓРґР°Р»РµРЅС‹' },
  bulkError: { en: 'Bulk action failed', ru: 'РќРµ СѓРґР°Р»РѕСЃСЊ РІС‹РїРѕР»РЅРёС‚СЊ РјР°СЃСЃРѕРІРѕРµ РґРµР№СЃС‚РІРёРµ' },
};

const HOMEPAGE_MESSAGES = {
  addSuccess: { en: 'Post will appear on the homepage', ru: 'РџРѕСЃС‚ РїРѕСЏРІРёС‚СЃСЏ РЅР° РіР»Р°РІРЅРѕР№' },
  removeSuccess: { en: 'Post removed from the homepage', ru: 'РџРѕСЃС‚ СЃРЅСЏС‚ СЃ РіР»Р°РІРЅРѕР№' },
  error: { en: 'Failed to update homepage flag', ru: 'РќРµ СѓРґР°Р»РѕСЃСЊ РѕР±РЅРѕРІРёС‚СЊ С„Р»Р°Рі РіР»Р°РІРЅРѕР№' },
};




function isUUIDLike(value: string | null | undefined): boolean {
  if (!value) return false;
  return /^(?:[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$/i.test(value);
}

export function ContentNodesList(): React.ReactElement {
  const navigate = useNavigate();
  const location = useLocation();
  const { pushToast } = useToast();
  const { confirm, confirmationElement } = useConfirmDialog();
  const { prompt, promptElement } = usePromptDialog();
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

  const [q, setQ] = React.useState('');
  const [slugQuery, setSlugQuery] = React.useState('');
  const [status, setStatus] = React.useState<NodeStatusFilter>('all');
  const [sort, setSort] = React.useState<NodeSortKey>('updated_at');
  const [order, setOrder] = React.useState<NodeSortOrder>('desc');
  const [devBlogOnly, setDevBlogOnly] = React.useState(false);
  const [openMenuRow, setOpenMenuRow] = React.useState<string | null>(null);
  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [homepageUpdating, setHomepageUpdating] = React.useState<Set<string>>(new Set());
  const columnVisibility = React.useMemo(
    () => ({ slug: true, author: true, status: true, updated: true, embedding: true, homepage: devBlogOnly }),
    [devBlogOnly],
  );
  const [listMeta, setListMeta] = React.useState<NodesListMeta>({
    total: null,
    published: null,
    drafts: null,
    pendingEmbeddings: null,
  });

  const enrichAuthorNames = React.useCallback(
    async (list: NodeItem[], signal?: AbortSignal): Promise<NodeItem[]> => {
      if (!list.length) return list;
      try {
        const needLookup = Array.from(
          new Set(
            list
              .filter(
                (item) =>
                  item.author_id &&
                  (!item.author_name || item.author_name === item.author_id || isUUIDLike(item.author_name)),
              )
              .map((item) => String(item.author_id)),
          ),
        );
        if (!needLookup.length) {
          return list;
        }
        const cache = authorLookupCacheRef.current;
        const missing = needLookup.filter((id) => !cache.has(id));
        if (missing.length) {
          await Promise.all(
            missing.map(async (id) => {
              try {
                const author = await fetchNodeAuthor(id, { signal });
                cache.set(id, author?.username ?? null);
              } catch (error) {
                console.error('Failed to resolve author info', id, error);
                cache.set(id, null);
              }
            }),
          );
        }
        return list.map((item) => {
          if (!item.author_id || (item.author_name && item.author_name !== item.author_id && !isUUIDLike(item.author_name))) {
            return item;
          }
          const cached = cache.get(String(item.author_id));
          if (cached) {
            return { ...item, author_name: cached };
          }
          return item;
        });
      } catch (error) {
        console.error('Failed to enrich author names', error);
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
  } = usePaginatedQuery<NodeItem, NodesListResult>({
    initialPageSize: 20,
    dependencies: [q, slugQuery, status, sort, order, authorId, devBlogOnly, enrichAuthorNames],
    debounceMs: 250,
    fetcher: async ({ page: currentPage, pageSize: size, signal }) => {
      const result = await fetchNodesList({
        q,
        slug: slugQuery,
        status,
        tag: devBlogOnly ? DEV_BLOG_TAG : undefined,
        authorId,
        sort,
        order,
        limit: size,
        offset: (currentPage - 1) * size,
        signal,
      });
      const enriched = await enrichAuthorNames(result.items, signal);
      return { ...result, items: enriched };
    },
    mapResponse: (result) => {
      setListMeta(result.meta);
      return {
        items: result.items,
        hasNext: result.hasNext,
        total: result.meta.total ?? undefined,
      };
    },
    onError: (err) => extractErrorMessage(err, translate({ en: 'Failed to load nodes', ru: 'РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РЅРѕРґС‹' })),
  });

  React.useEffect(() => {
    const params = new URLSearchParams(location.search);
    const preset = params.get('status') as NodeStatusFilter | null;
    if (preset && preset !== status && STATUS_OPTIONS.some((option) => option.value === preset)) {
      setStatus(preset);
      setPage(1);
    }
  }, [location.search, setPage, status]);

  React.useEffect(() => {
    const params = new URLSearchParams(location.search);
    const active = params.get('tag') === DEV_BLOG_TAG;
    setDevBlogOnly((prev) => (prev !== active ? active : prev));
  }, [location.search]);

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
    (value: NodeSortKey) => {
      setSort(value);
      setPage(1);
    },
    [setPage],
  );

  const handleOrderChange = React.useCallback(
    (value: NodeSortOrder) => {
      setOrder(value);
      setPage(1);
    },
    [setPage],
  );

  const handleDevBlogToggle = React.useCallback(() => {
    const params = new URLSearchParams(location.search);
    const nextValue = params.get('tag') !== DEV_BLOG_TAG;
    if (nextValue) {
      params.set('tag', DEV_BLOG_TAG);
    } else {
      params.delete('tag');
    }
    setDevBlogOnly(nextValue);
    setPage(1);
    const query = params.toString();
    const nextSearch = query ? `?${query}` : '';
    navigate({ pathname: location.pathname, search: nextSearch }, { replace: true });
  }, [location.pathname, location.search, navigate, setPage]);

  const handleHomepageToggle = React.useCallback(
    async (row: NodeItem, next: boolean) => {
      const nodeId = row.id;
      if (!nodeId) {
        return;
      }
      setHomepageUpdating((prev) => {
        const nextSet = new Set(prev);
        nextSet.add(nodeId);
        return nextSet;
      });
      try {
        await updateNodeTags(nodeId, [DEV_BLOG_HOME_TAG], next ? 'add' : 'remove');
        setItems((prev) =>
          prev.map((item) => (item.id === nodeId ? { ...item, showOnHome: next } : item)),
        );
        pushToast({ intent: 'success', description: translate(next ? HOMEPAGE_MESSAGES.addSuccess : HOMEPAGE_MESSAGES.removeSuccess) });
      } catch (err) {
        const message = extractErrorMessage(err, translate(HOMEPAGE_MESSAGES.error));
        setError(message);
        pushToast({ intent: 'error', description: message });
      } finally {
        setHomepageUpdating((prev) => {
          const nextSet = new Set(prev);
          nextSet.delete(nodeId);
          return nextSet;
        });
      }
    },
    [pushToast, setError, setHomepageUpdating, setItems],
  );

  const applyStatus = React.useCallback(
    (nextStatus: NodeStatusFilter) => {
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
    (option: NodeUserOption) => {
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
        await restoreNode(row.id);
        await refresh();
        pushToast({ intent: 'success', description: translate(TOAST_COPY.restoreSuccess) });
      } catch (err) {
        const message = extractErrorMessage(err, translate(TOAST_COPY.restoreError));
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

  const handleEngagement = React.useCallback(
    (row: NodeItem) => {
      closeMenu();
      navigate(`/admin/nodes/${encodeURIComponent(row.id)}`);
    },
    [closeMenu, navigate],
  );

  const handleModeration = React.useCallback(
    (row: NodeItem) => {
      closeMenu();
      navigate(`/admin/nodes/${encodeURIComponent(row.id)}/moderation`);
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
        await deleteNode(row.id);
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

    type ToastMessage = { en: string; ru: string };

  const bulkAction = React.useCallback(
    async (
      status: NodeLifecycleStatus,
      { publish_at, unpublish_at }: { publish_at?: string; unpublish_at?: string } = {},
      successMessage: ToastMessage,
    ) => {
      const ids = Array.from(selected);
      if (!ids.length) return false;
      try {
        await bulkUpdateNodesStatus({ ids, status, publish_at, unpublish_at });
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

  const handleBulkPublish = React.useCallback(
    async () => {
      await bulkAction('published', {}, TOAST_COPY.bulkPublish);
    },
    [bulkAction],
  );

  const handleBulkUnpublish = React.useCallback(
    async () => {
      await bulkAction('draft', {}, TOAST_COPY.bulkDraft);
    },
    [bulkAction],
  );

  const handleBulkSchedulePublish = React.useCallback(
    async () => {
      const value = await prompt({
        title: 'Schedule publish',
        description: 'Set publish time (YYYY-MM-DDTHH:mm)',
        placeholder: '2025-10-02T10:00',
        submitLabel: 'Schedule',
        cancelLabel: 'Cancel',
      });
      if (!value) return;
      await bulkAction('scheduled', { publish_at: value }, TOAST_COPY.bulkSchedulePublish);
    },
    [bulkAction, prompt],
  );

  const handleBulkScheduleUnpublish = React.useCallback(
    async () => {
      const value = await prompt({
        title: 'Schedule unpublish',
        description: 'Set unpublish time (YYYY-MM-DDTHH:mm)',
        placeholder: '2025-10-02T18:00',
        submitLabel: 'Schedule',
        cancelLabel: 'Cancel',
      });
      if (!value) return;
      await bulkAction('scheduled_unpublish', { unpublish_at: value }, TOAST_COPY.bulkScheduleUnpublish);
    },
    [bulkAction, prompt],
  );

  const handleBulkArchive = React.useCallback(
    async () => {
      await bulkAction('archived', {}, TOAST_COPY.bulkArchive);
    },
    [bulkAction],
  );

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
        await deleteNode(id);
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
  const handleImportExport = React.useCallback(() => navigate('/tools/import-export?scope=nodes'), [navigate]);
  const handleAnnounce = React.useCallback(() => navigate('/notifications?compose=nodes'), [navigate]);

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
  const bulkActions = (
    <NodesBulkActions
      selectedCount={selectedCount}
      onPublish={handleBulkPublish}
      onUnpublish={handleBulkUnpublish}
      onSchedulePublish={handleBulkSchedulePublish}
      onScheduleUnpublish={handleBulkScheduleUnpublish}
      onArchive={handleBulkArchive}
      onDelete={handleBulkDelete}
    />
  );
  const columnsCount = React.useMemo(
    () =>
      1 +
      Number(columnVisibility.slug) +
      Number(columnVisibility.author) +
      Number(columnVisibility.status) +
      Number(columnVisibility.embedding) +
      (columnVisibility.homepage ? 1 : 0) +
      Number(columnVisibility.updated) +
      1,
    [columnVisibility],
  );

  const headerMetrics = React.useMemo<PageHeroMetric[]>(
    () => [
      {
        id: 'nodes-total',
        label: 'Nodes',
        value: listMeta.total != null ? listMeta.total.toLocaleString('ru-RU') : 'N/A',
      },
      {
        id: 'nodes-published',
        label: 'Published',
        value: listMeta.published != null ? listMeta.published.toLocaleString('ru-RU') : 'N/A',
      },
      {
        id: 'nodes-drafts',
        label: 'Drafts',
        value: listMeta.drafts != null ? listMeta.drafts.toLocaleString('ru-RU') : 'N/A',
      },
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

  const layoutTitle = devBlogOnly ? 'Dev blog library' : 'Node library';
  const layoutDescription = devBlogOnly
    ? 'Plan, publish, and spotlight dev blog updates for players and partners.'
    : 'Search, refine, and orchestrate narrative nodes across every connected world.';

  return (
    <>
      <ContentLayout
        context="nodes"
        title={layoutTitle}
        description={layoutDescription}
        metrics={headerMetrics}
      >
        <Card skin="shadow" padding="lg" className="relative space-y-6 overflow-visible">
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
            devBlogOnly={devBlogOnly}
            onDevBlogToggle={handleDevBlogToggle}
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

          {error && (
            <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100">
              {error}
            </div>
          )}

          {embeddingWarningMessage && (
            <div className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-400/50 dark:bg-amber-950/30 dark:text-amber-200">
              {embeddingWarningMessage}
            </div>
          )}

          <NodesTable
            items={items}
            loading={loading}
            columns={columnVisibility}
            showHomepageToggle={devBlogOnly}
            onToggleHomepage={handleHomepageToggle}
            homepageUpdating={homepageUpdating}
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
            onEngagement={handleEngagement}
            onModeration={handleModeration}
            onOpenMenu={setOpenMenuRow}
            columnsCount={columnsCount}
            bulkActions={bulkActions}
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

export default ContentNodesList;


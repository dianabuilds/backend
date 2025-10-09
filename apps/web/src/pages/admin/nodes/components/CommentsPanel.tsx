import React from 'react';

import { Badge, Button, Card, Checkbox, Input, Skeleton, Tabs, useToast } from '@ui';

import { useConfirmDialog } from '@shared/hooks/useConfirmDialog';
import { extractErrorMessage } from '@shared/utils/errors';
import {
  deleteAdminComment,
  fetchAdminNodeComments,
  updateAdminCommentStatus,
} from '../api';
import type {
  AdminNodeComment,
  AdminNodeCommentsQuery,
  AdminNodeEngagementCommentSummary,
} from '../types';

type CommentsPanelProps = {
  nodeId: string;
  commentSummary: AdminNodeEngagementCommentSummary | null | undefined;
  onChange?: () => void;
};

type OrderValue = 'asc' | 'desc';
type CommentAction = string | null;

type ActiveFilterChip = {
  key: string;
  label: string;
  onRemove: () => void;
};

type FilterChipProps = Omit<ActiveFilterChip, 'key'>;

const COMMENT_STATUS_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'pending', label: 'Pending' },
  { value: 'published', label: 'Published' },
  { value: 'hidden', label: 'Hidden' },
  { value: 'deleted', label: 'Deleted' },
  { value: 'blocked', label: 'Blocked' },
];

const STATUS_BADGE_THEME: Record<string, { color: 'neutral' | 'info' | 'success' | 'warning' | 'error'; label: string }> = {
  pending: { color: 'warning', label: 'Pending' },
  published: { color: 'success', label: 'Published' },
  hidden: { color: 'neutral', label: 'Hidden' },
  deleted: { color: 'error', label: 'Deleted' },
  blocked: { color: 'error', label: 'Blocked' },
};

const COMMENT_LIMIT = 20;

function formatNumber(value: number | null | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0';
  return value.toLocaleString();
}

function FilterChip({ label, onRemove }: FilterChipProps) {
  return (
    <button
      type="button"
      onClick={onRemove}
      className="group inline-flex items-center gap-1 rounded-full border border-neutral-300 px-3 py-1 text-xs font-medium text-neutral-600 transition hover:border-neutral-400 hover:text-neutral-800 dark:border-dark-500 dark:text-dark-100 dark:hover:border-dark-300 dark:hover:text-white"
    >
      <span>{label}</span>
      <span className="text-base leading-none" aria-hidden>
        ?
      </span>
      <span className="sr-only">Remove filter {label}</span>
    </button>
  );
}

function CommentsSkeleton() {
  return (
    <div className="space-y-4">
      {[0, 1, 2].map((key) => (
        <div
          key={key}
          className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm dark:border-dark-500 dark:bg-dark-700"
        >
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <Skeleton className="h-4 w-28" rounded />
              <Skeleton className="h-4 w-16" rounded />
            </div>
            <Skeleton className="h-4 w-full" rounded />
            <Skeleton className="h-4 w-3/4" rounded />
          </div>
        </div>
      ))}
    </div>
  );
}

export function CommentsPanel({ nodeId, commentSummary, onChange }: CommentsPanelProps) {
  const { pushToast } = useToast();
  const { confirm, confirmationElement } = useConfirmDialog();

  const [view, setView] = React.useState<'tree' | 'list'>('tree');
  const [filtersOpen, setFiltersOpen] = React.useState(false);
  const [selectedStatuses, setSelectedStatuses] = React.useState<string[]>([]);
  const [authorId, setAuthorId] = React.useState('');
  const [search, setSearch] = React.useState('');
  const [createdFrom, setCreatedFrom] = React.useState('');
  const [createdTo, setCreatedTo] = React.useState('');
  const [includeDeleted, setIncludeDeleted] = React.useState(true);
  const [order, setOrder] = React.useState<OrderValue>('desc');

  const [items, setItems] = React.useState<AdminNodeComment[]>([]);
  const [summary, setSummary] = React.useState(commentSummary ?? null);
  const [hasMore, setHasMore] = React.useState<boolean>(false);
  const [offset, setOffset] = React.useState<number>(0);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [loadingMore, setLoadingMore] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);
  const [pendingAction, setPendingAction] = React.useState<CommentAction>(null);

  const buildQuery = React.useCallback(
    (override: Partial<AdminNodeCommentsQuery> = {}): AdminNodeCommentsQuery => {
      const normalizedView: AdminNodeCommentsQuery['view'] = view === 'tree' ? 'all' : 'all';
      const base: AdminNodeCommentsQuery = {
        view: normalizedView,
        order,
        includeDeleted,
        limit: COMMENT_LIMIT,
        ...override,
      };

      if (selectedStatuses.length) base.statuses = selectedStatuses;
      const trimmedAuthor = authorId.trim();
      if (trimmedAuthor) base.authorId = trimmedAuthor;
      const trimmedSearch = search.trim();
      if (trimmedSearch) base.search = trimmedSearch;
      if (createdFrom) base.createdFrom = createdFrom;
      if (createdTo) base.createdTo = createdTo;

      return base;
    },
    [authorId, createdFrom, createdTo, includeDeleted, order, search, selectedStatuses, view],
  );

  const loadComments = React.useCallback(
    async (nextOffset = 0, append = false) => {
      if (!nodeId) return;

      const request = buildQuery({ offset: nextOffset });
      if (append) setLoadingMore(true);
      else setLoading(true);

      try {
        const data = await fetchAdminNodeComments(nodeId, request);
        setSummary(data.summary);
        setHasMore(data.has_more);

        if (append) {
          setItems((prev) => [...prev, ...data.items]);
          setOffset(nextOffset + data.items.length);
        } else {
          setItems(data.items);
          setOffset(data.items.length);
        }
        setError(null);
      } catch (err) {
        if (!append) setItems([]);
        setError(extractErrorMessage(err));
      } finally {
        if (append) setLoadingMore(false);
        else setLoading(false);
      }
    },
    [buildQuery, nodeId],
  );

  React.useEffect(() => {
    setSummary(commentSummary ?? null);
  }, [commentSummary]);

  React.useEffect(() => {
    loadComments(0, false);
  }, [loadComments, nodeId, view]);

  const handleToggleStatusFilter = React.useCallback((value: string) => {
    setSelectedStatuses((prev) => {
      if (prev.includes(value)) return prev.filter((item) => item !== value);
      return [...prev, value];
    });
  }, []);

  const handleClearFilters = React.useCallback(() => {
    setSelectedStatuses([]);
    setAuthorId('');
    setSearch('');
    setCreatedFrom('');
    setCreatedTo('');
    setIncludeDeleted(true);
    setOrder('desc');
  }, []);

  const handleRefresh = React.useCallback(() => {
    loadComments(0, false);
  }, [loadComments]);

  const handleLoadMore = React.useCallback(() => {
    loadComments(offset, true);
  }, [loadComments, offset]);

  const activeFilters: ActiveFilterChip[] = [];
  selectedStatuses.forEach((status) => {
    const label = COMMENT_STATUS_OPTIONS.find((option) => option.value === status)?.label ?? status;
    activeFilters.push({
      key: `status:${status}`,
      label: `Status: ${label}`,
      onRemove: () => handleToggleStatusFilter(status),
    });
  });

  const trimmedAuthor = authorId.trim();
  if (trimmedAuthor) {
    activeFilters.push({
      key: 'author',
      label: `Author: ${trimmedAuthor}`,
      onRemove: () => setAuthorId(''),
    });
  }

  const trimmedSearch = search.trim();
  if (trimmedSearch) {
    activeFilters.push({
      key: 'search',
      label: `Search: "${trimmedSearch}"`,
      onRemove: () => setSearch(''),
    });
  }

  if (createdFrom) {
    activeFilters.push({
      key: 'createdFrom',
      label: `From: ${createdFrom}`,
      onRemove: () => setCreatedFrom(''),
    });
  }

  if (createdTo) {
    activeFilters.push({
      key: 'createdTo',
      label: `To: ${createdTo}`,
      onRemove: () => setCreatedTo(''),
    });
  }

  if (!includeDeleted) {
    activeFilters.push({
      key: 'includeDeleted',
      label: 'Exclude deleted',
      onRemove: () => setIncludeDeleted(true),
    });
  }

  if (order === 'asc') {
    activeFilters.push({
      key: 'order',
      label: 'Oldest first',
      onRemove: () => setOrder('desc'),
    });
  }

  const filterCount = activeFilters.length;
  const tabItems = React.useMemo(
    () => [
      { key: 'tree', label: <span data-testid="comments-view-tree">Tree view</span> },
      { key: 'list', label: <span data-testid="comments-view-list">List view</span> },
    ],
    [],
  );

  const handleChangeStatus = React.useCallback(
    async (comment: AdminNodeComment, nextStatus: string) => {
      const stateKey = `${comment.id}:status`;
      setPendingAction(stateKey);
      try {
        await updateAdminCommentStatus(comment.id, { status: nextStatus });
        pushToast({
          intent: 'success',
          description: `Comment #${comment.id} set to ${nextStatus}.`,
        });
        loadComments(0, false);
        onChange?.();
      } catch (err) {
        pushToast({ intent: 'error', description: extractErrorMessage(err) });
      } finally {
        setPendingAction(null);
      }
    },
    [loadComments, onChange, pushToast],
  );

  const handleDelete = React.useCallback(
    async (comment: AdminNodeComment) => {
      const confirmed = await confirm({
        title: 'Delete comment?',
        description: 'The comment will be removed for everyone. Continue?',
        confirmLabel: 'Delete',
        cancelLabel: 'Cancel',
      });
      if (!confirmed) return;

      setPendingAction(`${comment.id}:delete`);
      try {
        await deleteAdminComment(comment.id, { reason: 'admin_action' });
        pushToast({ intent: 'success', description: `Comment #${comment.id} deleted.` });
        loadComments(0, false);
        onChange?.();
      } catch (err) {
        pushToast({ intent: 'error', description: extractErrorMessage(err) });
      } finally {
        setPendingAction(null);
      }
    },
    [confirm, loadComments, onChange, pushToast],
  );

  const renderComment = React.useCallback(
    (comment: AdminNodeComment) => {
      const isPending = pendingAction === `${comment.id}:status` || pendingAction === `${comment.id}:delete`;
      const statusTone = STATUS_BADGE_THEME[comment.status] ?? { color: 'neutral', label: comment.status };
      const indent = view === 'tree' ? Math.min(comment.depth ?? 0, 5) * 24 : 0;

      return (
        <li
          key={comment.id}
          className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm dark:border-dark-500 dark:bg-dark-700"
          data-testid={`comment-item-${comment.id}`}
        >
          <div className="flex flex-col gap-3" style={indent ? { marginLeft: `${indent}px` } : undefined}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 space-y-1 text-sm text-neutral-700 dark:text-neutral-200">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-medium text-neutral-900 dark:text-neutral-100">
                    {comment.author_id || 'Unknown author'}
                  </span>
                  <Badge color={statusTone.color} variant="soft">
                    {statusTone.label}
                  </Badge>
                </div>
                <p className="whitespace-pre-wrap text-neutral-800 dark:text-neutral-100">{comment.content}</p>
              </div>
              <div className="text-right text-xs text-neutral-500 dark:text-neutral-300">
                <div>ID: {comment.id}</div>
                <div>Created: {comment.created_at ?? 'N/A'}</div>
                {comment.updated_at ? <div>Updated: {comment.updated_at}</div> : null}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs text-neutral-600 dark:text-neutral-300">
              <Button
                size="xs"
                variant="ghost"
                disabled={isPending || comment.status === 'published'}
                onClick={() => handleChangeStatus(comment, 'published')}
              >
                Publish
              </Button>
              <Button
                size="xs"
                variant="ghost"
                disabled={isPending || comment.status === 'hidden'}
                onClick={() => handleChangeStatus(comment, 'hidden')}
              >
                Hide
              </Button>
              <Button
                size="xs"
                variant="ghost"
                color="error"
                disabled={isPending}
                onClick={() => handleDelete(comment)}
              >
                Delete
              </Button>
              {comment.parent_comment_id && (
                <span className="ml-2 text-neutral-500">Parent #{comment.parent_comment_id}</span>
              )}
            </div>
          </div>
        </li>
      );
    },
    [handleChangeStatus, handleDelete, pendingAction, view],
  );

  const showInitialLoading = loading && !items.length;

  return (
    <>
      <Card
        id="comments"
        className="space-y-6 p-6 rounded-3xl border border-sky-100/80 bg-gradient-to-br from-sky-50/70 via-white to-white dark:border-dark-600 dark:from-dark-700/40 dark:via-dark-800 dark:to-dark-900"
        data-testid="admin-comments-panel"
        data-analytics="admin.comments.panel"
      >
        <div className="space-y-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-1">
              <h2 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">Comments moderation</h2>
              <p className="text-sm text-neutral-600 dark:text-neutral-300">
                Filter and moderate comments. Tree view preserves hierarchy; list view is flattened.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Tabs items={tabItems} value={view} onChange={(key) => setView(key as 'tree' | 'list')} />
              <Button
                size="sm"
                variant="outlined"
                color="neutral"
                onClick={handleRefresh}
                disabled={loading}
                data-testid="comments-refresh"
                data-analytics="admin.comments.refresh"
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Button
                size="sm"
                variant="outlined"
                color="neutral"
                onClick={() => setFiltersOpen((prev) => !prev)}
              >
                Filters{filterCount ? ` (${filterCount})` : ''}
              </Button>
              {activeFilters.map(({ key: chipKey, ...chip }) => (
                <FilterChip key={chipKey} {...chip} />
              ))}
              {filterCount ? (
                <Button size="xs" variant="ghost" onClick={handleClearFilters} data-testid="comments-filters-clear">
                  Clear all
                </Button>
              ) : null}
            </div>

            {filtersOpen ? (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <div className="md:col-span-2 xl:col-span-4 space-y-2">
                  <span className="text-xs font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400">
                    Statuses
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {COMMENT_STATUS_OPTIONS.map((option) => {
                      const active = selectedStatuses.includes(option.value);
                      return (
                        <button
                          key={option.value}
                          type="button"
                          className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                            active
                              ? 'border-primary-400 bg-primary-50 text-primary-700 dark:border-primary-500/60 dark:bg-primary-900/40 dark:text-primary-200'
                              : 'border-neutral-300 text-neutral-600 hover:bg-neutral-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-600'
                          }`}
                          onClick={() => handleToggleStatusFilter(option.value)}
                        >
                          {option.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <Input label="Author ID" value={authorId} onChange={(e) => setAuthorId(e.target.value)} placeholder="uuid" />
                <Input label="Search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Contains text" />
                <Input label="Created from" type="date" value={createdFrom} onChange={(e) => setCreatedFrom(e.target.value)} />
                <Input label="Created to" type="date" value={createdTo} onChange={(e) => setCreatedTo(e.target.value)} />

                <div className="flex items-center gap-2">
                  <Checkbox
                    id="includeDeleted"
                    checked={includeDeleted}
                    onChange={(e) => setIncludeDeleted(e.currentTarget.checked)}
                  />
                  <label htmlFor="includeDeleted" className="text-sm font-medium text-neutral-700 dark:text-neutral-200">
                    Include deleted comments
                  </label>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-sm text-neutral-600 dark:text-neutral-300">Order</span>
                  <select
                    className="form-select h-9 rounded-md border border-neutral-300 bg-white px-2 text-sm dark:border-dark-500 dark:bg-dark-700"
                    value={order}
                    onChange={(e) => setOrder(e.target.value as OrderValue)}
                  >
                    <option value="desc">Newest first</option>
                    <option value="asc">Oldest first</option>
                  </select>
                </div>
              </div>
            ) : null}
          </div>

          {summary ? (
            <div className="flex flex-wrap items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300">
              <span>Total: {formatNumber(summary?.total ?? 0)}</span>
              {Object.entries(summary.by_status ?? {}).map(([key, count]) => (
                <Badge key={key} color={(STATUS_BADGE_THEME[key]?.color ?? 'neutral') as any} variant="soft">
                  {STATUS_BADGE_THEME[key]?.label ?? key}: {formatNumber(typeof count === 'number' ? count : 0)}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>

        {commentSummary?.locked ? (
          <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-700 dark:border-amber-500/60 dark:bg-amber-900/30 dark:text-amber-200">
            Comments locked by {commentSummary.locked_by || 'moderator'}{' '}
            {commentSummary.locked_at ? `at ${commentSummary.locked_at}` : ''}.
          </div>
        ) : null}

        {commentSummary?.disabled ? (
          <div className="rounded-md border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-500/60 dark:bg-rose-900/30 dark:text-rose-200">
            Comments are disabled for this node. No new comments can be posted.
          </div>
        ) : null}

        {error ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700 dark:border-rose-500/60 dark:bg-rose-900/30 dark:text-rose-200">
            {error}
          </div>
        ) : null}

        <div className="space-y-4">
          {showInitialLoading ? (
            <CommentsSkeleton />
          ) : items.length === 0 ? (
            <Card className="border border-dashed border-neutral-300 bg-neutral-50 p-6 text-center text-sm text-neutral-500 dark:border-dark-500 dark:bg-dark-700/40 dark:text-dark-100">
              No comments match the current filters.
            </Card>
          ) : (
            <ul className="space-y-4" data-testid="comments-list">
              {items.map((comment) => renderComment(comment))}
            </ul>
          )}

          {hasMore ? (
            <div className="flex justify-center">
              <Button
                onClick={handleLoadMore}
                variant="outlined"
                color="neutral"
                disabled={loadingMore}
                data-testid="comments-load-more"
                data-analytics="admin.comments.loadMore"
              >
                {loadingMore ? 'Loading...' : 'Load more'}
              </Button>
            </div>
          ) : null}
        </div>
      </Card>

      {confirmationElement}
    </>
  );
}



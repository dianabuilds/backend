import React from 'react';

import { Badge, Button, Card, Checkbox, Input, Spinner, useToast } from '@ui';

import { useConfirmDialog } from '../../../../shared/hooks/useConfirmDialog';

import { extractErrorMessage } from '../../../../shared/utils/errors';

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

export function CommentsPanel({ nodeId, commentSummary, onChange }: CommentsPanelProps) {

  const { pushToast } = useToast();

  const { confirm, confirmationElement } = useConfirmDialog();

  const [view, setView] = React.useState<'tree' | 'list'>('tree');

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

      if (authorId.trim()) base.authorId = authorId.trim();

      if (search.trim()) base.search = search.trim();

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

    if (!hasMore || loadingMore) return;

    loadComments(offset, true);

  }, [hasMore, loadComments, loadingMore, offset]);

  const handleChangeStatus = React.useCallback(

    async (comment: AdminNodeComment, status: string) => {

      setPendingAction(`${comment.id}:status`);

      try {

        await updateAdminCommentStatus(comment.id, { status });

        pushToast({ intent: 'success', description: `Comment #${comment.id} marked as ${status}.` });

        await loadComments(0, false);

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

        description: 'The comment will be removed from public view. Hard delete is available later.',

        confirmLabel: 'Delete',

        cancelLabel: 'Cancel',

        destructive: true,

      });

      if (!confirmed) return;

      setPendingAction(`${comment.id}:delete`);

      try {

        await deleteAdminComment(comment.id, { reason: 'admin_action' });

        pushToast({ intent: 'success', description: `Comment #${comment.id} deleted.` });

        await loadComments(0, false);

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

        <li key={comment.id} className="rounded-lg border border-neutral-200 bg-white p-4 shadow-sm dark:border-dark-500 dark:bg-dark-700" data-testid={`comment-item-${comment.id}`}>

          <div className="flex flex-col gap-3" style={indent ? { marginLeft: `${indent}px` } : undefined}>

            <div className="flex items-start justify-between gap-3">

              <div className="flex-1 space-y-1 text-sm text-neutral-700 dark:text-neutral-200">

                <div className="flex flex-wrap items-center gap-2">

                  <span className="font-medium text-neutral-900 dark:text-neutral-100">{comment.author_id || 'Unknown author'}</span>

                  <Badge color={statusTone.color} variant="soft">{statusTone.label}</Badge>

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

  return (

    <>

      <Card className="space-y-6 p-6" data-testid="admin-comments-panel" data-analytics="admin.comments.panel">

        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">

          <div>

            <h2 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">Comments moderation</h2>

            <p className="text-sm text-neutral-600 dark:text-neutral-300">

              Filter and moderate comments. Tree view follows hierarchical depth; list view is flattened.

            </p>

          </div>

          <div className="flex items-center gap-2">

            <button

              type="button"

              className={`rounded-full px-4 py-1.5 text-xs font-medium ${

                view === 'tree'

                  ? 'bg-primary-600 text-white'

                  : 'bg-neutral-200 text-neutral-700 hover:bg-neutral-300 dark:bg-dark-600 dark:text-dark-50'

              }`}

              data-testid="comments-view-tree"

              data-analytics="admin.comments.view.tree"

              onClick={() => setView('tree')}

            >

              Tree view

            </button>

            <button

              type="button"

              className={`rounded-full px-4 py-1.5 text-xs font-medium ${

                view === 'list'

                  ? 'bg-primary-600 text-white'

                  : 'bg-neutral-200 text-neutral-700 hover:bg-neutral-300 dark:bg-dark-600 dark:text-dark-50'

              }`}

              data-testid="comments-view-list"

              data-analytics="admin.comments.view.list"

              onClick={() => setView('list')}

            >

              List view

            </button>

            <Button size="sm" variant="outlined" color="neutral" onClick={handleRefresh} disabled={loading} data-testid="comments-refresh" data-analytics="admin.comments.refresh">

              {loading ? 'Refreshing...' : 'Refresh'}

            </Button>

          </div>

        </div>

        {commentSummary?.locked && (

          <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-700 dark:border-amber-500/60 dark:bg-amber-900/30 dark:text-amber-200">

            Comments locked by {commentSummary.locked_by || 'moderator'} {commentSummary.locked_at ? `at ${commentSummary.locked_at}` : ''}.

          </div>

        )}

        {commentSummary?.disabled && (

          <div className="rounded-md border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-700 dark:border-rose-500/60 dark:bg-rose-900/30 dark:text-rose-200">

            Comments are disabled for this node. No new comments can be posted.

          </div>

        )}

        <div className="space-y-4">

          <div className="flex flex-wrap items-center gap-3">

            {COMMENT_STATUS_OPTIONS.map((option) => (

              <button

                key={option.value}

                type="button"

                className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${

                  selectedStatuses.includes(option.value)

                    ? 'border-primary-400 bg-primary-50 text-primary-700 dark:border-primary-500/60 dark:bg-primary-900/40 dark:text-primary-200'

                    : 'border-neutral-300 text-neutral-600 hover:bg-neutral-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-600'

                }`}

                onClick={() => handleToggleStatusFilter(option.value)}

              >

                {option.label}

              </button>

            ))}

            {selectedStatuses.length > 0 && (

              <button

                type="button"

                className="rounded-full border border-neutral-300 px-3 py-1.5 text-xs font-medium text-neutral-600 transition hover:bg-neutral-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-600"

                onClick={() => setSelectedStatuses([])}

              >

                Reset statuses

              </button>

            )}

          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

            <Input label="Author ID" value={authorId} onChange={(e) => setAuthorId(e.target.value)} placeholder="uuid" />

            <Input label="Search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Contains text" />

            <Input label="Created from" type="date" value={createdFrom} onChange={(e) => setCreatedFrom(e.target.value)} />

            <Input label="Created to" type="date" value={createdTo} onChange={(e) => setCreatedTo(e.target.value)} />

            <div className="flex items-center gap-2">

              <Checkbox id="includeDeleted" checked={includeDeleted} onChange={(e) => setIncludeDeleted(e.currentTarget.checked)} />

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

            <div>

              <Button size="sm" variant="ghost" onClick={handleClearFilters} data-testid="comments-filters-clear">

                Clear filters

              </Button>

            </div>

          </div>

        </div>

        {summary && (

          <div className="flex flex-wrap items-center gap-2 text-sm text-neutral-600 dark:text-neutral-300">

            <span>Total: {formatNumber(summary?.total ?? 0)}</span>

            {Object.entries(summary.by_status ?? {}).map(([key, count]) => (

              <Badge key={key} color={(STATUS_BADGE_THEME[key]?.color ?? 'neutral') as any} variant="soft">

                {STATUS_BADGE_THEME[key]?.label ?? key}: {formatNumber(typeof count === 'number' ? count : 0)}

              </Badge>

            ))}

          </div>

        )}

        {error && (

          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700 dark:border-rose-500/60 dark:bg-rose-900/30 dark:text-rose-200">

            {error}

          </div>

        )}

        <div className="space-y-4">

          {loading && !items.length ? (

            <div className="flex flex-col items-center gap-2 py-12 text-sm text-neutral-500 dark:text-neutral-300">

              <Spinner />

              <span>Loading comments...</span>

            </div>

          ) : items.length === 0 ? (

            <Card className="border border-dashed border-neutral-300 bg-neutral-50 p-6 text-center text-sm text-neutral-500 dark:border-dark-500 dark:bg-dark-700/40 dark:text-dark-100">

              No comments match the current filters.

            </Card>

          ) : (

            <ul className="space-y-4" data-testid="comments-list">

              {items.map((comment) => renderComment(comment))}

            </ul>

          )}

          {hasMore && (

            <div className="flex justify-center">

              <Button onClick={handleLoadMore} variant="outlined" color="neutral" disabled={loadingMore} data-testid="comments-load-more" data-analytics="admin.comments.loadMore">

                {loadingMore ? 'Loading...' : 'Load more'}

              </Button>

            </div>

          )}

        </div>

      </Card>

      {confirmationElement}

    </>

  );

}



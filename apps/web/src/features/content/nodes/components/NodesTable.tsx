import React from 'react';
import { createPortal } from 'react-dom';
import {
  EllipsisVerticalIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  LinkIcon,
  PresentationChartBarIcon,
  ChatBubbleLeftRightIcon,
} from '@heroicons/react/24/outline';

import { Badge, Spinner, Switch } from '@ui';
import { Table } from '@ui/table';
import { formatDateTime } from '@shared/utils/format';
import type { NodeItem, EmbeddingStatus } from '@shared/types/nodes';

const STATUS_LABELS: Record<string, { label: string; color: 'success' | 'warning' | 'info' | 'error' | 'neutral' }> = {
  published: { label: 'Published', color: 'success' },
  draft: { label: 'Draft', color: 'warning' },
  scheduled: { label: 'Scheduled', color: 'info' },
  scheduled_unpublish: { label: 'Will unpublish', color: 'info' },
  archived: { label: 'Archived', color: 'neutral' },
  deleted: { label: 'Deleted', color: 'error' },
};

type ColumnVisibility = {
  slug: boolean;
  author: boolean;
  status: boolean;
  updated: boolean;
  embedding: boolean;
  homepage?: boolean;
};

export type NodesTableProps = {
  items: NodeItem[];
  loading: boolean;
  columns: ColumnVisibility;
  selected: Set<string>;
  openMenuRow: string | null;
  renderEmbeddingBadge: (status?: EmbeddingStatus | null) => React.ReactNode;
  onModeration: (row: NodeItem) => void;
  onToggleRow: (id: string, checked: boolean) => void;
  onToggleAll: (checked: boolean) => void;
  onCopyLink: (row: NodeItem) => void;
  onRestore: (row: NodeItem) => void;
  onView: (row: NodeItem) => void;
  onEdit: (row: NodeItem) => void;
  onDelete: (row: NodeItem) => void;
  onEngagement: (row: NodeItem) => void;
  onOpenMenu: (rowId: string | null) => void;
  columnsCount: number;
  bulkActions?: React.ReactNode;
  showHomepageToggle?: boolean;
  onToggleHomepage?: (row: NodeItem, next: boolean) => void;
  homepageUpdating?: Set<string>;
};

function resolveStatusBadge(row: NodeItem): { label: string; color: 'success' | 'warning' | 'info' | 'error' | 'neutral' } | null {
  const normalized = (row.status ?? '').toLowerCase();
  if (normalized && STATUS_LABELS[normalized]) {
    return STATUS_LABELS[normalized];
  }

  const isPublished = normalized ? normalized === 'published' : row.is_public === true;
  return STATUS_LABELS[isPublished ? 'published' : 'draft'];
}

export function NodesTable({
  items,
  loading,
  columns,
  selected,
  openMenuRow,
  renderEmbeddingBadge,
  onModeration,
  onToggleRow,
  onToggleAll,
  onCopyLink,
  onRestore,
  onView,
  onEdit,
  onDelete,
  onEngagement,
  onOpenMenu,
  columnsCount,
  bulkActions,
  showHomepageToggle = false,
  onToggleHomepage,
  homepageUpdating,
}: NodesTableProps) {
  const selectAllRef = React.useRef<HTMLInputElement | null>(null);
  const menuRef = React.useRef<HTMLDivElement | null>(null);
  const menuTriggerRef = React.useRef<HTMLButtonElement | null>(null);
  const fallbackValue = '—';
  const allSelected = !loading && items.length > 0 && items.every((item) => selected.has(item.id));
  const [menuPosition, setMenuPosition] = React.useState<{ top: number; left: number; placement: 'bottom' | 'top' } | null>(null);
  const portalTarget = typeof document !== 'undefined' ? document.body : null;
  const showHomepageColumn = !!(showHomepageToggle && columns.homepage);
  const homepageLoadingSet = homepageUpdating ?? new Set<string>();

  React.useLayoutEffect(() => {
    if (typeof window === 'undefined') return;

    if (!openMenuRow) {
      setMenuPosition(null);
      menuTriggerRef.current = null;
      return;
    }

    let animationFrameId = 0;

    const updatePosition = () => {
      const element = menuRef.current;
      const trigger = menuTriggerRef.current;
      if (!element || !trigger) {
        animationFrameId = window.requestAnimationFrame(updatePosition);
        return;
      }

      const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
      const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
      const menuHeight = element.offsetHeight;
      const menuWidth = element.offsetWidth;
      const triggerRect = trigger.getBoundingClientRect();
      const spaceBelow = viewportHeight - triggerRect.bottom;
      const spaceAbove = triggerRect.top;

      let placement: 'bottom' | 'top' = 'bottom';
      if (menuHeight + 12 > spaceBelow && spaceAbove > spaceBelow) {
        placement = 'top';
      }

      const preferredTop = placement === 'top'
        ? triggerRect.top - menuHeight - 12
        : triggerRect.bottom + 12;
      const preferredLeft = triggerRect.right - menuWidth;

      const top = Math.min(Math.max(12, preferredTop), viewportHeight - menuHeight - 12);
      const left = Math.min(Math.max(12, preferredLeft), viewportWidth - menuWidth - 12);

      setMenuPosition((prev) => {
        if (prev && prev.top === top && prev.left === left && prev.placement === placement) {
          return prev;
        }
        return { top, left, placement };
      });
    };

    const schedule = () => {
      if (animationFrameId) {
        window.cancelAnimationFrame(animationFrameId);
      }
      animationFrameId = window.requestAnimationFrame(updatePosition);
    };

    schedule();
    window.addEventListener('resize', schedule);
    window.addEventListener('scroll', schedule, true);

    return () => {
      if (animationFrameId) {
        window.cancelAnimationFrame(animationFrameId);
      }
      window.removeEventListener('resize', schedule);
      window.removeEventListener('scroll', schedule, true);
    };
  }, [openMenuRow]);

  React.useEffect(() => {
    if (!selectAllRef.current) return;
    selectAllRef.current.indeterminate = selected.size > 0 && !allSelected;
  }, [allSelected, selected]);

  return (
    <div className="hide-scrollbar overflow-x-auto overflow-y-visible">
      <Table
        preset="surface"
        className="min-w-[960px] overflow-visible"
        hover
        zebra
        headerSticky
        actions={bulkActions}
      >
        <Table.Actions />
        <Table.THead>
          <Table.TR>
            <Table.TH className="w-12">
              <input
                ref={selectAllRef}
                type="checkbox"
                className="form-checkbox accent-primary-600 align-middle"
                aria-label="Select all nodes"
                checked={allSelected}
                onChange={(event) => onToggleAll(event.currentTarget.checked)}
              />
            </Table.TH>
            <Table.TH className="min-w-[200px]">Title</Table.TH>
            {columns.slug && <Table.TH>Slug</Table.TH>}
            {columns.author && <Table.TH>Author</Table.TH>}
            {columns.status && <Table.TH>Status</Table.TH>}
            {columns.embedding && <Table.TH>Embedding</Table.TH>}\n            {showHomepageColumn && <Table.TH>Homepage</Table.TH>}\n            {columns.updated && <Table.TH>Updated</Table.TH>}\n            <Table.TH className="w-28 text-right">Actions</Table.TH>
          </Table.TR>
        </Table.THead>
        <Table.TBody>
          {loading ? (
            <Table.Loading rows={4} colSpan={columnsCount} />
          ) : items.length === 0 ? (
            <Table.Empty colSpan={columnsCount} title="No nodes yet" description="Create or import content to see it listed here." />
          ) : (
            items.map((row) => {
              const statusBadge = resolveStatusBadge(row);
              const updated = formatDateTime(row.updated_at, { withSeconds: true, fallback: fallbackValue });
              const rowLabel = row.title || row.slug || row.id;

              return (
                <Table.TR key={row.id} className="border-0">
                  <Table.TD className="w-12">
                    <input
                      type="checkbox"
                      className="form-checkbox accent-primary-600 align-middle"
                      aria-label={`Select node ${rowLabel}`}
                      checked={selected.has(row.id)}
                      onChange={(event) => onToggleRow(row.id, event.currentTarget.checked)}
                    />
                  </Table.TD>
                  <Table.TD>
                    <span className="font-medium text-gray-900 dark:text-dark-50">{row.title || 'Untitled node'}</span>
                  </Table.TD>
                  {columns.slug && (
                    <Table.TD>
                      {row.slug ? (
                        <code className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-dark-700 dark:text-dark-200">{row.slug}</code>
                      ) : (
                        <span className="text-gray-400 dark:text-dark-300">{fallbackValue}</span>
                      )}
                    </Table.TD>
                  )}
                  {columns.author && (
                    <Table.TD className="text-gray-600 dark:text-dark-200">{row.author_name || fallbackValue}</Table.TD>
                  )}
                  {columns.status && (
                    <Table.TD>
                      {statusBadge ? (
                        <Badge color={statusBadge.color} variant="soft">{statusBadge.label}</Badge>
                      ) : (
                        <span className="text-gray-500">{fallbackValue}</span>
                      )}
                    </Table.TD>
                  )}
                  {columns.embedding && <Table.TD>{renderEmbeddingBadge(row.embedding_status)}</Table.TD>}
                  {showHomepageColumn && (
                    <Table.TD>
                      {row.isDevBlog ? (
                        <div className="flex items-center gap-2">
                          <Switch
                            checked={row.showOnHome === true}
                            onChange={(event) => onToggleHomepage?.(row, event.currentTarget.checked)}
                            disabled={!onToggleHomepage || homepageLoadingSet.has(row.id)}
                            aria-label={`Toggle homepage visibility for ${row.title || row.slug || row.id}`}
                          />
                          {homepageLoadingSet.has(row.id) && <Spinner size="sm" />}
                        </div>
                      ) : (
                        <span className="text-gray-400 dark:text-dark-300">—</span>
                      )}
                    </Table.TD>
                  )}
                  {columns.updated && (
                    <Table.TD className="text-gray-600 dark:text-dark-200">{updated}</Table.TD>
                  )}
                  <Table.TD>
                    <div
                      className="relative flex items-center justify-end"
                      role="presentation"
                      tabIndex={-1}
                      onClick={(event) => event.stopPropagation()}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') {
                          event.stopPropagation();
                        }
                      }}
                    >
                      <button
                        ref={(node) => {
                          if (openMenuRow === row.id) {
                            menuTriggerRef.current = node;
                          }
                        }}
                        type="button"
                        className="inline-flex h-8 w-8 items-center justify-center rounded hover:bg-gray-200/60 dark:hover:bg-dark-500"
                        onClick={(event) => {
                          event.stopPropagation();
                          onOpenMenu(openMenuRow === row.id ? null : row.id);
                        }}
                      >
                        <EllipsisVerticalIcon className="h-5 w-5 text-gray-500" />
                      </button>
                      {openMenuRow === row.id && portalTarget
                        ? createPortal(
                            <div
                              ref={menuRef}
                              className="fixed z-50 w-48 rounded-md border border-gray-200 bg-white shadow-lg dark:border-dark-500 dark:bg-dark-700"
                              style={{
                                top: menuPosition?.top ?? 0,
                                left: menuPosition?.left ?? 0,
                                visibility: menuPosition ? 'visible' : 'hidden',
                              }}
                            >
                              <button
                                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600 disabled:opacity-50"
                                onClick={() => onCopyLink(row)}
                                disabled={!row.slug}
                                type="button"
                              >
                                <LinkIcon className="h-4 w-4" /> Copy link
                              </button>
                              {row.status?.toLowerCase() === 'deleted' && (
                                <button
                                  type="button"
                                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-green-700 hover:bg-green-50 dark:text-green-300 dark:hover:bg-green-500/20"
                                  onClick={() => onRestore(row)}
                                >
                                  Restore
                                </button>
                              )}
                              <button
                                type="button"
                                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                                onClick={() => onView(row)}
                              >
                                <EyeIcon className="h-4 w-4" /> View
                              </button>
                              <button
                                type="button"
                                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                                onClick={() => onEngagement(row)}
                              >
                                <PresentationChartBarIcon className="h-4 w-4" /> Engagement
                              </button>
                              <button
                                type="button"
                                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                                onClick={() => onModeration(row)}
                              >
                                <ChatBubbleLeftRightIcon className="h-4 w-4" /> Moderation
                              </button>
                              <button
                                type="button"
                                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                                onClick={() => onEdit(row)}
                              >
                                <PencilIcon className="h-4 w-4" /> Edit
                              </button>
                              <button
                                type="button"
                                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:text-red-300 dark:hover:bg-red-500/20"
                                onClick={() => onDelete(row)}
                              >
                                <TrashIcon className="h-4 w-4" /> Delete
                              </button>
                            </div>,
                            portalTarget
                          )
                        : null}
                    </div>
                  </Table.TD>
                </Table.TR>
              );
            })
          )}
        </Table.TBody>
      </Table>
    </div>
  );
}














import React from 'react';
import {
  EllipsisVerticalIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  LinkIcon,
} from '@heroicons/react/24/outline';

import type { NodeItem, EmbeddingStatus } from '../types';

type ColumnVisibility = {
  slug: boolean;
  author: boolean;
  status: boolean;
  updated: boolean;
  embedding: boolean;
};

export type NodesTableProps = {
  items: NodeItem[];
  loading: boolean;
  columns: ColumnVisibility;
  selected: Set<string>;
  openMenuRow: string | null;
  renderEmbeddingBadge: (status?: EmbeddingStatus | null) => React.ReactNode;
  onToggleRow: (id: string, checked: boolean) => void;
  onToggleAll: (checked: boolean) => void;
  onCopyLink: (row: NodeItem) => void;
  onRestore: (row: NodeItem) => void;
  onView: (row: NodeItem) => void;
  onEdit: (row: NodeItem) => void;
  onDelete: (row: NodeItem) => void;
  onOpenMenu: (rowId: string | null) => void;
  columnsCount: number;
};

export function NodesTable({
  items,
  loading,
  columns,
  selected,
  openMenuRow,
  renderEmbeddingBadge,
  onToggleRow,
  onToggleAll,
  onCopyLink,
  onRestore,
  onView,
  onEdit,
  onDelete,
  onOpenMenu,
  columnsCount,
}: NodesTableProps) {
  return (
    <div className="mt-4 hide-scrollbar overflow-x-auto overflow-y-visible">
      <table className="min-w-[960px] w-full text-left">
        <thead>
          <tr className="bg-gray-200 text-gray-800 uppercase">
            <th className="py-2 px-3">
              <input
                type="checkbox"
                className="form-checkbox accent-primary-600 align-middle"
                checked={items.length > 0 && items.every((item) => selected.has(item.id))}
                onChange={(e) => onToggleAll(e.currentTarget.checked)}
              />
            </th>
            <th className="py-2 px-3">Title</th>
            {columns.slug && <th className="py-2 px-3">Slug</th>}
            {columns.author && <th className="py-2 px-3">Author</th>}
            {columns.status && <th className="py-2 px-3">Status</th>}
            {columns.embedding && <th className="py-2 px-3">Embedding</th>}
            {columns.updated && <th className="py-2 px-3">Updated</th>}
            <th className="py-2 px-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {loading && (
            <tr>
              <td className="py-3 px-3" colSpan={columnsCount}>
                Loading...
              </td>
            </tr>
          )}
          {!loading && items.length === 0 && (
            <tr>
              <td className="py-8 px-3 text-center text-sm text-gray-500" colSpan={columnsCount}>
                No nodes yet
              </td>
            </tr>
          )}
          {!loading &&
            items.map((row) => {
              const normalizedStatus = (row.status || '').toLowerCase();
              const isPublished = normalizedStatus ? normalizedStatus === 'published' : row.is_public ?? false;
              const updated = row.updated_at ? String(row.updated_at).slice(0, 19).replace('T', ' ') : '-';

              const renderStatus = () => {
                if (normalizedStatus === 'scheduled') return <span className="badge badge-info">Scheduled</span>;
                if (normalizedStatus === 'scheduled_unpublish') return <span className="badge badge-info">Will unpublish</span>;
                if (normalizedStatus === 'archived') return <span className="badge">Archived</span>;
                if (normalizedStatus === 'deleted') return <span className="badge badge-error">Deleted</span>;
                if (!normalizedStatus) {
                  return isPublished ? (
                    <span className="badge badge-success">Published</span>
                  ) : (
                    <span className="badge badge-warning">Draft</span>
                  );
                }
                if (!['scheduled', 'scheduled_unpublish', 'archived', 'deleted'].includes(normalizedStatus)) {
                  return normalizedStatus === 'published' ? (
                    <span className="badge badge-success">Published</span>
                  ) : (
                    <span className="badge badge-warning">Draft</span>
                  );
                }
                return null;
              };

              return (
                <tr key={row.id} className="border-b border-gray-200">
                  <td className="py-2 px-3">
                    <input
                      type="checkbox"
                      className="form-checkbox accent-primary-600 align-middle"
                      checked={selected.has(row.id)}
                      onChange={(e) => onToggleRow(row.id, e.currentTarget.checked)}
                    />
                  </td>
                  <td className="py-2 px-3">
                    <span className="font-medium text-gray-800">{row.title || '-'}</span>
                  </td>
                  {columns.slug && (
                    <td className="py-2 px-3">
                      {row.slug ? (
                        <code className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700">{row.slug}</code>
                      ) : (
                        <span className="text-gray-500">-</span>
                      )}
                    </td>
                  )}
                  {columns.author && <td className="py-2 px-3 text-gray-700">{row.author_name || '-'}</td>}
                  {columns.status && <td className="py-2 px-3">{renderStatus()}</td>}
                  {columns.embedding && <td className="py-2 px-3">{renderEmbeddingBadge(row.embedding_status)}</td>}
                  {columns.updated && <td className="py-2 px-3 text-gray-500">{updated}</td>}
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
                          onOpenMenu(openMenuRow === row.id ? null : row.id);
                        }}
                      >
                        <EllipsisVerticalIcon className="h-5 w-5 text-gray-500" />
                      </button>
                      {openMenuRow === row.id && (
                        <div className="absolute right-0 top-9 z-30 w-48 rounded-md border border-gray-200 bg-white shadow-lg dark:border-dark-500 dark:bg-dark-700">
                          <button
                            className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600 disabled:opacity-50"
                            onClick={() => onCopyLink(row)}
                            disabled={!row.slug}
                            type="button"
                          >
                            <LinkIcon className="h-4 w-4" /> Copy link
                          </button>
                          {normalizedStatus === 'deleted' && (
                            <button
                              type="button"
                              className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-green-700 hover:bg-green-50 dark:hover:bg-green-500/20"
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
                            onClick={() => onEdit(row)}
                          >
                            <PencilIcon className="h-4 w-4" /> Edit
                          </button>
                          <button
                            type="button"
                            className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-500/20"
                            onClick={() => onDelete(row)}
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
  );
}

import React from 'react';
import { Spinner } from '@ui';
import { MagnifyingGlassIcon, PlusIcon } from '@heroicons/react/24/outline';

import type { NodeStatus, SortKey, SortOrder, UserOption } from '../types';

export type NodesFiltersProps = {
  q: string;
  slugQuery: string;
  sort: SortKey;
  order: SortOrder;
  status: NodeStatus;
  statusOptions: Array<{ value: NodeStatus; label: string }>;
  loading: boolean;
  authorId: string;
  authorQuery: string;
  userOptions: UserOption[];
  showUserOptions: boolean;
  isDraftFilter: boolean;
  hasCustomStatus: boolean;
  onQueryChange: (value: string) => void;
  onSlugChange: (value: string) => void;
  onSortChange: (value: SortKey) => void;
  onOrderChange: (value: SortOrder) => void;
  onStatusChange: (value: NodeStatus) => void;
  onAuthorChange: (value: string) => void;
  onAuthorFocus: () => void;
  onAuthorSelect: (option: UserOption) => void;
  onAuthorClear: () => void;
  onCreateNode: () => void;
  onImportExport: () => void;
  onAnnounce: () => void;
};

export function NodesFilters({
  q,
  slugQuery,
  sort,
  order,
  status,
  statusOptions,
  loading,
  authorId,
  authorQuery,
  userOptions,
  showUserOptions,
  isDraftFilter,
  hasCustomStatus,
  onQueryChange,
  onSlugChange,
  onSortChange,
  onOrderChange,
  onStatusChange,
  onAuthorChange,
  onAuthorFocus,
  onAuthorSelect,
  onAuthorClear,
  onCreateNode,
  onImportExport,
  onAnnounce,
}: NodesFiltersProps) {
  return (
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
              onChange={(e) => onQueryChange(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 dark:border-dark-500 dark:bg-dark-700">
            <span className="text-xs text-gray-500">Slug</span>
            <input
              className="h-9 w-56 bg-transparent text-sm outline-none placeholder:text-gray-400"
              placeholder="16-hex"
              value={slugQuery}
              onChange={(e) => onSlugChange(e.target.value)}
            />
          </div>
          {loading && <Spinner size="sm" />}
          <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 py-1 text-sm dark:border-dark-500 dark:bg-dark-700">
            <span className="text-xs text-gray-500">Sort</span>
            <select className="form-select h-9 w-40" value={sort} onChange={(e) => onSortChange(e.target.value as SortKey)}>
              <option value="updated_at">Updated</option>
              <option value="title">Title</option>
              <option value="author">Author</option>
              <option value="status">Status</option>
            </select>
            <select className="form-select h-9 w-28" value={order} onChange={(e) => onOrderChange(e.target.value as SortOrder)}>
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
              onChange={(e) => onAuthorChange(e.target.value)}
              onFocus={onAuthorFocus}
            />
            {authorId && (
              <button
                className="rounded bg-gray-200 px-2 text-xs hover:bg-gray-300 dark:bg-dark-600"
                onClick={onAuthorClear}
                type="button"
              >
                Clear
              </button>
            )}
            {showUserOptions && userOptions.length > 0 && (
              <div className="absolute left-0 top-10 z-10 w-64 rounded border border-gray-300 bg-white shadow dark:border-dark-500 dark:bg-dark-700">
                {userOptions.map((option) => (
                  <button
                    key={option.id}
                    type="button"
                    className="block w-full truncate px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                    onClick={() => onAuthorSelect(option)}
                  >
                    {option.username || option.id}
                  </button>
                ))}
              </div>
            )}
          </div>
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded hover:bg-gray-200/60 dark:hover:bg-dark-500"
            title="Create node"
            onClick={onCreateNode}
          >
            <PlusIcon className="h-5 w-5 text-gray-600" />
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-sm">
        <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-1.5 dark:border-dark-500 dark:bg-dark-700">
          <span className="text-xs text-gray-500">Status</span>
          <select
            className="form-select h-8 w-44 text-xs"
            value={status}
            onChange={(e) => onStatusChange(e.target.value as NodeStatus)}
          >
            {statusOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
            isDraftFilter
              ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-600/60 dark:bg-primary-900/30 dark:text-primary-300'
              : 'border-gray-300 text-gray-600 hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60'
          }`}
          onClick={() => onStatusChange('draft')}
        >
          Drafts only
        </button>
        {hasCustomStatus && (
          <button
            type="button"
            className="rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60"
            onClick={() => onStatusChange('all')}
          >
            Clear filter
          </button>
        )}
        <button
          type="button"
          className="rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60"
          onClick={onImportExport}
        >
          Import / export
        </button>
        <button
          type="button"
          className="rounded-full border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-600 transition hover:bg-gray-100 dark:border-dark-500 dark:text-dark-100 dark:hover:bg-dark-700/60"
          onClick={onAnnounce}
        >
          Announce update
        </button>
      </div>
    </div>
  );
}

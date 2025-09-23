import React from 'react';
import { Pagination } from '../primitives/Pagination';

type TablePaginationProps = {
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  currentCount: number;
  totalItems?: number;
  hasNext?: boolean;
  pageSizeOptions?: number[];
  className?: string;
  summaryPrefix?: string;
  children?: React.ReactNode;
};

export function TablePagination({
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  currentCount,
  totalItems,
  hasNext,
  pageSizeOptions = [10, 20, 50, 100],
  className = '',
  summaryPrefix = 'Showing',
  children,
}: TablePaginationProps) {
  const start = currentCount > 0 ? (page - 1) * pageSize + 1 : 0;
  const end = currentCount > 0 ? (page - 1) * pageSize + currentCount : 0;
  const totalLabel =
    typeof totalItems === 'number'
      ? totalItems.toLocaleString()
      : hasNext
      ? '...'
      : end.toLocaleString();
  const summary = currentCount === 0
    ? `${summaryPrefix} 0`
    : `${summaryPrefix} ${start.toLocaleString()}-${end.toLocaleString()}${totalItems != null || hasNext ? ` of ${totalLabel}` : ''}`;

  const totalPages =
    typeof totalItems === 'number'
      ? Math.max(1, Math.ceil(totalItems / Math.max(pageSize, 1)))
      : undefined;

  return (
    <div className={`table-pagination flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between ${className}`}>
      <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-dark-200">
        <div className="flex items-center gap-2">
          <span className="text-gray-500 dark:text-dark-300">Rows per page</span>
          <select
            className="form-select h-8 w-24"
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
          >
            {pageSizeOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
        <span className="text-gray-500 dark:text-dark-300">{summary}</span>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {children}
        <Pagination
          page={page}
          total={totalPages}
          hasNext={typeof totalItems !== 'number' ? hasNext : undefined}
          onChange={onPageChange}
        />
      </div>
    </div>
  );
}


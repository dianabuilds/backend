import React from "react";

import type { Column } from "./DataTable.helpers";
import Skeleton from "./Skeleton";

type Props<T> = {
  columns: Column<T>[];
  rows: T[];
  emptyText?: string;
  rowKey: (row: T) => string;
  className?: string;
  loading?: boolean;
  skeletonRows?: number;
  onRowClick?: (row: T) => void;
};

export default function DataTable<T>({
  columns,
  rows,
  emptyText,
  rowKey,
  className,
  loading = false,
  skeletonRows = 3,
  onRowClick,
}: Props<T>) {
  return (
    <div className={className || ""}>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm" role="table">
          <thead>
            <tr className="text-left text-gray-500" role="row">
              {columns.map((c) => (
                <th
                  key={c.key}
                  className={`px-2 py-1 ${c.className || ""}`}
                  style={c.width ? { width: c.width } : undefined}
                  scope="col"
                >
                  {c.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: skeletonRows }).map((_, i) => (
                  <tr key={`skeleton-${i}`} className="border-t" role="row">
                    {columns.map((c) => (
                      <td key={c.key} className="px-2 py-1">
                        <Skeleton className="h-4 w-full" />
                      </td>
                    ))}
                  </tr>
                ))
              : (rows || []).map((row) => (
                  <tr
                    key={rowKey(row)}
                    className="border-t"
                    role="row"
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                  >
                    {columns.map((c) => (
                      <td
                        key={c.key}
                        className={`px-2 py-1 ${c.className || ""}`}
                      >
                        {c.render
                          ? c.render(row)
                          : c.accessor
                            ? c.accessor(row)
                            : (row as any)[c.key]}
                      </td>
                    ))}
                  </tr>
                ))}
            {!loading && (rows || []).length === 0 ? (
              <tr>
                <td
                  className="px-2 py-3 text-gray-500"
                  colSpan={columns.length}
                >
                  {emptyText || "Нет данных"}
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}

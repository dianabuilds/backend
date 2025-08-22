import React from "react";

export type Column<T> = {
  key: string;
  title: string;
  width?: string | number;
  render?: (row: T) => React.ReactNode;
  accessor?: (row: T) => React.ReactNode;
  className?: string;
};

type Props<T> = {
  columns: Column<T>[];
  data: T[];
  emptyText?: string;
  rowKey: (row: T) => string;
  className?: string;
};

export default function DataTable<T>({ columns, data, emptyText, rowKey, className }: Props<T>) {
  return (
    <div className={className || ""}>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-gray-500">
              {columns.map((c) => (
                <th key={c.key} className={`px-2 py-1 ${c.className || ""}`} style={c.width ? { width: c.width } : undefined}>
                  {c.title}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(data || []).map((row) => (
              <tr key={rowKey(row)} className="border-t">
                {columns.map((c) => (
                  <td key={c.key} className={`px-2 py-1 ${c.className || ""}`}>
                    {c.render ? c.render(row) : c.accessor ? c.accessor(row) : (row as any)[c.key]}
                  </td>
                ))}
              </tr>
            ))}
            {(data || []).length === 0 ? (
              <tr>
                <td className="px-2 py-3 text-gray-500" colSpan={columns.length}>
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

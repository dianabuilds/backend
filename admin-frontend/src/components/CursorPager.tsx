import React from "react";

type Props = {
  hasMore: boolean;
  loading?: boolean;
  onLoadMore: () => void | Promise<void>;
  className?: string;
  label?: string;
};

export default function CursorPager({ hasMore, loading, onLoadMore, className, label }: Props) {
  if (!hasMore) return null;
  return (
    <div className={className ?? "flex justify-center my-3"}>
      <button
        onClick={() => onLoadMore()}
        disabled={loading}
        className="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
      >
        {loading ? "Загрузка…" : (label || "Показать ещё")}
      </button>
    </div>
  );
}

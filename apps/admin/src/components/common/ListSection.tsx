import React from 'react';

interface Props {
  title: React.ReactNode;
  loading?: boolean;
  error?: unknown;
  children: React.ReactNode;
  className?: string;
}

export default function ListSection({ title, loading, error, children, className = '' }: Props) {
  return (
    <div className={`rounded border p-3 ${className}`.trim()}>
      <div className="text-sm text-gray-500 mb-2">{title}</div>
      {loading ? <div className="text-sm text-gray-500">Загрузка…</div> : null}
      {error ? (
        <div className="text-sm text-red-600">
          {error instanceof Error ? error.message : String(error)}
        </div>
      ) : null}
      {children}
    </div>
  );
}


import React from 'react';

type ProgressProps = {
  value: number; // 0..100
  className?: string;
};

export function Progress({ value, className = '' }: ProgressProps) {
  const v = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div className={`h-2 w-full rounded-full bg-gray-200 dark:bg-dark-600 ${className}`}>
      <div
        className="h-2 rounded-full bg-primary-600 transition-[width] duration-300 ease-out"
        style={{ width: `${v}%` }}
      />
    </div>
  );
}


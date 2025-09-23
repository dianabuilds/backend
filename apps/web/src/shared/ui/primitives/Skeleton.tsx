import React from 'react';

type SkeletonProps = React.HTMLAttributes<HTMLDivElement> & {
  rounded?: boolean | 'full';
};

export function Skeleton({ className = '', rounded, ...rest }: SkeletonProps) {
  const r = rounded === 'full' ? 'rounded-full' : rounded ? 'rounded' : '';
  return (
    <div
      className={`skeleton animate-pulse bg-gray-200 dark:bg-dark-600 ${r} ${className}`.trim()}
      {...rest}
    />
  );
}


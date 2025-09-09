import type { HTMLAttributes } from 'react';

/**
 * Simple gray placeholder used as a skeleton while content loads.
 */
export default function Skeleton({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={['animate-pulse rounded bg-gray-200 dark:bg-gray-700', className || ''].join(' ')}
      {...rest}
    />
  );
}

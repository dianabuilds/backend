import React from 'react';

export type SurfaceVariant = 'frosted' | 'soft' | 'plain';

const variantMap: Record<SurfaceVariant, string> = {
  frosted:
    'border border-white/60 bg-white/70 shadow-[0_10px_40px_-30px_rgba(17,24,39,0.7)] backdrop-blur-xl dark:border-white/10 dark:bg-dark-800/70 dark:shadow-[0_20px_60px_-35px_rgba(14,23,42,0.9)]',
  soft:
    'border border-gray-200/70 bg-gray-50/90 shadow-soft backdrop-blur-sm dark:border-dark-600/60 dark:bg-dark-800/60',
  plain: 'border border-transparent bg-transparent',
};

export type SurfaceProps = React.HTMLAttributes<HTMLDivElement> & {
  variant?: SurfaceVariant;
  inset?: boolean;
};

/**
 * Utility wrapper that gives sections a polished "card" look while keeping spacing consistent.
 */
export function Surface({ variant = 'frosted', inset = false, className = '', ...rest }: SurfaceProps) {
  const padding = inset ? 'p-0 sm:p-0' : 'p-6 sm:p-8';
  return (
    <section
      {...rest}
      className={`relative overflow-hidden rounded-3xl transition duration-300 ${variantMap[variant]} ${padding} ${className}`}
    />
  );
}

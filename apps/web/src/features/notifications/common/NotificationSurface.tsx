import React from 'react';
import { Card } from '@ui';

type NotificationSurfaceProps = React.ComponentProps<typeof Card>;

const SURFACE_BASE =
  'w-full max-w-full rounded-3xl border border-white/60 bg-gradient-to-br from-indigo-50 via-white to-indigo-100 shadow-[0_30px_60px_-25px_rgba(79,70,229,0.45)] backdrop-blur-xl dark:border-dark-600/70 dark:from-dark-700/80 dark:via-dark-750/80 dark:to-dark-800/90';

export const notificationTableHeadCellClass =
  'bg-indigo-100 text-indigo-900 uppercase tracking-wide text-xs font-semibold leading-tight py-3 px-4 align-middle first:rounded-l-2xl last:rounded-r-2xl dark:bg-dark-650 dark:text-dark-50';
export const notificationTableRowClass =
  'border-b border-indigo-100/60 bg-white/70 backdrop-blur-sm transition-colors hover:bg-white/90 last:border-none dark:border-dark-600/50 dark:bg-dark-700/60 dark:hover:bg-dark-650';

export function NotificationSurface({ className = '', ...props }: NotificationSurfaceProps) {
  return <Card skin="none" {...props} className={`${SURFACE_BASE} ${className}`.trim()} />;
}

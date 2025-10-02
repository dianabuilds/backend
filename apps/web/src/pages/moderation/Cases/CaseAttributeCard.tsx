import React from 'react';

export type CaseAttributeTone = 'default' | 'highlight' | 'muted';

export type CaseAttributeItem = {
  id: string;
  label: React.ReactNode;
  value?: React.ReactNode;
  hint?: React.ReactNode;
  action?: React.ReactNode;
  tone?: CaseAttributeTone;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  valueClassName?: string;
};

function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(' ');
}

const toneMap: Record<CaseAttributeTone, string> = {
  default:
    'border-gray-200 bg-white text-gray-800 dark:border-dark-600 dark:bg-dark-700/60 dark:text-gray-100',
  highlight:
    'border-primary-200 bg-primary-50 text-primary-900 shadow-sm dark:border-primary-500/40 dark:bg-primary-500/10 dark:text-primary-100',
  muted:
    'border-gray-100 bg-gray-50 text-gray-700 dark:border-dark-600 dark:bg-dark-700/40 dark:text-gray-200',
};

const hintToneMap: Record<CaseAttributeTone, string> = {
  default: 'text-xs text-gray-400 dark:text-gray-400',
  highlight: 'text-xs text-primary-700/80 dark:text-primary-200/80',
  muted: 'text-xs text-gray-400 dark:text-gray-500',
};

export function CaseAttributeCard({
  label,
  value,
  hint,
  action,
  tone = 'default',
  onClick,
  disabled,
  className = '',
  valueClassName = '',
}: Omit<CaseAttributeItem, 'id'>) {
  const isInteractive = Boolean(onClick) && !disabled;
  const interactiveProps = isInteractive
    ? {
        role: 'button' as const,
        tabIndex: 0,
        onClick: onClick,
        onKeyDown: (event: React.KeyboardEvent<HTMLDivElement>) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            onClick?.();
          }
        },
      }
    : {};

  return (
    <div
      {...interactiveProps}
      className={cx(
        'group flex h-full flex-col gap-2 rounded-2xl border p-3 text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-dark-800',
        toneMap[tone] ?? toneMap.default,
        isInteractive && 'cursor-pointer hover:shadow-md dark:hover:shadow-primary-900/20',
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
          {label}
        </div>
        {action ? (
          <div
            className="shrink-0"
            onClick={(event) => event.stopPropagation()}
            onKeyDown={(event) => event.stopPropagation()}
          >
            {action}
          </div>
        ) : null}
      </div>
      <div className={cx('break-words text-base font-semibold', tone === 'highlight' ? 'text-inherit' : 'text-gray-900 dark:text-gray-100', valueClassName)}>
        {value ?? '-'}
      </div>
      {hint && <div className={hintToneMap[tone] ?? hintToneMap.default}>{hint}</div>}
    </div>
  );
}

export function CaseAttributeGrid({ items, className = '' }: { items: CaseAttributeItem[]; className?: string }) {
  if (!items.length) return null;
  return (
    <div className={cx('grid gap-4 sm:grid-cols-2 xl:grid-cols-3', className)}>
      {items.map(({ id, ...rest }) => (
        <CaseAttributeCard key={id} {...rest} />
      ))}
    </div>
  );
}



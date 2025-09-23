import React from 'react';

type CardProps = React.HTMLAttributes<HTMLDivElement> & { skin?: 'bordered' | 'shadow' | 'none' };

// Native template classes: card + rounded + skin
export function Card({ className = '', skin = 'bordered', ...props }: CardProps) {
  const base = 'card rounded-lg';
  const skinCls =
    skin === 'bordered'
      ? 'border border-gray-200 dark:border-dark-600'
      : skin === 'shadow'
        ? 'shadow-soft dark:bg-dark-700 bg-white dark:shadow-none'
        : '';
  const cls = `${base} ${skinCls} ${className}`.trim();
  return <div {...props} className={cls} />;
}

import React from 'react';

type CardProps = React.HTMLAttributes<HTMLDivElement> & { skin?: 'bordered' | 'shadow' | 'none'; padding?: 'none' | 'sm' | 'md' | 'lg' };

const paddingMap: Record<NonNullable<CardProps['padding']>, string> = { none: '', sm: 'p-4', md: 'p-6', lg: 'p-8' };

// Native template classes: card + rounded + skin
export function Card({ className = '', skin = 'bordered', padding, ...props }: CardProps) {
  const base = 'card rounded-lg';
  const skinCls =
    skin === 'bordered'
      ? 'border border-gray-200 dark:border-dark-600'
      : skin === 'shadow'
        ? 'shadow-soft dark:bg-dark-700 bg-white dark:shadow-none'
        : '';
  const paddingCls = padding ? paddingMap[padding] : '';
  const cls = `${base} ${skinCls} ${paddingCls} ${className}`.trim();
  return <div {...props} className={cls} />;
}

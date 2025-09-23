import React from 'react';

type TagProps = React.HTMLAttributes<HTMLSpanElement> & {
  color?: 'gray' | 'primary' | 'emerald' | 'amber' | 'sky' | 'rose';
};

const colorToBg: Record<NonNullable<TagProps['color']>, string> = {
  gray: 'bg-gray-100 text-gray-700',
  primary: 'bg-primary-50 text-primary-700',
  emerald: 'bg-emerald-50 text-emerald-700',
  amber: 'bg-amber-50 text-amber-700',
  sky: 'bg-sky-50 text-sky-700',
  rose: 'bg-rose-50 text-rose-700',
};

export function Tag({ color = 'gray', className = '', ...rest }: TagProps) {
  const cls = `inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colorToBg[color]} ${className}`.trim();
  return <span className={cls} {...rest} />;
}


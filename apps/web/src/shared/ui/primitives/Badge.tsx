import React from 'react';

type BadgeProps = React.HTMLAttributes<HTMLSpanElement> & {
  color?: 'primary' | 'success' | 'warning' | 'error' | 'neutral' | 'info';
  variant?: 'soft' | 'solid' | 'outline';
};

const colorMap: Record<NonNullable<BadgeProps['color']>, { solid: string; soft: string; outline: string }> = {
  primary: {
    solid: 'bg-primary-600 text-white',
    soft: 'bg-primary-50 text-primary-700',
    outline: 'border border-primary-600 text-primary-700',
  },
  success: {
    solid: 'bg-emerald-600 text-white',
    soft: 'bg-emerald-50 text-emerald-700',
    outline: 'border border-emerald-600 text-emerald-700',
  },
  warning: {
    solid: 'bg-amber-500 text-white',
    soft: 'bg-amber-50 text-amber-700',
    outline: 'border border-amber-500 text-amber-700',
  },
  error: {
    solid: 'bg-rose-600 text-white',
    soft: 'bg-rose-50 text-rose-700',
    outline: 'border border-rose-600 text-rose-700',
  },
  info: {
    solid: 'bg-sky-600 text-white',
    soft: 'bg-sky-50 text-sky-700',
    outline: 'border border-sky-600 text-sky-700',
  },
  neutral: {
    solid: 'bg-gray-700 text-white',
    soft: 'bg-gray-100 text-gray-700',
    outline: 'border border-gray-400 text-gray-700',
  },
};

export function Badge({ color = 'neutral', variant = 'soft', className = '', ...rest }: BadgeProps) {
  const style = colorMap[color][variant];
  const base = `badge inline-flex items-center rounded px-2 py-0.5 text-xs ${style} ${className}`.trim();
  return <span className={base} {...rest} />;
}


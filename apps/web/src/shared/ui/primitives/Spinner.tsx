import React from 'react';

type SpinnerProps = React.HTMLAttributes<HTMLDivElement> & {
  size?: 'sm' | 'md' | 'lg';
};

export function Spinner({ size = 'md', className = '', ...rest }: SpinnerProps) {
  const sizes: Record<NonNullable<SpinnerProps['size']>, string> = {
    sm: 'h-4 w-4 border-2',
    md: 'h-6 w-6 border-2',
    lg: 'h-8 w-8 border-3',
  };
  const cls = `inline-block animate-spin rounded-full border-current border-t-transparent text-primary-600 ${sizes[size]} ${className}`.trim();
  return <div role="status" aria-label="loading" className={cls} {...rest} />;
}


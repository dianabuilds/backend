import React from 'react';

type AvatarProps = React.HTMLAttributes<HTMLDivElement> & {
  src?: string | null;
  alt?: string;
  name?: string; // used for fallback initial
  size?: 'sm' | 'md' | 'lg';
  rounded?: boolean;
};

export function Avatar({ src, alt, name, size = 'md', rounded = true, className = '', ...rest }: AvatarProps) {
  const sizes: Record<NonNullable<AvatarProps['size']>, string> = {
    sm: 'size-8 text-xs',
    md: 'size-10 text-sm',
    lg: 'size-12 text-base',
  };
  const base = `avatar inline-flex items-center justify-center ${sizes[size]} ${rounded ? 'rounded-full' : 'rounded-md'} overflow-hidden bg-gray-200 text-gray-700 dark:bg-dark-600 ${className}`.trim();
  const fallback = (name || alt || '?').trim()[0]?.toUpperCase() || '?';
  return (
    <div className={base} {...rest}>
      {src ? (
        <img src={src} alt={alt || name || ''} className="h-full w-full object-cover" />
      ) : (
        <span>{fallback}</span>
      )}
    </div>
  );
}


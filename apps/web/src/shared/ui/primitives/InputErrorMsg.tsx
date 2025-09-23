import React from 'react';

type Props = {
  when?: boolean;
  children?: React.ReactNode;
  className?: string;
};

export function InputErrorMsg({ when, children, className = '' }: Props) {
  if (!when) return null;
  return (
    <span className={`input-text-error mt-1 text-xs text-error dark:text-error-lighter ${className}`}>
      {children}
    </span>
  );
}

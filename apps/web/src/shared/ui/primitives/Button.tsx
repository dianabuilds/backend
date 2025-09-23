import React from 'react';

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'filled' | 'outlined' | 'ghost';
  color?: 'primary' | 'neutral';
  size?: 'sm' | 'md' | 'icon';
};

// Uses native template classes: btn-base + btn + color utilities
export function Button({ variant = 'filled', color = 'primary', size = 'md', className = '', ...props }: ButtonProps) {
  const base = 'btn-base btn';
  const filled =
    color === 'primary'
      ? 'bg-primary-600 text-white hover:bg-primary-700 focus:bg-primary-700 active:bg-primary-700/90'
      : 'bg-gray-150 text-gray-900 hover:bg-gray-200 focus:bg-gray-200 active:bg-gray-200/80';
  const outlined =
    color === 'primary'
      ? 'text-primary-700 border border-primary-600 hover:bg-primary-600/10 focus:bg-primary-600/10'
      : 'text-gray-900 border border-gray-300 hover:bg-gray-300/20 focus:bg-gray-300/20';
  const ghost = color === 'primary' ? 'text-primary-700 hover:bg-primary-600/10' : 'text-gray-800 hover:bg-gray-100';
  const sizeCls = size === 'sm' ? 'h-8 px-3 text-xs' : size === 'icon' ? 'h-8 w-8 p-0 inline-flex items-center justify-center' : '';
  const variantCls = variant === 'filled' ? filled : variant === 'outlined' ? outlined : ghost;
  const cls = `${base} ${sizeCls} ${variantCls} ${className}`.trim();
  return <button {...props} className={cls} />;
}

import React from 'react';

type ButtonVariant = 'filled' | 'outlined' | 'ghost';
type ButtonColor = 'primary' | 'neutral' | 'error';
type ButtonSize = 'xs' | 'sm' | 'md' | 'icon';

type ButtonOwnProps = {
  variant?: ButtonVariant;
  color?: ButtonColor;
  size?: ButtonSize;
  className?: string;
};

type ButtonProps<C extends React.ElementType = 'button'> = {
  as?: C;
} & ButtonOwnProps & Omit<React.ComponentPropsWithoutRef<C>, keyof ButtonOwnProps | 'as'>;

const ButtonBase = <C extends React.ElementType = 'button'>(
  { as, variant = 'filled', color = 'primary', size = 'md', className = '', ...rest }: ButtonProps<C>,
  ref: React.Ref<Element>,
) => {
  const Component = (as || 'button') as React.ElementType;
  const base = 'btn-base btn';
  const styles: Record<ButtonColor, Record<ButtonVariant, string>> = {
    primary: {
      filled: 'bg-primary-600 text-white hover:bg-primary-700 focus:bg-primary-700 active:bg-primary-700/90',
      outlined: 'text-primary-700 border border-primary-600 hover:bg-primary-600/10 focus:bg-primary-600/10',
      ghost: 'text-primary-700 hover:bg-primary-600/10',
    },
    neutral: {
      filled: 'bg-gray-150 text-gray-900 hover:bg-gray-200 focus:bg-gray-200 active:bg-gray-200/80',
      outlined: 'text-gray-900 border border-gray-300 hover:bg-gray-300/20 focus:bg-gray-300/20',
      ghost: 'text-gray-800 hover:bg-gray-100',
    },
    error: {
      filled: 'bg-rose-600 text-white hover:bg-rose-700 focus:bg-rose-700 active:bg-rose-700/90',
      outlined: 'text-rose-700 border border-rose-600 hover:bg-rose-600/10 focus:bg-rose-600/10',
      ghost: 'text-rose-600 hover:bg-rose-50',
    },
  };
  const sizeCls =
    size === 'xs'
      ? 'h-7 px-2 text-[11px]'
      : size === 'sm'
      ? 'h-8 px-3 text-xs'
      : size === 'icon'
      ? 'h-8 w-8 p-0 inline-flex items-center justify-center'
      : 'h-10 px-4';
  const variantCls = styles[color][variant];
  const cls = `${base} ${sizeCls} ${variantCls} ${className}`.trim();
  return <Component ref={ref} className={cls} {...rest} />;
};

export const Button = React.forwardRef(ButtonBase) as <C extends React.ElementType = 'button'>(
  props: ButtonProps<C> & { ref?: React.Ref<React.ElementRef<C>> },
) => React.ReactElement | null;


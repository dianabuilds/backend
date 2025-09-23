import React from 'react';

type BoxProps<T extends React.ElementType = 'div'> = {
  component?: T;
} & React.ComponentPropsWithoutRef<T>;

export function Box<T extends React.ElementType = 'div'>(
  { component, ...props }: BoxProps<T>
) {
  const Comp: any = component || 'div';
  return <Comp {...props} />;
}


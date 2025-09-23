import React from 'react';

type CollapseProps = React.HTMLAttributes<HTMLDivElement> & {
  open?: boolean;
  unmountOnExit?: boolean;
};

export function Collapse({ open = false, unmountOnExit, style, children, ...rest }: CollapseProps) {
  if (unmountOnExit && !open) return null;
  return (
    <div
      aria-hidden={!open}
      style={{ display: open ? 'block' : 'none', ...style }}
      {...rest}
    >
      {children}
    </div>
  );
}


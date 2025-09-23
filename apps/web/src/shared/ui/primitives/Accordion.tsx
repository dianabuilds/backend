import React from 'react';

type AccordionProps = {
  title: React.ReactNode;
  defaultOpen?: boolean;
  children?: React.ReactNode;
  className?: string;
};

export function Accordion({ title, defaultOpen = false, children, className = '' }: AccordionProps) {
  const [open, setOpen] = React.useState(defaultOpen);
  return (
    <div className={`rounded-md border border-gray-200 dark:border-dark-600 ${className}`}>
      <button type="button" className="flex w-full items-center justify-between px-4 py-3 text-sm font-semibold" onClick={() => setOpen((v) => !v)}>
        <span>{title}</span>
        <span className="text-gray-400">{open ? '▾' : '▸'}</span>
      </button>
      <div className={`${open ? 'block' : 'hidden'} border-t border-gray-200 dark:border-dark-600`}>{children}</div>
    </div>
  );
}

export default Accordion;


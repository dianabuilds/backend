import React from 'react';

type DrawerProps = {
  open: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  footer?: React.ReactNode;
  widthClass?: string; // e.g., 'w-[520px]'
  children?: React.ReactNode;
};

export function Drawer({ open, onClose, title, footer, widthClass = 'w-[520px]', children }: DrawerProps) {
  return (
    <div className={`fixed inset-0 z-50 ${open ? '' : 'pointer-events-none'}`} aria-hidden={!open}>
      {/* Backdrop */}
      <div
        className={`absolute inset-0 bg-black/20 transition-opacity ${open ? 'opacity-100' : 'opacity-0'}`}
        onClick={onClose}
      />
      {/* Panel */}
      <div
        className={`absolute inset-y-0 right-0 bg-white dark:bg-dark-800 shadow-xl border-l border-gray-200 dark:border-dark-600 flex flex-col ${widthClass} transform transition-transform ${open ? 'translate-x-0' : 'translate-x-full'}`}
      >
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-dark-700">
          <div className="text-sm font-semibold">{title}</div>
          <button className="text-gray-400 hover:text-gray-700" onClick={onClose} aria-label="Close">×</button>
        </div>
        <div className="flex-1 overflow-auto">{children}</div>
        {footer && (
          <div className="px-4 py-3 border-t border-gray-100 dark:border-dark-700">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

export default Drawer;


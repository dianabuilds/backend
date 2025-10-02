import React from 'react';

const focusableSelectors = [
  'a[href]',
  "button:not([disabled])",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(',');

type DialogSize = 'sm' | 'md' | 'lg';

type DialogProps = {
  open: boolean;
  onClose?: () => void;
  title?: React.ReactNode;
  children?: React.ReactNode;
  footer?: React.ReactNode;
  size?: DialogSize;
  initialFocusRef?: React.RefObject<HTMLElement>;
  labelledBy?: string;
  descriptionId?: string;
  className?: string;
};

function getFocusable(container: HTMLElement | null): HTMLElement[] {
  if (!container) return [];
  const nodes = Array.from(container.querySelectorAll<HTMLElement>(focusableSelectors));
  return nodes.filter((node) => !node.hasAttribute('disabled') && node.getAttribute('tabindex') !== '-1');
}

export function Dialog({
  open,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  initialFocusRef,
  labelledBy,
  descriptionId,
  className = '',
}: DialogProps) {
  const dialogRef = React.useRef<HTMLDivElement>(null);
  const previouslyFocused = React.useRef<HTMLElement | null>(null);
  const autoTitleId = React.useId();
  const shouldWrapBody = React.useMemo(() => {
    if (children == null) return false;
    const asArray = React.Children.toArray(children);
    return asArray.every((child) => typeof child === 'string' || typeof child === 'number');
  }, [children]);

  const sizeClasses: Record<DialogSize, string> = {
    sm: 'max-w-md',
    md: 'max-w-xl',
    lg: 'max-w-2xl',
  };

  React.useEffect(() => {
    if (open) {
      previouslyFocused.current = document.activeElement as HTMLElement | null;
      const focusTarget = initialFocusRef?.current || dialogRef.current;
      window.setTimeout(() => {
        focusTarget?.focus();
      }, 0);
    } else if (previouslyFocused.current) {
      previouslyFocused.current.focus?.();
      previouslyFocused.current = null;
    }
  }, [open, initialFocusRef]);

  const handleKeyDown = React.useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (event.key === 'Escape') {
        if (onClose) {
          event.preventDefault();
          onClose();
        }
        return;
      }
      if (event.key !== 'Tab') return;
      const focusables = getFocusable(dialogRef.current);
      if (focusables.length === 0) {
        event.preventDefault();
        dialogRef.current?.focus();
        return;
      }
      const first = focusables[0];
      const last = focusables[focusables.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (event.shiftKey) {
        if (!active || active === first) {
          event.preventDefault();
          last.focus();
        }
      } else if (!active || active === last) {
        event.preventDefault();
        first.focus();
      }
    },
    [onClose],
  );

  if (!open) return null;

  const resolvedLabelId = labelledBy || (title ? `${autoTitleId}-title` : undefined);
  const resolvedDescriptionId = descriptionId || (shouldWrapBody ? `${autoTitleId}-description` : undefined);

  const body = shouldWrapBody ? (
    <p id={resolvedDescriptionId} className="text-sm leading-relaxed text-gray-600 dark:text-dark-200">
      {children}
    </p>
  ) : (
    <div id={resolvedDescriptionId}>{children}</div>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4 py-6">
      {onClose ? (
        <button
          type="button"
          className="absolute inset-0 bg-black/40 backdrop-blur-[1px]"
          aria-label="Close dialog"
          onClick={onClose}
        />
      ) : (
        <div className="absolute inset-0 bg-black/40 backdrop-blur-[1px]" aria-hidden="true" />
      )}
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={resolvedLabelId}
        aria-describedby={resolvedDescriptionId}
        tabIndex={-1}
        className={`relative w-full ${sizeClasses[size]} rounded-xl bg-white shadow-2xl outline-none transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary-500 dark:bg-dark-800 ${className}`}
        onKeyDown={handleKeyDown}
      >
        <div className="flex flex-col gap-4 p-6">
          {title ? (
            <div id={resolvedLabelId} className="text-lg font-semibold text-gray-900 dark:text-dark-50">
              {title}
            </div>
          ) : null}
          {body}
        </div>
        {footer ? (
          <div className="flex items-center justify-end gap-3 border-t border-gray-100 px-6 py-4 dark:border-dark-600">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default Dialog;

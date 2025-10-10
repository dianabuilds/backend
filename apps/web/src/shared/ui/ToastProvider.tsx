import React from 'react';
import ReactDOM from 'react-dom';

import { ToastContext, type ToastIntent, type ToastOptions } from './ToastContext';
import { subscribeToGlobalToasts } from './toastBus';

type ToastEntry = {
  id: string;
  title?: string;
  description: string;
  intent: ToastIntent;
  durationMs: number;
};

const DEFAULT_DURATION = 5000;

export function ToastProvider({ children }: { children: React.ReactNode }): React.ReactElement {
  const [toasts, setToasts] = React.useState<ToastEntry[]>([]);

  const dismissToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const pushToast = React.useCallback(
    ({ id, title, description, intent = 'info', durationMs = DEFAULT_DURATION }: ToastOptions) => {
      const toastId = id ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`;
      setToasts((prev) => {
        const next = prev.filter((entry) => entry.id !== toastId);
        next.push({ id: toastId, title, description, intent, durationMs });
        return next;
      });
      if (durationMs > 0) {
        window.setTimeout(() => dismissToast(toastId), durationMs);
      }
      return toastId;
    },
    [dismissToast],
  );

  React.useEffect(() => {
    return subscribeToGlobalToasts((detail) => {
      pushToast(detail);
    });
  }, [pushToast]);

  return (
    <ToastContext.Provider value={{ pushToast, dismissToast }}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
}

type ToastViewportProps = {
  toasts: ToastEntry[];
  onDismiss: (id: string) => void;
};

function ToastViewport({ toasts, onDismiss }: ToastViewportProps): React.ReactPortal | null {
  if (typeof document === 'undefined') return null;
  return ReactDOM.createPortal(
    <div className="pointer-events-none fixed bottom-4 right-4 z-[1000] flex w-full max-w-sm flex-col gap-3 sm:right-6">
      {toasts.map((toast) => (
        <ToastCard key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>,
    document.body,
  );
}

type ToastCardProps = {
  toast: ToastEntry;
  onDismiss: (id: string) => void;
};

function ToastCard({ toast, onDismiss }: ToastCardProps) {
  const tone = React.useMemo(() => {
    switch (toast.intent) {
      case 'success':
        return 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-400/40 dark:bg-emerald-500/10 dark:text-emerald-100';
      case 'error':
        return 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100';
      default:
        return 'border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-100';
    }
  }, [toast.intent]);

  return (
    <div className={`pointer-events-auto overflow-hidden rounded-lg border shadow-sm transition ${tone}`}>
      <div className="flex items-start gap-3 px-4 py-3">
        <div className="flex-1">
          {toast.title ? <div className="text-sm font-semibold">{toast.title}</div> : null}
          <div className="text-sm leading-snug">{toast.description}</div>
        </div>
        <button
          type="button"
          className="ml-2 inline-flex shrink-0 items-center justify-center rounded-md bg-black/10 px-2 py-1 text-xs font-semibold uppercase tracking-wide text-black/70 hover:bg-black/20 dark:bg-white/10 dark:text-white/70 dark:hover:bg-white/20"
          onClick={() => onDismiss(toast.id)}
          aria-label="Dismiss notification"
        >
          ×
        </button>
      </div>
    </div>
  );
}


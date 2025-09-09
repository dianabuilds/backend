import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from 'react';

import type { Toast } from './ToastProvider.helpers';

interface ToastContextType {
  addToast: (t: Omit<Toast, 'id'>) => string;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timers = useRef<Record<string, number>>({});

  const removeToast = useCallback((id: string) => {
    setToasts((arr) => arr.filter((t) => t.id !== id));
    const tm = timers.current[id];
    if (tm) {
      window.clearTimeout(tm);
      delete timers.current[id];
    }
  }, []);

  const addToast = useCallback(
    (t: Omit<Toast, 'id'>) => {
      const id = crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + Math.random());
      const toast: Toast = { id, duration: 4000, variant: 'info', ...t };
      setToasts((arr) => [...arr, toast]);
      timers.current[id] = window.setTimeout(() => removeToast(id), toast.duration);
      return id;
    },
    [removeToast],
  );

  const value = useMemo(() => ({ addToast, removeToast }), [addToast, removeToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed top-3 right-3 z-50 space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={[
              'min-w-[260px] max-w-sm rounded shadow px-3 py-2 text-sm text-white',
              t.variant === 'success'
                ? 'bg-emerald-600'
                : t.variant === 'error'
                  ? 'bg-rose-600'
                  : t.variant === 'warning'
                    ? 'bg-amber-600'
                    : 'bg-gray-800',
            ].join(' ')}
            role="status"
          >
            <div className="flex items-start gap-2">
              <div className="flex-1">
                <div className="font-semibold">{t.title}</div>
                {t.description && <div className="opacity-90">{t.description}</div>}
              </div>
              <button
                aria-label="Close"
                className="opacity-80 hover:opacity-100"
                onClick={() => removeToast(t.id)}
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast(): ToastContextType {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}

import type { ToastOptions } from './ToastContext';

export const TOAST_EVENT_NAME = 'app:toast';

type ToastBusDetail = ToastOptions & { id: string };

function createToastId(): string {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function pushGlobalToast(options: ToastOptions): string {
  const id = options.id ?? createToastId();
  if (typeof window !== 'undefined') {
    const detail: ToastBusDetail = { ...options, id };
    window.dispatchEvent(new CustomEvent<ToastBusDetail>(TOAST_EVENT_NAME, { detail }));
  }
  return id;
}

export function subscribeToGlobalToasts(handler: (detail: ToastBusDetail) => void): () => void {
  if (typeof window === 'undefined') {
    return () => undefined;
  }
  const listener = (event: Event) => {
    const custom = event as CustomEvent<ToastBusDetail>;
    if (custom.detail) {
      handler(custom.detail);
    }
  };
  window.addEventListener(TOAST_EVENT_NAME, listener as EventListener);
  return () => window.removeEventListener(TOAST_EVENT_NAME, listener as EventListener);
}

export type { ToastBusDetail };
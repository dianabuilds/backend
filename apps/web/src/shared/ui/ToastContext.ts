import React from 'react';

export type ToastIntent = 'success' | 'info' | 'error';

export type ToastOptions = {
  id?: string;
  title?: string;
  description: string;
  intent?: ToastIntent;
  durationMs?: number;
};

export type ToastContextValue = {
  pushToast: (toast: ToastOptions) => string;
  dismissToast: (id: string) => void;
};

export const ToastContext = React.createContext<ToastContextValue | undefined>(undefined);

import React from 'react';
import { ToastContext, type ToastContextValue } from './ToastContext';

export function useToast(): ToastContextValue {
  const ctx = React.useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return ctx;
}

export default useToast;


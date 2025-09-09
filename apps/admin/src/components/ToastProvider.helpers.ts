import type { ReactNode } from 'react';

export interface Toast {
  id: string;
  title: string;
  description?: ReactNode;
  variant?: 'success' | 'error' | 'info' | 'warning';
  duration?: number; // ms
}

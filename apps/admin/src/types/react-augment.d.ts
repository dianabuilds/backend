// Allow custom attribute `onCommit` for React elements to avoid TS errors.
// Важно: React не будет автоматически пробрасывать этот атрибут в реальный DOM.
// Это только для типовой поддержки, чтобы можно было временно использовать onCommit в JSX.

import 'react';

import type { HTMLAttributes } from 'react';

declare module 'react' {
  interface DOMAttributes {
    onCommit?: (action: unknown) => void;
  }

  interface InputHTMLAttributes<T> extends HTMLAttributes<T> {
    onCommit?: (action: unknown) => void;
  }
}

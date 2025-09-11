import { lazy } from 'react';

// Retry wrapper for React.lazy to mitigate transient dev import errors
// (e.g., Vite HMR race or flaky network on Windows). Keeps code-splitting.
export function lazyWithRetry<T extends { default: React.ComponentType<any> }>(
  factory: () => Promise<T>,
) {
  return lazy(async () => {
    try {
      return await factory();
    } catch (err) {
      // Brief delay and one retry
      await new Promise((r) => setTimeout(r, 150));
      return factory();
    }
  });
}

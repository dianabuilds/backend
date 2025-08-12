import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { normalizeError } from '../errors/AppError';
import { logError } from '../telemetry';

function retryDecider(failureCount: number, error: unknown): boolean {
  const e = normalizeError(error);
  // Не ретраим предсказуемые бизнес-ошибки
  const nonRetryable = new Set(['validation', 'unauthorized', 'forbidden', 'not_found', 'conflict']);
  if (nonRetryable.has(e.code)) return false;
  return failureCount < 2;
}

function retryDelay(attempt: number): number {
  const base = 500;
  const cap = 10_000;
  const exp = Math.min(cap, base * 2 ** attempt);
  const jitter = Math.random() * exp * 0.3;
  return Math.floor(exp - exp * 0.15 + jitter);
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: retryDecider,
      retryDelay,
      staleTime: 30_000,
      gcTime: 5 * 60_000,
      refetchOnWindowFocus: false,
      throwOnError: false,
      onError: (error) => {
        const e = normalizeError(error);
        logError(e, { scope: 'react-query.query' });
      },
    },
    mutations: {
      retry: retryDecider,
      retryDelay,
      onError: (error) => {
        const e = normalizeError(error);
        logError(e, { scope: 'react-query.mutation' });
      },
    },
  },
});

export function AppQueryProvider({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

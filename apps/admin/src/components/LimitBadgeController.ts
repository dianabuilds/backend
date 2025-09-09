import { api } from '../api/client';

// Shared internal state (module singleton)
let limits: Record<string, number> = {};
let messages: Record<string, string> = {};
const listeners = new Set<() => void>();

async function fetchLimits(clearMessages = true) {
  try {
    const res = await api.get<Record<string, number>>('/admin/ops/limits');
    limits = res.data || {};
    if (clearMessages) messages = {};
  } catch {
    // ignore
  }
  listeners.forEach((cb) => cb());
}

export async function refreshLimits() {
  await fetchLimits(true);
}

export async function handleLimit429(limitKey: string, retryAfter?: number) {
  const seconds = typeof retryAfter === 'number' && retryAfter > 0 ? retryAfter : undefined;
  messages[limitKey] = seconds ? `try again in ${seconds}s` : 'rate limited';
  listeners.forEach((cb) => cb());
  await fetchLimits(false);
}

// Internal helpers for a component
export function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function getLimitState(limitKey: string): { value: number | null; message?: string } {
  return { value: limits[limitKey] ?? null, message: messages[limitKey] };
}

export async function ensureFetched(limitKey: string) {
  if (typeof limits[limitKey] === 'undefined') await fetchLimits(true);
}

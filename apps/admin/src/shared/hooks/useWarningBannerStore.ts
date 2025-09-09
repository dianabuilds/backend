import { useSyncExternalStore } from 'react';

let banner: string | null = null;
const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot() {
  return banner;
}

export function setWarningBanner(value: string | null) {
  banner = value;
  listeners.forEach((l) => l());
}

export function useWarningBannerStore(): string | null {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

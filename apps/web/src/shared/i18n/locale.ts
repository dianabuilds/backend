import { useSyncExternalStore } from 'react';

let currentLocale: 'en' | 'ru' = 'ru';

export type Locale = 'en' | 'ru';

type Listener = (locale: Locale) => void;
const listeners = new Set<Listener>();

function notify(locale: Locale) {
  for (const listener of Array.from(listeners)) {
    try {
      listener(locale);
    } catch {
      // ignore listener errors to keep notifications flowing
    }
  }
}

export function setLocale(locale: Locale) {
  const normalized: Locale = locale === 'en' ? 'en' : 'ru';
  if (currentLocale === normalized) return;
  currentLocale = normalized;
  notify(currentLocale);
}

export function getLocale(): Locale {
  return currentLocale;
}

export function subscribeLocale(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useLocale(): Locale {
  return useSyncExternalStore(subscribeLocale, getLocale);
}

export function translate(map: Record<Locale, string>): string {
  return map[currentLocale] ?? map.ru ?? map.en;
}

export function translateWithVars(
  map: Record<Locale, string>,
  vars: Record<string, string | number>,
): string {
  const template = translate(map);
  return template.replace(/{{\s*(\w+)\s*}}/g, (_, key: string) => {
    const value = vars[key];
    return value == null ? '' : String(value);
  });
}

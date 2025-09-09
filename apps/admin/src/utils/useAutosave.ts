import { useCallback, useEffect, useRef, useState } from 'react';

import { safeLocalStorage } from './safeStorage';

/**
 * Generic hook to manage editor state with auto-save capability.
 * @param initial - initial data
 * @param onSave - async save handler invoked on auto-save or manual save
 * @param delay - debounce delay in ms before auto-saving
 */
export function useAutosave<T>(
  initial: T,
  onSave?: (data: T, signal?: AbortSignal) => Promise<void> | void,
  delay = 1000,
  storageKey?: string,
) {
  const [data, setData] = useState<T>(() => {
    if (storageKey) {
      const raw = safeLocalStorage.getItem(storageKey);
      if (raw) {
        try {
          return JSON.parse(raw) as T;
        } catch {
          /* ignore */
        }
      }
    }
    return initial;
  });
  const [saving, setSaving] = useState(false);
  const timer = useRef<number | null>(null);
  const latest = useRef<T>(initial);
  const abortRef = useRef<AbortController | null>(null);

  const save = useCallback(async () => {
    if (!onSave) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setSaving(true);
    try {
      await onSave(latest.current, controller.signal);
      if (storageKey) {
        safeLocalStorage.removeItem(storageKey);
      }
    } catch (e: any) {
      if (e?.name !== 'AbortError') throw e;
    } finally {
      abortRef.current = null;
      setSaving(false);
    }
  }, [onSave, storageKey]);

  const update = useCallback((next: T) => {
    setData(next);
  }, []);

  useEffect(() => {
    latest.current = data;
    if (storageKey) {
      try {
        safeLocalStorage.setItem(storageKey, JSON.stringify(data));
      } catch {
        /* ignore */
      }
    }
    if (!onSave) return;
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      save().catch(() => {});
    }, delay);
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [data, delay, onSave, save, storageKey]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (storageKey && onSave) {
      // propagate loaded data to parent once
      void onSave(latest.current);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { data, update, save, saving, setData };
}

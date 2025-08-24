import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Generic hook to manage editor state with auto-save capability.
 * @param initial - initial data
 * @param onSave - async save handler invoked on auto-save or manual save
 * @param delay - debounce delay in ms before auto-saving
 */
export function useAutosave<T>(
  initial: T,
  onSave?: (data: T) => Promise<void> | void,
  delay = 1000,
  storageKey?: string,
) {
  const [data, setData] = useState<T>(() => {
    if (storageKey && typeof localStorage !== "undefined") {
      const raw = localStorage.getItem(storageKey);
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

  const save = useCallback(async () => {
    if (!onSave) return;
    setSaving(true);
    try {
      await onSave(latest.current);
      if (storageKey && typeof localStorage !== "undefined") {
        localStorage.removeItem(storageKey);
      }
    } finally {
      setSaving(false);
    }
  }, [onSave, storageKey]);

  const update = useCallback((next: T) => {
    setData(next);
  }, []);

  useEffect(() => {
    latest.current = data;
    if (storageKey && typeof localStorage !== "undefined") {
      try {
        localStorage.setItem(storageKey, JSON.stringify(data));
      } catch {
        /* ignore */
      }
    }
    if (!onSave) return;
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      void save();
    }, delay);
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [data, delay, onSave, save, storageKey]);

  useEffect(() => {
    if (storageKey && onSave) {
      // propagate loaded data to parent once
      void onSave(latest.current);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { data, update, save, saving, setData };
}

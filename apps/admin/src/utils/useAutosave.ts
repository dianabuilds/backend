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
) {
  const [data, setData] = useState<T>(initial);
  const [saving, setSaving] = useState(false);
  const timer = useRef<number | null>(null);
  const latest = useRef<T>(initial);

  const save = useCallback(async () => {
    if (!onSave) return;
    setSaving(true);
    try {
      await onSave(latest.current);
    } finally {
      setSaving(false);
    }
  }, [onSave]);

  const update = useCallback((next: T) => {
    setData(next);
  }, []);

  useEffect(() => {
    latest.current = data;
    if (!onSave) return;
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      void save();
    }, delay);
    return () => {
      if (timer.current) window.clearTimeout(timer.current);
    };
  }, [data, delay, onSave, save]);

  return { data, update, save, saving, setData };
}

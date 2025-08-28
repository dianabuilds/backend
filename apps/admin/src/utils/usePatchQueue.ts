import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Queue of patches with debounce and sequential processing.
 */
export function usePatchQueue(
  onPatch: (patch: Record<string, unknown>, signal?: AbortSignal) => Promise<void>,
  delay = 800,
) {
  const queueRef = useRef<Record<string, unknown>[]>([]);
  const [pending, setPending] = useState(0);
  const [saving, setSaving] = useState(false);
  const timerRef = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const processingRef = useRef(false);

  const process = useCallback(async () => {
    if (processingRef.current) return;
    if (queueRef.current.length === 0) return;
    processingRef.current = true;
    const patch = queueRef.current.shift()!;
    setPending(queueRef.current.length);
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setSaving(true);
    try {
      await onPatch(patch, controller.signal);
    } catch {
      // swallow error, state updated by caller
    } finally {
      setSaving(false);
      abortRef.current = null;
      processingRef.current = false;
      if (queueRef.current.length > 0) {
        void process();
      }
    }
  }, [onPatch]);

  const schedule = useCallback(() => {
    if (timerRef.current) window.clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => {
      void process();
    }, delay);
  }, [process, delay]);

  const enqueue = useCallback((patch: Record<string, unknown>) => {
    queueRef.current.push(patch);
    setPending(queueRef.current.length);
    schedule();
  }, [schedule]);

  const flush = useCallback(async () => {
    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    while (queueRef.current.length > 0 || processingRef.current) {
      if (!processingRef.current) {
        await process();
      }
      await new Promise((resolve) => setTimeout(resolve, 0));
    }
  }, [process]);

  // Немедленное сохранение: если есть очередь — flush, иначе "touch" пустым патчем
  const saveNow = useCallback(async () => {
    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (queueRef.current.length > 0 || processingRef.current) {
      await flush();
      return;
    }
    // Пустой патч: сервер обновит updated_at/updated_by, UI покажет "Сохранено"
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setSaving(true);
    try {
      await onPatch({}, controller.signal);
    } catch {
      // swallow; ошибки обработаются в onPatch
    } finally {
      setSaving(false);
      abortRef.current = null;
    }
  }, [flush, onPatch]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, []);

  return { enqueue, flush, saving, pending, saveNow };
}

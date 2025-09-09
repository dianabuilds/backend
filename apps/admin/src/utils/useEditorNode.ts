import { useCallback, useEffect, useRef, useState } from 'react';

import { getNode, patchNode } from '../api/nodes';
import type { NodeOut } from '../openapi';
import { useUnsavedChanges } from './useUnsavedChanges';

/**
 * Hook for editing a node with auto‑save and dirty state tracking.
 * Handles loading, manual saving and debounced auto‑saving.
 */
export function useEditorNode(accountId: string, id: string, autoSaveDelay = 1000) {
  const [data, setData] = useState<NodeOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const baseRef = useRef<NodeOut | null>(null);
  const timer = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useUnsavedChanges(dirty);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const node = await getNode(accountId, id);
      setData(node);
      baseRef.current = node;
      setDirty(false);
    } finally {
      setLoading(false);
    }
  }, [id, accountId]);

  useEffect(() => {
    void load();
  }, [load]);

  const computePatch = useCallback((): Partial<NodeOut> => {
    const current = data;
    const base = baseRef.current;
    const patch: Partial<NodeOut> = {};
    if (!current || !base) return patch;
    for (const key of Object.keys(current) as (keyof NodeOut)[]) {
      const c = current[key];
      const b = base[key];
      if (JSON.stringify(c) !== JSON.stringify(b)) {
        (patch as Record<string, unknown>)[key as string] = c as unknown;
      }
    }
    return patch;
  }, [data]);

  const save = useCallback(async () => {
    if (!data) return;
    const patch = computePatch();
    if (Object.keys(patch).length === 0) {
      setDirty(false);
      return;
    }
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setSaving(true);
    try {
      const updated = await patchNode(accountId, id, patch, {
        signal: controller.signal,
        next: true,
      });
      setData(updated);
      baseRef.current = updated;
      setDirty(false);
    } catch (e: unknown) {
      if ((e as Error).name !== 'AbortError') throw e;
    } finally {
      abortRef.current = null;
      setSaving(false);
    }
  }, [computePatch, data, id, accountId]);

  const scheduleSave = useCallback(() => {
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      void save();
    }, autoSaveDelay);
  }, [save, autoSaveDelay]);

  const update = useCallback((patch: Partial<NodeOut>) => {
    setData((prev) => ({ ...(prev || {}), ...patch }) as NodeOut);
  }, []);

  useEffect(() => {
    const current = data;
    const base = baseRef.current;
    if (!current || !base) return;
    const isDirty = JSON.stringify(current) !== JSON.stringify(base);
    setDirty(isDirty);
    if (isDirty) scheduleSave();
  }, [data, scheduleSave]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  return { data, update, loading, saving, dirty, save, reload: load };
}

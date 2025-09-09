import { useCallback, useEffect, useRef, useState } from 'react';

import { ensureArray } from '../utils';

export function usePaginatedList<T>(
  loader: (params: { limit: number; offset: number }) => Promise<unknown>,
  options?: { initialLimit?: number },
) {
  const { initialLimit = 50 } = options ?? {};
  const [items, setItems] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [limit, setLimit] = useState(initialLimit);
  const [offset, setOffset] = useState(0);

  const loaderRef = useRef(loader);
  useEffect(() => {
    loaderRef.current = loader;
  }, [loader]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await loaderRef.current({ limit, offset });
      setItems(ensureArray<T>(data));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [limit, offset]);

  useEffect(() => {
    void load();
  }, [load]);

  const nextPage = () => setOffset((o) => o + limit);
  const prevPage = () => setOffset((o) => Math.max(0, o - limit));
  const reset = () => setOffset(0);

  return {
    items,
    loading,
    error,
    limit,
    offset,
    setLimit,
    setOffset,
    nextPage,
    prevPage,
    reset,
    hasPrev: offset > 0,
    hasNext: items.length >= limit,
    reload: load,
  };
}

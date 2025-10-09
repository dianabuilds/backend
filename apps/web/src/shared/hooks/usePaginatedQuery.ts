import React from 'react';
import { extractErrorMessage } from '../utils/errors';

type FetcherContext = {
  page: number;
  pageSize: number;
  signal?: AbortSignal;
};

type MapResponseContext = {
  page: number;
  pageSize: number;
};

type PaginatedPayload<TItem> = {
  items: TItem[];
  hasNext: boolean;
  total?: number | null;
};

export type UsePaginatedQueryOptions<TItem, TResponse> = {
  fetcher: (ctx: FetcherContext) => Promise<TResponse>;
  mapResponse: (response: TResponse, ctx: MapResponseContext) => PaginatedPayload<TItem>;
  initialPage?: number;
  initialPageSize?: number;
  debounceMs?: number;
  dependencies?: React.DependencyList;
  onError?: (error: unknown) => string;
};

export type UsePaginatedQueryResult<TItem> = {
  items: TItem[];
  setItems: React.Dispatch<React.SetStateAction<TItem[]>>;
  page: number;
  setPage: (page: number) => void;
  pageSize: number;
  setPageSize: (pageSize: number) => void;
  hasNext: boolean;
  setHasNext: React.Dispatch<React.SetStateAction<boolean>>;
  loading: boolean;
  error: string | null;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  refresh: () => Promise<void>;
};

export function usePaginatedQuery<TItem, TResponse>(
  options: UsePaginatedQueryOptions<TItem, TResponse>,
): UsePaginatedQueryResult<TItem> {
  const {
    fetcher,
    mapResponse,
    dependencies = [],
    initialPage = 1,
    initialPageSize = 20,
    debounceMs = 200,
    onError,
  } = options;

  const fetcherRef = React.useRef(fetcher);
  const mapResponseRef = React.useRef(mapResponse);
  const onErrorRef = React.useRef(onError);

  fetcherRef.current = fetcher;
  mapResponseRef.current = mapResponse;
  onErrorRef.current = onError;

  const [page, setPageState] = React.useState(initialPage);
  const [pageSize, setPageSizeState] = React.useState(initialPageSize);
  const [items, setItems] = React.useState<TItem[]>([]);
  const [hasNext, setHasNext] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const setPage = React.useCallback((next: number) => {
    setPageState((prev) => {
      const normalized = Number.isFinite(next) && next > 0 ? Math.trunc(next) : 1;
      return normalized === prev ? prev : normalized;
    });
  }, []);

  const setPageSize = React.useCallback((next: number) => {
    const normalized = Number.isFinite(next) && next > 0 ? Math.trunc(next) : 1;
    setPageState(1);
    setPageSizeState(normalized);
  }, []);

  const requestIdRef = React.useRef(0);
  const dependenciesRef = React.useRef<React.DependencyList>(dependencies);
  const dependenciesVersionRef = React.useRef(0);

  if (
    dependencies.length !== dependenciesRef.current.length ||
    dependencies.some((dependency, index) => !Object.is(dependency, dependenciesRef.current[index]))
  ) {
    dependenciesRef.current = Array.from(dependencies);
    dependenciesVersionRef.current += 1;
  }
  const dependenciesVersion = dependenciesVersionRef.current;

  const load = React.useCallback(
    async (pageArg: number, pageSizeArg: number, signal?: AbortSignal) => {
      const requestId = ++requestIdRef.current;
      setLoading(true);
      setError(null);
      try {
        const response = await fetcherRef.current({ page: pageArg, pageSize: pageSizeArg, signal });
        if (signal?.aborted || requestId !== requestIdRef.current) return;
        const mapped = mapResponseRef.current(response, { page: pageArg, pageSize: pageSizeArg });
        if (!mapped || !Array.isArray(mapped.items)) {
          setItems([]);
          setHasNext(false);
          return;
        }
        setItems(mapped.items);
        setHasNext(Boolean(mapped.hasNext));
      } catch (err) {
        if ((err as any)?.name === 'AbortError') return;
        if (requestId !== requestIdRef.current) return;
        const message = onErrorRef.current ? onErrorRef.current(err) : extractErrorMessage(err);
        setItems([]);
        setHasNext(false);
        setError(message);
      } finally {
        if (requestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    },
    [],
  );

  React.useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      void load(page, pageSize, controller.signal);
    }, debounceMs);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [page, pageSize, debounceMs, load, dependenciesVersion]);

  const refresh = React.useCallback(async () => {
    await load(page, pageSize);
  }, [load, page, pageSize]);

  return {
    items,
    setItems,
    page,
    setPage,
    pageSize,
    setPageSize,
    hasNext,
    setHasNext,
    loading,
    error,
    setError,
    refresh,
  };
}

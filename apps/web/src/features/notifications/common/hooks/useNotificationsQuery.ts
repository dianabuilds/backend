import React from 'react';
import { extractErrorMessage } from '@shared/utils/errors';

type Fetcher<TData> = (signal: AbortSignal) => Promise<TData>;

export type UseNotificationsQueryOptions<TData> = {
  fetcher: Fetcher<TData>;
  auto?: boolean;
  mapError?: (error: unknown) => string;
  initialData?: TData | null;
};

export type UseNotificationsQueryResult<TData> = {
  data: TData | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  reload: (mode?: 'initial' | 'refresh') => Promise<void>;
  setError: (message: string | null) => void;
};

export function useNotificationsQuery<TData>({
  fetcher,
  auto = true,
  mapError,
  initialData = null,
}: UseNotificationsQueryOptions<TData>): UseNotificationsQueryResult<TData> {
  const fetcherRef = React.useRef(fetcher);
  const mapErrorRef = React.useRef(mapError);
  const abortRef = React.useRef<AbortController | null>(null);
  const mountedRef = React.useRef(true);

  fetcherRef.current = fetcher;
  mapErrorRef.current = mapError;

  const [data, setData] = React.useState<TData | null>(initialData);
  const [loading, setLoading] = React.useState<boolean>(auto);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setErrorState] = React.useState<string | null>(null);

  React.useEffect(() => () => {
    mountedRef.current = false;
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const resolveError = React.useCallback((err: unknown) => {
    if (mapErrorRef.current) {
      return mapErrorRef.current(err);
    }
    return extractErrorMessage(err);
  }, []);

  const reload = React.useCallback(
    async (mode: 'initial' | 'refresh' = 'initial') => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      if (mode === 'initial') {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setErrorState(null);

      try {
        const result = await fetcherRef.current(controller.signal);
        if (controller.signal.aborted || !mountedRef.current) {
          return;
        }
        setData(result);
      } catch (err) {
        if (!controller.signal.aborted && mountedRef.current) {
          const message = resolveError(err);
          setErrorState(message);
          if (mode === 'initial') {
            setData(null);
          }
        }
      } finally {
        const aborted = controller.signal.aborted;
        abortRef.current = null;
        if (!aborted && mountedRef.current) {
          if (mode === 'initial') {
            setLoading(false);
          } else {
            setRefreshing(false);
          }
        }
      }
    },
    [resolveError],
  );

  React.useEffect(() => {
    if (!auto) return;
    void reload('initial');
  }, [auto, reload]);

  const setError = React.useCallback((message: string | null) => {
    setErrorState(message);
  }, []);

  return {
    data,
    loading,
    refreshing,
    error,
    reload,
    setError,
  };
}

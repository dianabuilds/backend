import React from 'react';
import { extractErrorMessage } from '../../shared/utils/errors';

type Fetcher<T> = (signal: AbortSignal) => Promise<T>;

type UseTelemetryQueryOptions<T> = {
  fetcher: Fetcher<T>;
  deps?: React.DependencyList;
  mapError?: (error: unknown) => string;
};

type UseTelemetryQueryResult<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<T | null>;
};

export function useTelemetryQuery<T>({
  fetcher,
  deps = [],
  mapError,
}: UseTelemetryQueryOptions<T>): UseTelemetryQueryResult<T> {
  const fetcherRef = React.useRef(fetcher);
  const mapErrorRef = React.useRef(mapError);

  fetcherRef.current = fetcher;
  mapErrorRef.current = mapError;

  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);
  const requestIdRef = React.useRef(0);

  const resolveError = React.useCallback((err: unknown) => {
    if (mapErrorRef.current) return mapErrorRef.current(err);
    return extractErrorMessage(err);
  }, []);

  const run = React.useCallback(
    async (signal: AbortSignal, silent = false): Promise<T | null> => {
      const requestId = ++requestIdRef.current;
      if (!silent) {
        setLoading(true);
        setError(null);
      }
      try {
        const result = await fetcherRef.current(signal);
        if (signal.aborted || requestId !== requestIdRef.current) return null;
        setData(result);
        setLoading(false);
        return result;
      } catch (err) {
        if (signal.aborted || requestId !== requestIdRef.current) return null;
        setData(null);
        setError(resolveError(err));
        setLoading(false);
        return null;
      }
    },
    [resolveError],
  );

  React.useEffect(() => {
    const controller = new AbortController();
    void run(controller.signal);
    return () => {
      controller.abort();
      requestIdRef.current += 1;
    };
  }, [run, deps]);

  const refresh = React.useCallback(async () => {
    const controller = new AbortController();
    const result = await run(controller.signal);
    controller.abort();
    return result;
  }, [run]);

  return { data, loading, error, refresh };
}

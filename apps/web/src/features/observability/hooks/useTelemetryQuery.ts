import React from 'react';
import { extractErrorMessage } from '@shared/utils/errors';

type Fetcher<T> = (signal: AbortSignal) => Promise<T>;

type UseTelemetryQueryOptions<T> = {
  fetcher: Fetcher<T>;
  deps?: React.DependencyList;
  pollIntervalMs?: number;
  mapError?: (error: unknown) => string;
};

type UseTelemetryQueryResult<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<T | null>;
  lastUpdated: Date | null;
};

export function useTelemetryQuery<T>({
  fetcher,
  deps = [],
  pollIntervalMs,
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
  const [lastUpdated, setLastUpdated] = React.useState<Date | null>(null);
  const pollingTimerRef = React.useRef<number | null>(null);
  const pollingBusyRef = React.useRef(false);
  const dependenciesRef = React.useRef<React.DependencyList>(deps);
  const dependenciesVersionRef = React.useRef(0);

  if (
    deps.length !== dependenciesRef.current.length ||
    deps.some((dependency, index) => !Object.is(dependency, dependenciesRef.current[index]))
  ) {
    dependenciesRef.current = Array.from(deps);
    dependenciesVersionRef.current += 1;
  }
  const dependenciesVersion = dependenciesVersionRef.current;

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
        setLastUpdated(new Date());
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
    if (!pollIntervalMs || pollIntervalMs <= 0) {
      if (pollingTimerRef.current !== null) {
        window.clearInterval(pollingTimerRef.current);
        pollingTimerRef.current = null;
      }
      return undefined;
    }
    const tick = () => {
      if (pollingBusyRef.current) return;
      pollingBusyRef.current = true;
      const controller = new AbortController();
      void run(controller.signal, true).finally(() => {
        controller.abort();
        pollingBusyRef.current = false;
      });
    };
    const id = window.setInterval(tick, pollIntervalMs);
    pollingTimerRef.current = id;
    return () => {
      if (pollingTimerRef.current !== null) {
        window.clearInterval(pollingTimerRef.current);
        pollingTimerRef.current = null;
      }
    };
  }, [run, pollIntervalMs, dependenciesVersion]);

  React.useEffect(() => {
    const controller = new AbortController();
    void run(controller.signal);
    return () => {
      controller.abort();
      requestIdRef.current += 1;
    };
  }, [run, dependenciesVersion]);

  const refresh = React.useCallback(async () => {
    const controller = new AbortController();
    const result = await run(controller.signal);
    controller.abort();
    return result;
  }, [run]);

  return { data, loading, error, refresh, lastUpdated };
}


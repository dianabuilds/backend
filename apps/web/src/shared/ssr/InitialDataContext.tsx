/* eslint-disable react-refresh/only-export-components */
import React from 'react';

export type InitialDataMap = Record<string, unknown>;

type InitialDataContextValue = {
  data: InitialDataMap;
};

const InitialDataContext = React.createContext<InitialDataContextValue>({ data: {} });

type InitialDataProviderProps = {
  data?: InitialDataMap | null;
  children: React.ReactNode;
};

export function InitialDataProvider({ data, children }: InitialDataProviderProps): React.ReactElement {
  const value = React.useMemo<InitialDataContextValue>(() => ({ data: data ? { ...data } : {} }), [data]);
  return <InitialDataContext.Provider value={value}>{children}</InitialDataContext.Provider>;
}

export function useInitialData<T = unknown>(key: string): T | undefined {
  const { data } = React.useContext(InitialDataContext);
  if (!key) return undefined;
  return data[key] as T | undefined;
}

export function mergeInitialData(existing: InitialDataMap | undefined, next: InitialDataMap | null | undefined): InitialDataMap {
  if (!existing && !next) return {};
  if (!existing) return next ? { ...next } : {};
  if (!next) return { ...existing };
  return { ...existing, ...next };
}


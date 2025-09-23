import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

import { apiGet } from '../api/client';
import { useAuth } from '../auth/AuthContext';

type SettingsFeatureMap = Record<string, boolean>;

type SettingsContextValue = {
  isReady: boolean;
  loading: boolean;
  error: string | null;
  features: SettingsFeatureMap;
  schemaVersion: string;
  idempotencyHeader: string;
  reload: () => Promise<void>;
};

const DEFAULT_STATE: SettingsContextValue = {
  isReady: false,
  loading: false,
  error: null,
  features: {},
  schemaVersion: '',
  idempotencyHeader: 'Idempotency-Key',
  reload: async () => {},
};

const SettingsContext = createContext<SettingsContextValue>(DEFAULT_STATE);

async function fetchFeatures(): Promise<{ features: SettingsFeatureMap; schemaVersion: string; idempotencyHeader: string }> {
  const res = await apiGet<any>('/v1/settings/features');
  const features = (res?.features && typeof res.features === 'object') ? (res.features as SettingsFeatureMap) : {};
  const schemaVersion = typeof res?.schema_version === 'string' ? res.schema_version : '';
  const idempotencyHeader = typeof res?.idempotency_header === 'string' ? res.idempotency_header : 'Idempotency-Key';
  return { features, schemaVersion, idempotencyHeader };
}

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isReady: authReady } = useAuth();
  const [state, setState] = useState<SettingsContextValue>(DEFAULT_STATE);
  const loadingRef = useRef(false);

  const load = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    loadingRef.current = true;
    try {
      const { features, schemaVersion, idempotencyHeader } = await fetchFeatures();
      setState({
        isReady: true,
        loading: false,
        error: null,
        features,
        schemaVersion,
        idempotencyHeader,
        reload: async () => {},
      });
    } catch (error: any) {
      setState((prev) => ({
        ...prev,
        isReady: true,
        loading: false,
        error: error?.message || 'Не удалось загрузить настройки',
        features: {},
        schemaVersion: '',
        idempotencyHeader: 'Idempotency-Key',
      }));
    } finally {
      loadingRef.current = false;
    }
  }, []);

  useEffect(() => {
    if (!authReady) return;
    if (!isAuthenticated) {
      setState((prev) => ({
        ...prev,
        isReady: true,
        loading: false,
        error: null,
        features: {},
        schemaVersion: '',
        idempotencyHeader: 'Idempotency-Key',
      }));
      return;
    }
    if (!loadingRef.current) {
      load();
    }
  }, [authReady, isAuthenticated, load]);

  const reload = useCallback(async () => {
    if (!authReady || !isAuthenticated) {
      setState((prev) => ({ ...prev, isReady: authReady, loading: false }));
      return;
    }
    await load();
  }, [authReady, isAuthenticated, load]);

  const value = useMemo<SettingsContextValue>(() => ({
    ...state,
    reload,
  }), [state, reload]);

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings() {
  return useContext(SettingsContext);
}

export function useSettingsFeature(key: string, fallback = false): boolean {
  const ctx = useSettings();
  if (!ctx.isReady) return fallback;
  return key in ctx.features ? Boolean(ctx.features[key]) : fallback;
}

export function useSettingsIdempotencyHeader(): string {
  const ctx = useSettings();
  return ctx.idempotencyHeader || 'Idempotency-Key';
}

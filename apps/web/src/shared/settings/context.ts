import { createContext, useContext } from 'react';

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

function useSettings(): SettingsContextValue {
  return useContext(SettingsContext);
}

function useSettingsFeature(key: string, fallback = false): boolean {
  const ctx = useSettings();
  if (!ctx.isReady) return fallback;
  return key in ctx.features ? Boolean(ctx.features[key]) : fallback;
}

function useSettingsIdempotencyHeader(): string {
  const ctx = useSettings();
  return ctx.idempotencyHeader || 'Idempotency-Key';
}

export { DEFAULT_STATE, SettingsContext, useSettings, useSettingsFeature, useSettingsIdempotencyHeader };
export type { SettingsContextValue, SettingsFeatureMap };

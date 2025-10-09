import * as React from "react";

import {
  fetchManagementAiFallbacks,
  fetchManagementAiModels,
  fetchManagementAiProviders,
  fetchManagementAiSummary
} from "@shared/api";
import type { FallbackRule, LLMSummary, Model, Provider } from "../types";

type LoadOptions = { silent?: boolean };

export type UseManagementAiState = {
  models: Model[];
  providers: Provider[];
  fallbacks: FallbackRule[];
  metrics: LLMSummary | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  loadAll: (opts?: LoadOptions) => Promise<void>;
  setModels: React.Dispatch<React.SetStateAction<Model[]>>;
  setProviders: React.Dispatch<React.SetStateAction<Provider[]>>;
  setFallbacks: React.Dispatch<React.SetStateAction<FallbackRule[]>>;
  setMetrics: React.Dispatch<React.SetStateAction<LLMSummary | null>>;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
};

export function useManagementAi(): UseManagementAiState {
  const [models, setModels] = React.useState<Model[]>([]);
  const [providers, setProviders] = React.useState<Provider[]>([]);
  const [fallbacks, setFallbacks] = React.useState<FallbackRule[]>([]);
  const [metrics, setMetrics] = React.useState<LLMSummary | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadAll = React.useCallback(async (opts?: LoadOptions) => {
    if (opts?.silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    const [modelsRes, providersRes, metricsRes, fallbacksRes] = await Promise.allSettled([
      fetchManagementAiModels(),
      fetchManagementAiProviders(),
      fetchManagementAiSummary(),
      fetchManagementAiFallbacks(),
    ]);

    const failed: string[] = [];

    if (modelsRes.status === 'fulfilled') {
      setModels(modelsRes.value ?? []);
    } else {
      failed.push('модели');
    }

    if (providersRes.status === 'fulfilled') {
      setProviders(providersRes.value ?? []);
    } else {
      failed.push('провайдеры');
    }

    if (metricsRes.status === 'fulfilled') {
      setMetrics(metricsRes.value ?? null);
    } else {
      failed.push('метрики');
    }

    if (fallbacksRes.status === 'fulfilled') {
      setFallbacks(fallbacksRes.value ?? []);
    } else {
      failed.push('fallback-правила');
    }

    if (failed.length) {
      const message =
        failed.length > 2
          ? 'Не удалось загрузить часть данных. Повторите обновление или проверьте соединение.'
          : `Не удалось обновить: ${failed.join(', ')}`;
      setError(message);
    } else {
      setError(null);
    }

    if (opts?.silent) {
      setRefreshing(false);
    } else {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadAll();
  }, [loadAll]);

  return {
    models,
    providers,
    fallbacks,
    metrics,
    loading,
    refreshing,
    error,
    loadAll,
    setModels,
    setProviders,
    setFallbacks,
    setMetrics,
    setError,
  };
}



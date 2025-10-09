import * as React from 'react';

import {
  deleteBillingPlan,
  fetchBillingMetrics,
  fetchBillingPlanHistory,
  fetchBillingPlans,
  saveBillingPlan,
  updateBillingPlanLimits,
} from '@shared/api/management';
import { extractErrorMessage } from '@shared/utils/errors';
import type {
  BillingMetrics,
  BillingPlan,
  BillingPlanHistoryItem,
  BillingPlanLimitsUpdate,
  BillingPlanPayload,
} from '@shared/types/management';

const DEFAULT_METRICS: BillingMetrics = {
  active_subs: 0,
  mrr: 0,
  arpu: 0,
  churn_30d: 0,
};

export type UseManagementTariffsOptions = {
  auto?: boolean;
};

export type UseManagementTariffsResult = {
  loading: boolean;
  error: string | null;
  metrics: BillingMetrics;
  plans: BillingPlan[];
  history: BillingPlanHistoryItem[];
  refresh: () => Promise<void>;
  clearError: () => void;
  savePlan: (payload: BillingPlanPayload) => Promise<void>;
  deletePlan: (id: string) => Promise<void>;
  updatePlanLimits: (items: BillingPlanLimitsUpdate[]) => Promise<void>;
  loadPlanHistory: (slug: string) => Promise<void>;
};

export function useManagementTariffs(
  { auto = true }: UseManagementTariffsOptions = {},
): UseManagementTariffsResult {
  const [loading, setLoading] = React.useState<boolean>(auto);
  const [error, setError] = React.useState<string | null>(null);
  const [metrics, setMetrics] = React.useState<BillingMetrics>(DEFAULT_METRICS);
  const [plans, setPlans] = React.useState<BillingPlan[]>([]);
  const [history, setHistory] = React.useState<BillingPlanHistoryItem[]>([]);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);

    const results = await Promise.allSettled([fetchBillingMetrics(), fetchBillingPlans()]);
    const [metricsResult, plansResult] = results;

    if (metricsResult.status === 'fulfilled') {
      setMetrics(metricsResult.value ?? DEFAULT_METRICS);
    } else {
      setMetrics(DEFAULT_METRICS);
    }

    if (plansResult.status === 'fulfilled') {
      setPlans(Array.isArray(plansResult.value) ? plansResult.value : []);
    } else {
      setPlans([]);
    }

    const message = results
      .filter((result) => result.status === 'rejected')
      .map((result) => extractErrorMessage((result as PromiseRejectedResult).reason, 'РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ С‚Р°СЂРёС„С‹.'))
      .shift();

    setError(message ?? null);
    setLoading(false);
  }, []);

  React.useEffect(() => {
    if (!auto) return;
    void refresh();
  }, [auto, refresh]);

  const savePlan = React.useCallback(
    async (payload: BillingPlanPayload) => {
      await saveBillingPlan(payload);
      await refresh();
    },
    [refresh],
  );

  const deletePlan = React.useCallback(
    async (id: string) => {
      await deleteBillingPlan(id);
      await refresh();
    },
    [refresh],
  );

  const updatePlanLimits = React.useCallback(
    async (items: BillingPlanLimitsUpdate[]) => {
      await updateBillingPlanLimits(items);
      await refresh();
    },
    [refresh],
  );

  const loadPlanHistory = React.useCallback(async (slug: string) => {
    try {
      const items = await fetchBillingPlanHistory(slug);
      setHistory(Array.isArray(items) ? items : []);
    } catch (err) {
      setError(extractErrorMessage(err, 'РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РёСЃС‚РѕСЂРёСЋ С‚Р°СЂРёС„РЅРѕРіРѕ РїР»Р°РЅР°.'));
      setHistory([]);
    }
  }, []);

  const clearError = React.useCallback(() => setError(null), []);

  return {
    loading,
    error,
    metrics,
    plans,
    history,
    refresh,
    clearError,
    savePlan,
    deletePlan,
    updatePlanLimits,
    loadPlanHistory,
  };
}

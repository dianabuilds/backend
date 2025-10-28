import * as React from 'react';

import {
  fetchBillingOverview,
  fetchBillingOverviewPayouts,
} from '@shared/api/management';
import { extractErrorMessage } from '@shared/utils/errors';
import type {
  BillingOverviewResponse,
  BillingPayout,
} from '@shared/types/management';

type UseBillingOverviewOptions = {
  auto?: boolean;
  payoutStatus?: string;
  payoutLimit?: number;
};

type UseBillingOverviewResult = {
  loading: boolean;
  error: string | null;
  overview: BillingOverviewResponse;
  previousOverview: BillingOverviewResponse | null;
  payouts: BillingPayout[];
  refresh: () => Promise<void>;
  clearError: () => void;
};

const DEFAULT_OVERVIEW: BillingOverviewResponse = {
  kpi: {
    success: 0,
    errors: 0,
    pending: 0,
    volume_cents: 0,
    avg_confirm_ms: 0,
    contracts: {
      total: 0,
      enabled: 0,
      disabled: 0,
      testnet: 0,
      mainnet: 0,
    },
  },
  subscriptions: {
    active_subs: 0,
    mrr: 0,
    arpu: 0,
    churn_30d: 0,
    tokens: [],
    networks: [],
  },
  revenue: [],
};

export function useBillingOverview(
  { auto = true, payoutStatus = 'failed', payoutLimit = 25 }: UseBillingOverviewOptions = {},
): UseBillingOverviewResult {
  const [loading, setLoading] = React.useState<boolean>(auto);
  const [error, setError] = React.useState<string | null>(null);
  const [overview, setOverview] = React.useState<BillingOverviewResponse>(DEFAULT_OVERVIEW);
  const [previousOverview, setPreviousOverview] = React.useState<BillingOverviewResponse | null>(null);
  const [payouts, setPayouts] = React.useState<BillingPayout[]>([]);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);

    const results = await Promise.allSettled([
      fetchBillingOverview(),
      fetchBillingOverviewPayouts({ status: payoutStatus, limit: payoutLimit }),
    ]);

    const [overviewResult, payoutsResult] = results;

    if (overviewResult.status === 'fulfilled') {
      setPreviousOverview(overview);
      setOverview(overviewResult.value);
    } else {
      setOverview(DEFAULT_OVERVIEW);
    }

    if (payoutsResult.status === 'fulfilled') {
      setPayouts(Array.isArray(payoutsResult.value) ? payoutsResult.value : []);
    } else {
      setPayouts([]);
    }

    const message = results
      .filter((result) => result.status === 'rejected')
      .map((result) =>
        extractErrorMessage(
          (result as PromiseRejectedResult).reason,
          'Не удалось загрузить биллинг-обзор.',
        ),
      )
      .shift();

    setError(message ?? null);
    setLoading(false);
  }, [overview, payoutLimit, payoutStatus]);

  React.useEffect(() => {
    if (!auto) return;
    void refresh();
  }, [auto, refresh]);

  const clearError = React.useCallback(() => setError(null), []);

  return {
    loading,
    error,
    overview,
    previousOverview,
    payouts,
    refresh,
    clearError,
  };
}

export type { UseBillingOverviewOptions, UseBillingOverviewResult };

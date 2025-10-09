import * as React from 'react';

import {
  deleteBillingContract,
  deleteBillingProvider,
  fetchBillingContractEvents,
  fetchBillingContracts,
  fetchBillingCryptoConfig,
  fetchBillingKpi,
  fetchBillingProviders,
  fetchBillingTransactions,
  saveBillingContract,
  saveBillingProvider,
  updateBillingCryptoConfig,
} from '@shared/api/management';
import { extractErrorMessage } from '@shared/utils/errors';
import type {
  BillingContract,
  BillingContractEvent,
  BillingContractPayload,
  BillingCryptoConfig,
  BillingKpi,
  BillingProvider,
  BillingProviderPayload,
  BillingTransaction,
} from '@shared/types/management';

const DEFAULT_KPI: BillingKpi = {
  success: 0,
  errors: 0,
  volume_cents: 0,
  avg_confirm_ms: 0,
};

const DEFAULT_CRYPTO_CONFIG: BillingCryptoConfig = {
  rpc_endpoints: {},
  retries: 0,
  gas_price_cap: null,
  fallback_networks: {},
};

export type UseManagementPaymentsOptions = {
  auto?: boolean;
};

export type UseManagementPaymentsResult = {
  loading: boolean;
  error: string | null;
  kpi: BillingKpi;
  providers: BillingProvider[];
  transactions: BillingTransaction[];
  contracts: BillingContract[];
  contractEvents: BillingContractEvent[];
  cryptoConfig: BillingCryptoConfig;
  refresh: () => Promise<void>;
  clearError: () => void;
  saveProvider: (payload: BillingProviderPayload) => Promise<void>;
  deleteProvider: (slug: string) => Promise<void>;
  saveContract: (payload: BillingContractPayload) => Promise<void>;
  deleteContract: (id: string) => Promise<void>;
  updateCryptoConfig: (payload: BillingCryptoConfig) => Promise<void>;
};

function pickValue<T>(result: PromiseSettledResult<T>, fallback: T): T {
  if (result.status === 'fulfilled') {
    const value = result.value;
    if (value === undefined || value === null) {
      return fallback;
    }
    return value;
  }
  return fallback;
}

function firstErrorMessage(
  results: Array<PromiseSettledResult<unknown>>,
  defaultMessage: string,
): string | null {
  for (const result of results) {
    if (result.status === 'rejected') {
      return extractErrorMessage(result.reason, defaultMessage);
    }
  }
  return null;
}

export function useManagementPayments(
  { auto = true }: UseManagementPaymentsOptions = {},
): UseManagementPaymentsResult {
  const [loading, setLoading] = React.useState<boolean>(auto);
  const [error, setError] = React.useState<string | null>(null);
  const [kpi, setKpi] = React.useState<BillingKpi>(DEFAULT_KPI);
  const [providers, setProviders] = React.useState<BillingProvider[]>([]);
  const [transactions, setTransactions] = React.useState<BillingTransaction[]>([]);
  const [contracts, setContracts] = React.useState<BillingContract[]>([]);
  const [contractEvents, setContractEvents] = React.useState<BillingContractEvent[]>([]);
  const [cryptoConfig, setCryptoConfig] = React.useState<BillingCryptoConfig>(DEFAULT_CRYPTO_CONFIG);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);

    const results = await Promise.allSettled([
      fetchBillingKpi(),
      fetchBillingProviders(),
      fetchBillingTransactions({ limit: 200 }),
      fetchBillingContracts(),
      fetchBillingContractEvents({ limit: 100 }),
      fetchBillingCryptoConfig(),
    ]);

    const [
      kpiResult,
      providersResult,
      transactionsResult,
      contractsResult,
      eventsResult,
      cryptoResult,
    ] = results;

    setKpi(pickValue(kpiResult as PromiseSettledResult<BillingKpi>, DEFAULT_KPI));
    setProviders(pickValue(providersResult as PromiseSettledResult<BillingProvider[]>, []));
    setTransactions(pickValue(transactionsResult as PromiseSettledResult<BillingTransaction[]>, []));
    setContracts(pickValue(contractsResult as PromiseSettledResult<BillingContract[]>, []));
    setContractEvents(pickValue(eventsResult as PromiseSettledResult<BillingContractEvent[]>, []));
    setCryptoConfig(pickValue(cryptoResult as PromiseSettledResult<BillingCryptoConfig>, DEFAULT_CRYPTO_CONFIG));

    const message = firstErrorMessage(results, 'Не удалось загрузить данные платежного управления.');
    setError(message);
    setLoading(false);
  }, []);

  React.useEffect(() => {
    if (!auto) return;
    void refresh();
  }, [auto, refresh]);

  const saveProvider = React.useCallback(
    async (payload: BillingProviderPayload) => {
      await saveBillingProvider(payload);
      await refresh();
    },
    [refresh],
  );

  const deleteProvider = React.useCallback(
    async (slug: string) => {
      await deleteBillingProvider(slug);
      await refresh();
    },
    [refresh],
  );

  const saveContract = React.useCallback(
    async (payload: BillingContractPayload) => {
      await saveBillingContract(payload);
      await refresh();
    },
    [refresh],
  );

  const deleteContract = React.useCallback(
    async (id: string) => {
      await deleteBillingContract(id);
      await refresh();
    },
    [refresh],
  );

  const updateCrypto = React.useCallback(
    async (payload: BillingCryptoConfig) => {
      await updateBillingCryptoConfig(payload);
      const updated = await fetchBillingCryptoConfig();
      setCryptoConfig(updated ?? DEFAULT_CRYPTO_CONFIG);
    },
    [],
  );

  const clearError = React.useCallback(() => setError(null), []);

  return {
    loading,
    error,
    kpi,
    providers,
    transactions,
    contracts,
    contractEvents,
    cryptoConfig,
    refresh,
    clearError,
    saveProvider,
    deleteProvider,
    saveContract,
    deleteContract,
    updateCryptoConfig: updateCrypto,
  };
}

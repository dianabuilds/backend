import { apiDelete, apiGet, apiPost } from '../client';
import type {
  BillingContract,
  BillingContractEvent,
  BillingContractPayload,
  BillingCryptoConfig,
  BillingKpi,
  BillingProvider,
  BillingProviderPayload,
  BillingTransaction,
  BillingMetrics,
  BillingPlan,
  BillingPlanHistoryItem,
  BillingPlanLimitsUpdate,
  BillingPlanPayload,
} from '../../types/management';

export async function fetchBillingKpi(): Promise<BillingKpi> {
  const data = await apiGet<BillingKpi>('/v1/billing/admin/kpi');
  return {
    success: Number(data?.success ?? 0),
    errors: Number(data?.errors ?? 0),
    volume_cents: Number(data?.volume_cents ?? 0),
    avg_confirm_ms: Number(data?.avg_confirm_ms ?? 0),
  };
}

export async function fetchBillingProviders(): Promise<BillingProvider[]> {
  const response = await apiGet<{ items?: BillingProvider[] }>('/v1/billing/admin/providers');
  return Array.isArray(response?.items) ? response.items : [];
}

export async function saveBillingProvider(payload: BillingProviderPayload): Promise<void> {
  await apiPost('/v1/billing/admin/providers', payload);
}

export async function deleteBillingProvider(slug: string): Promise<void> {
  await apiDelete(`/v1/billing/admin/providers/${encodeURIComponent(slug)}`);
}

type TransactionParams = {
  limit?: number;
};

export async function fetchBillingTransactions({ limit = 200 }: TransactionParams = {}): Promise<BillingTransaction[]> {
  const response = await apiGet<{ items?: BillingTransaction[] }>(`/v1/billing/admin/transactions?limit=${encodeURIComponent(String(limit))}`);
  return Array.isArray(response?.items) ? response.items : [];
}

export async function fetchBillingContracts(): Promise<BillingContract[]> {
  const response = await apiGet<{ items?: BillingContract[] }>('/v1/billing/admin/contracts');
  return Array.isArray(response?.items) ? response.items : [];
}

export async function saveBillingContract(payload: BillingContractPayload): Promise<void> {
  await apiPost('/v1/billing/admin/contracts', payload);
}

export async function deleteBillingContract(id: string): Promise<void> {
  await apiDelete(`/v1/billing/admin/contracts/${encodeURIComponent(id)}`);
}

type ContractEventsParams = {
  limit?: number;
  contractIdOrSlug?: string;
  signal?: AbortSignal;
};

export async function fetchBillingContractEvents({ limit = 100, contractIdOrSlug, signal }: ContractEventsParams = {}): Promise<BillingContractEvent[]> {
  const params = new URLSearchParams();
  if (limit != null) {
    params.set('limit', String(limit));
  }
  const base = contractIdOrSlug
    ? `/v1/billing/admin/contracts/${encodeURIComponent(contractIdOrSlug)}/events`
    : '/v1/billing/admin/contracts/events';
  const query = params.toString();
  const response = await apiGet<{ items?: BillingContractEvent[] }>(query ? `${base}?${query}` : base, { signal });
  return Array.isArray(response?.items) ? response.items : [];
}

export async function fetchBillingCryptoConfig(): Promise<BillingCryptoConfig> {
  const response = await apiGet<{ config?: BillingCryptoConfig }>('/v1/billing/admin/crypto-config');
  const config = response?.config;
  return {
    rpc_endpoints: (config?.rpc_endpoints && typeof config.rpc_endpoints === 'object') ? config.rpc_endpoints : {},
    retries: Number(config?.retries ?? 0),
    gas_price_cap: config?.gas_price_cap === null || config?.gas_price_cap === undefined ? null : Number(config.gas_price_cap),
    fallback_networks: (config?.fallback_networks && typeof config.fallback_networks === 'object') ? config.fallback_networks : {},
  };
}

export async function updateBillingCryptoConfig(config: BillingCryptoConfig): Promise<void> {
  await apiPost('/v1/billing/admin/crypto-config', config);
}

export async function fetchBillingMetrics(): Promise<BillingMetrics> {
  const data = await apiGet<Partial<BillingMetrics>>('/v1/billing/admin/metrics');
  return {
    active_subs: Number(data?.active_subs ?? 0),
    mrr: Number(data?.mrr ?? 0),
    arpu: Number(data?.arpu ?? 0),
    churn_30d: Number(data?.churn_30d ?? 0),
  };
}

export async function fetchBillingPlans(): Promise<BillingPlan[]> {
  const response = await apiGet<{ items?: BillingPlan[] }>('/v1/billing/admin/plans/all');
  return Array.isArray(response?.items) ? response.items : [];
}

export async function saveBillingPlan(payload: BillingPlanPayload): Promise<void> {
  await apiPost('/v1/billing/admin/plans', payload);
}

export async function deleteBillingPlan(id: string): Promise<void> {
  await apiDelete(`/v1/billing/admin/plans/${encodeURIComponent(id)}`);
}

export async function updateBillingPlanLimits(items: BillingPlanLimitsUpdate[]): Promise<void> {
  await apiPost('/v1/billing/admin/plans/bulk_limits', { items });
}

export async function fetchBillingPlanHistory(slug: string): Promise<BillingPlanHistoryItem[]> {
  const response = await apiGet<{ items?: BillingPlanHistoryItem[] }>(`/v1/billing/admin/plans/${encodeURIComponent(slug)}/audit?limit=100`);
  return Array.isArray(response?.items) ? response.items : [];
}

export const managementApi = {
  fetchBillingKpi,
  fetchBillingProviders,
  saveBillingProvider,
  deleteBillingProvider,
  fetchBillingTransactions,
  fetchBillingContracts,
  saveBillingContract,
  deleteBillingContract,
  fetchBillingContractEvents,
  fetchBillingCryptoConfig,
  updateBillingCryptoConfig,
  fetchBillingMetrics,
  fetchBillingPlans,
  saveBillingPlan,
  deleteBillingPlan,
  updateBillingPlanLimits,
  fetchBillingPlanHistory,
};


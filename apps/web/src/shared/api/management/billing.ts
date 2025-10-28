import { apiDelete, apiGet, apiPost } from '../client';
import type {
  BillingContract,
  BillingContractEvent,
  BillingContractPayload,
  BillingCryptoConfig,
  BillingKpi,
  BillingKpiContracts,
  BillingMetrics,
  BillingMetricsNetworkBreakdown,
  BillingMetricsTokenBreakdown,
  BillingOverviewResponse,
  BillingPlan,
  BillingPlanHistoryItem,
  BillingPlanLimitsUpdate,
  BillingPlanPayload,
  BillingProvider,
  BillingProviderPayload,
  BillingTransaction,
  BillingPayout,
} from '../../types/management';

type RawOverviewResponse = {
  kpi?: Partial<BillingKpi> | { [key: string]: unknown } | null;
  subscriptions?: (Partial<BillingMetrics> & {
    tokens?: unknown;
    networks?: unknown;
  }) | null;
  revenue?: unknown;
};

const DEFAULT_KPI: BillingKpi = {
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
};

const DEFAULT_METRICS: BillingMetrics = {
  active_subs: 0,
  mrr: 0,
  arpu: 0,
  churn_30d: 0,
  tokens: [],
  networks: [],
};

const asNumber = (value: unknown, fallback = 0): number => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const normalizeContracts = (input: unknown): BillingKpiContracts | null => {
  if (!input || typeof input !== 'object') {
    return null;
  }
  const value = input as Record<string, unknown>;
  const normalized: BillingKpiContracts = {
    total: asNumber(value.total),
    enabled: asNumber(value.enabled),
    disabled: asNumber(value.disabled),
    testnet: asNumber(value.testnet),
    mainnet: asNumber(value.mainnet),
  };
  const hasData = Object.values(normalized).some((item) => item !== 0);
  return hasData ? normalized : null;
};

const normalizeKpi = (raw: RawOverviewResponse['kpi']): BillingKpi => ({
  ...DEFAULT_KPI,
  success: asNumber((raw as BillingKpi)?.success),
  errors: asNumber((raw as BillingKpi)?.errors),
  pending: asNumber((raw as BillingKpi)?.pending),
  volume_cents: asNumber((raw as BillingKpi)?.volume_cents),
  avg_confirm_ms: asNumber((raw as BillingKpi)?.avg_confirm_ms),
  contracts: normalizeContracts((raw as BillingKpi)?.contracts) ?? DEFAULT_KPI.contracts,
});

const normalizeTokenBreakdown = (item: unknown): BillingMetricsTokenBreakdown | null => {
  if (!item || typeof item !== 'object') {
    return null;
  }
  const source = item as Record<string, unknown>;
  const token = String(source.token ?? '').trim() || 'USD';
  return {
    token,
    total: asNumber(source.total),
    mrr_usd: asNumber(source.mrr_usd),
  };
};

const normalizeNetworkBreakdown = (item: unknown): BillingMetricsNetworkBreakdown | null => {
  if (!item || typeof item !== 'object') {
    return null;
  }
  const source = item as Record<string, unknown>;
  const network = String(source.network ?? '').trim();
  if (!network) {
    return null;
  }
  return {
    network,
    chain_id: source.chain_id != null ? String(source.chain_id) : null,
    total: asNumber(source.total),
  };
};

const normalizeMetrics = (raw: RawOverviewResponse['subscriptions']): BillingMetrics => {
  const tokensRaw = Array.isArray(raw?.tokens) ? raw?.tokens : [];
  const networksRaw = Array.isArray(raw?.networks) ? raw?.networks : [];
  return {
    ...DEFAULT_METRICS,
    active_subs: asNumber(raw?.active_subs),
    mrr: asNumber(raw?.mrr),
    arpu: asNumber(raw?.arpu),
    churn_30d: asNumber(raw?.churn_30d),
    tokens: tokensRaw
      .map((item) => normalizeTokenBreakdown(item))
      .filter((item): item is BillingMetricsTokenBreakdown => Boolean(item)),
    networks: networksRaw
      .map((item) => normalizeNetworkBreakdown(item))
      .filter((item): item is BillingMetricsNetworkBreakdown => Boolean(item)),
  };
};

const normalizeRevenue = (raw: RawOverviewResponse['revenue']) => {
  if (!Array.isArray(raw)) {
    return [];
  }
  return raw
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null;
      }
      const value = item as Record<string, unknown>;
      const day = typeof value.day === 'string' ? value.day : null;
      if (!day) {
        return null;
      }
      return {
        day,
        amount: asNumber(value.amount),
      };
    })
    .filter((item): item is { day: string; amount: number } => Boolean(item));
};

export async function fetchBillingOverview(): Promise<BillingOverviewResponse> {
  const data = await apiGet<RawOverviewResponse>('/v1/billing/overview/dashboard');
  return {
    kpi: normalizeKpi(data?.kpi ?? null),
    subscriptions: normalizeMetrics(data?.subscriptions ?? null),
    revenue: normalizeRevenue(data?.revenue ?? []),
  };
}

export async function fetchBillingKpi(): Promise<BillingKpi> {
  const { kpi } = await fetchBillingOverview();
  return kpi;
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

export type BillingTransactionsParams = {
  limit?: number;
  status?: string;
  provider?: string;
  contract?: string;
  network?: string;
  from?: string;
  to?: string;
  min_amount?: number;
  max_amount?: number;
};

const buildTransactionsQuery = (params: BillingTransactionsParams = {}) => {
  const search = new URLSearchParams();
  if (params.limit != null) search.set('limit', String(params.limit));
  if (params.status) search.set('status', params.status);
  if (params.provider) search.set('provider', params.provider);
  if (params.contract) search.set('contract', params.contract);
  if (params.network) search.set('network', params.network);
  if (params.from) search.set('from', params.from);
  if (params.to) search.set('to', params.to);
  if (typeof params.min_amount === 'number') search.set('min_amount', String(params.min_amount));
  if (typeof params.max_amount === 'number') search.set('max_amount', String(params.max_amount));
  return search.toString();
};

export async function fetchBillingTransactions(params: BillingTransactionsParams = {}): Promise<BillingTransaction[]> {
  const query = buildTransactionsQuery({ limit: params.limit ?? 200, ...params });
  const response = await apiGet<{ items?: BillingTransaction[] }>(
    query ? `/v1/billing/admin/transactions?${query}` : '/v1/billing/admin/transactions',
  );
  return Array.isArray(response?.items) ? response.items : [];
}

type OverviewPayoutParams = {
  status?: string;
  limit?: number;
};

export async function fetchBillingOverviewPayouts({ status, limit = 25 }: OverviewPayoutParams = {}): Promise<BillingPayout[]> {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  if (limit != null) params.set('limit', String(limit));
  const query = params.toString();
  const response = await apiGet<{ items?: BillingPayout[] }>(query ? `/v1/billing/overview/payouts?${query}` : '/v1/billing/overview/payouts');
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
  const response = await apiGet<{ config?: BillingCryptoConfig }>('/v1/billing/overview/crypto-config');
  const config = response?.config;
  return {
    rpc_endpoints: (config?.rpc_endpoints && typeof config.rpc_endpoints === 'object') ? config.rpc_endpoints : {},
    retries: Number(config?.retries ?? 0),
    gas_price_cap: config?.gas_price_cap === null || config?.gas_price_cap === undefined ? null : Number(config.gas_price_cap),
    fallback_networks: (config?.fallback_networks && typeof config.fallback_networks === 'object') ? config.fallback_networks : {},
  };
}

export async function updateBillingCryptoConfig(config: BillingCryptoConfig): Promise<void> {
  await apiPost('/v1/billing/overview/crypto-config', config);
}

export async function fetchBillingMetrics(): Promise<BillingMetrics> {
  const { subscriptions } = await fetchBillingOverview();
  return subscriptions;
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
  fetchBillingOverview,
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

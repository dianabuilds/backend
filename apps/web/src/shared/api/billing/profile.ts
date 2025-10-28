import { apiGet } from '../client';

export interface BillingGasInfo {
  used?: number | null;
  limit?: number | null;
  price?: number | null;
  fee?: number | null;
  token?: string | null;
  currency?: string | null;
  unit?: string | null;
  note?: string | null;
}

export interface BillingHistoryItem {
  id?: string;
  status?: string;
  created_at?: string;
  confirmed_at?: string | null;
  amount?: number | null;
  amount_cents?: number | null;
  currency?: string | null;
  token?: string | null;
  network?: string | null;
  tx_hash?: string | null;
  provider?: string | null;
  product_type?: string | null;
  failure_reason?: string | null;
  gas?: BillingGasInfo | null;
}

export interface BillingSummary {
  plan: {
    id: string;
    slug: string;
    title: string;
    price_cents: number | null;
    currency: string | null;
    features?: Record<string, unknown> | null;
  } | null;
  subscription: {
    plan_id: string;
    status: string;
    auto_renew: boolean;
    started_at: string;
    ends_at?: string | null;
  } | null;
  payment: {
    mode: string;
    title: string;
    message: string;
    coming_soon?: boolean;
    status?: string;
  };
  wallet?: {
    address?: string | null;
    chain_id?: string | null;
    verified_at?: string | null;
    is_verified?: boolean;
    status?: string | null;
  } | null;
  debt?: {
    amount_cents?: number | null;
    amount?: number | null;
    currency?: string | null;
    is_overdue?: boolean;
    transactions?: number;
    last_issue?: BillingHistoryItem | null;
  } | null;
  last_payment?: BillingHistoryItem | null;
}

export interface BillingHistoryResponse {
  items: BillingHistoryItem[];
  coming_soon?: boolean;
}

type HistoryParams = {
  limit?: number;
  signal?: AbortSignal;
};

export async function fetchBillingSummary(signal?: AbortSignal): Promise<BillingSummary> {
  return apiGet<BillingSummary>('/v1/billing/me/summary', { signal });
}

export async function fetchBillingHistory(
  { limit = 10, signal }: HistoryParams = {},
): Promise<BillingHistoryResponse> {
  const params = new URLSearchParams();
  if (limit != null) {
    params.set('limit', String(limit));
  }
  const query = params.toString();
  const endpoint = query ? `/v1/billing/me/history?${query}` : '/v1/billing/me/history';
  return apiGet<BillingHistoryResponse>(endpoint, { signal });
}


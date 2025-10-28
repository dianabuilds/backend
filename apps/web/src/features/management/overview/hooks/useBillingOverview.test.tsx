import { renderHook, act } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  fetchBillingOverview,
  fetchBillingOverviewPayouts,
} from '@shared/api/management';

vi.mock('@shared/api/management', () => ({
  fetchBillingOverview: vi.fn(),
  fetchBillingOverviewPayouts: vi.fn(),
}));

import { useBillingOverview } from './useBillingOverview';

const mockedFetchOverview = vi.mocked(fetchBillingOverview);
const mockedFetchPayouts = vi.mocked(fetchBillingOverviewPayouts);

const mockOverview = {
  kpi: {
    success: 3,
    errors: 1,
    pending: 2,
    volume_cents: 1200,
    avg_confirm_ms: 80,
    contracts: { total: 2, enabled: 1, disabled: 1, testnet: 0, mainnet: 2 },
  },
  subscriptions: {
    active_subs: 5,
    mrr: 50,
    arpu: 10,
    churn_30d: 0.1,
    tokens: [{ token: 'usdc', total: 2, mrr_usd: 20 }],
    networks: [{ network: 'polygon', chain_id: '137', total: 2 }],
  },
  revenue: [{ day: '2024-01-01', amount: 42 }],
};

const mockPayouts = [
  { id: 'p1', status: 'failed', gross_cents: 500 },
  { id: 'p2', status: 'pending', gross_cents: 200 },
];

describe('useBillingOverview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedFetchOverview.mockResolvedValue(mockOverview as any);
    mockedFetchPayouts.mockResolvedValue(mockPayouts as any);
  });

  it('loads overview and payouts on refresh', async () => {
    const { result } = renderHook(() => useBillingOverview({ auto: false }));

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockedFetchOverview).toHaveBeenCalledTimes(1);
    expect(mockedFetchPayouts).toHaveBeenCalledWith({ status: 'failed', limit: 25 });
    expect(result.current.overview).toEqual(mockOverview);
    expect(result.current.payouts).toEqual(mockPayouts);
    expect(result.current.error).toBeNull();
  });

  it('exposes refresh method', async () => {
    const { result } = renderHook(() => useBillingOverview({ auto: false }));

    await act(async () => {
      await result.current.refresh();
    });

    mockedFetchOverview.mockResolvedValue({
      ...mockOverview,
      kpi: { ...mockOverview.kpi, success: 7 },
    } as any);

    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.overview.kpi.success).toBe(7);
  });

  it('captures errors from overview request', async () => {
    mockedFetchOverview.mockRejectedValueOnce(new Error('network down'));

    const { result } = renderHook(() => useBillingOverview({ auto: false }));

    await act(async () => {
      await result.current.refresh();
    });

    expect(result.current.error).toBe('network down');
    expect(result.current.overview.kpi.success).toBe(0);
  });

  it('allows custom payout filters', async () => {
    const { result } = renderHook(() =>
      useBillingOverview({ auto: false, payoutStatus: 'pending', payoutLimit: 10 }),
    );

    expect(mockedFetchOverview).not.toHaveBeenCalled();

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockedFetchPayouts).toHaveBeenCalledWith({ status: 'pending', limit: 10 });
  });
});

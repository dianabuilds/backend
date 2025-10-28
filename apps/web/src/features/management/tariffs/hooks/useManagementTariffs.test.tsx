import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';

import {
  fetchBillingMetrics,
  fetchBillingPlans,
  fetchBillingPlanHistory,
  saveBillingPlan,
  deleteBillingPlan,
  updateBillingPlanLimits,
} from '@shared/api/management';

vi.mock('@shared/api/management', () => ({
  fetchBillingMetrics: vi.fn(),
  fetchBillingPlans: vi.fn(),
  fetchBillingPlanHistory: vi.fn(),
  saveBillingPlan: vi.fn(),
  deleteBillingPlan: vi.fn(),
  updateBillingPlanLimits: vi.fn(),
}));

import { useManagementTariffs } from './useManagementTariffs';

const mockedFetchMetrics = vi.mocked(fetchBillingMetrics);
const mockedFetchPlans = vi.mocked(fetchBillingPlans);
const mockedFetchHistory = vi.mocked(fetchBillingPlanHistory);
const mockedSavePlan = vi.mocked(saveBillingPlan);
const mockedDeletePlan = vi.mocked(deleteBillingPlan);
const mockedUpdateLimits = vi.mocked(updateBillingPlanLimits);

const mockMetrics = {
  active_subs: 10,
  mrr: 200,
  arpu: 20,
  churn_30d: 0.12,
  tokens: [],
  networks: [],
};

const mockPlans = [
  {
    id: 'plan-1',
    slug: 'starter',
    title: 'Starter',
    description: 'For newcomers',
    price_cents: 999,
    currency: 'USD',
    price_token: 'USDC',
    price_usd_estimate: 9.99,
    billing_interval: 'month',
    is_active: true,
    order: 1,
    gateway_slug: 'main',
    contract_slug: 'vault',
    monthly_limits: { api_quota: 1000 },
    features: { status: 'active' },
  },
];

const mockHistory = [
  {
    id: 'h1',
    action: 'update',
    actor: 'admin',
    created_at: '2024-01-01T00:00:00Z',
    payload: { price_cents: 999 },
    resource_id: 'starter',
  },
];

describe('useManagementTariffs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedFetchMetrics.mockResolvedValue(mockMetrics);
    mockedFetchPlans.mockResolvedValue(mockPlans);
    mockedFetchHistory.mockResolvedValue(mockHistory);
    mockedSavePlan.mockResolvedValue();
    mockedDeletePlan.mockResolvedValue();
    mockedUpdateLimits.mockResolvedValue();
  });

  it('loads metrics and plans on mount', async () => {
    const { result } = renderHook(() => useManagementTariffs());
    expect(result.current.loading).toBe(true);

    await vi.waitFor(() => expect(result.current.loading).toBe(false));

    expect(mockedFetchMetrics).toHaveBeenCalledTimes(1);
    expect(mockedFetchPlans).toHaveBeenCalledTimes(1);
    expect(result.current.metrics).toEqual(mockMetrics);
    expect(result.current.plans).toEqual(mockPlans);
  });

  it('exposes savePlan that refreshes data', async () => {
    const { result } = renderHook(() => useManagementTariffs());
    await vi.waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.savePlan({ slug: 'starter' });
    });

    expect(mockedSavePlan).toHaveBeenCalledWith({ slug: 'starter' });
    expect(mockedFetchPlans).toHaveBeenCalledTimes(2);
  });

  it('exposes deletePlan', async () => {
    const { result } = renderHook(() => useManagementTariffs());
    await vi.waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.deletePlan('plan-1');
    });

    expect(mockedDeletePlan).toHaveBeenCalledWith('plan-1');
  });

  it('loads plan history with error handling', async () => {
    const { result } = renderHook(() => useManagementTariffs());
    await vi.waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.loadPlanHistory('starter');
    });

    expect(mockedFetchHistory).toHaveBeenCalledWith('starter');
    expect(result.current.history).toEqual(mockHistory);

    mockedFetchHistory.mockRejectedValueOnce(new Error('api down'));

    await act(async () => {
      await result.current.loadPlanHistory('starter');
    });

    expect(result.current.error).toBe('api down');
    expect(result.current.history).toEqual([]);
  });

  it('handles errors during refresh', async () => {
    mockedFetchPlans.mockRejectedValueOnce(new Error('boom'));
    const { result } = renderHook(() => useManagementTariffs());

    await vi.waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.error).toBe('boom');
    expect(result.current.plans).toEqual([]);
  });
});

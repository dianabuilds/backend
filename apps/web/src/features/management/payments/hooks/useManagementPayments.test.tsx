import { renderHook, act } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  fetchBillingKpi,
  fetchBillingProviders,
  fetchBillingContracts,
  fetchBillingContractEvents,
  fetchBillingCryptoConfig,
  fetchBillingTransactions,
  saveBillingProvider,
  deleteBillingProvider,
  saveBillingContract,
  deleteBillingContract,
  updateBillingCryptoConfig,
} from '@shared/api/management';

vi.mock('@shared/api/management', () => ({
  fetchBillingKpi: vi.fn(),
  fetchBillingProviders: vi.fn(),
  fetchBillingContracts: vi.fn(),
  fetchBillingContractEvents: vi.fn(),
  fetchBillingCryptoConfig: vi.fn(),
  fetchBillingTransactions: vi.fn(),
  saveBillingProvider: vi.fn(),
  deleteBillingProvider: vi.fn(),
  saveBillingContract: vi.fn(),
  deleteBillingContract: vi.fn(),
  updateBillingCryptoConfig: vi.fn(),
}));

import { useManagementPayments } from './useManagementPayments';

const mockedFetchKpi = vi.mocked(fetchBillingKpi);
const mockedFetchProviders = vi.mocked(fetchBillingProviders);
const mockedFetchContracts = vi.mocked(fetchBillingContracts);
const mockedFetchEvents = vi.mocked(fetchBillingContractEvents);
const mockedFetchCrypto = vi.mocked(fetchBillingCryptoConfig);
const mockedFetchTransactions = vi.mocked(fetchBillingTransactions);
const mockedSaveProvider = vi.mocked(saveBillingProvider);
const mockedDeleteProvider = vi.mocked(deleteBillingProvider);
const mockedSaveContract = vi.mocked(saveBillingContract);
const mockedDeleteContract = vi.mocked(deleteBillingContract);
const mockedUpdateCrypto = vi.mocked(updateBillingCryptoConfig);

const mockKpi = {
  success: 10,
  errors: 2,
  pending: 3,
  volume_cents: 123400,
  avg_confirm_ms: 90,
  contracts: { total: 2, enabled: 1, disabled: 1, testnet: 0, mainnet: 2 },
};

const mockProviders = [
  {
    slug: 'stripe',
    type: 'stripe',
    enabled: true,
    priority: 10,
    config: {},
  },
];

const mockContracts = [
  {
    id: 'ctr-1',
    slug: 'vault',
    title: 'Main Vault',
    chain: 'polygon',
    address: '0x123',
    type: 'ERC-20',
    enabled: true,
    testnet: false,
    methods: { list: ['deposit'], roles: ['ops'] },
    status: 'active',
    abi_present: true,
    webhook_url: '',
  },
];

const mockEvents = [
  {
    id: 'evt-1',
    contract_id: 'ctr-1',
    created_at: '2024-01-01T00:00:00Z',
    event: 'Deposit',
    status: 'succeeded',
    amount: 100,
    tx_hash: '0xabc',
  },
];

const mockCrypto = {
  rpc_endpoints: { polygon: 'https://rpc' },
  retries: 2,
  gas_price_cap: null,
  fallback_networks: {},
};

const mockTransactions = [
  {
    id: 'tx-1',
    created_at: '2024-01-01T10:00:00Z',
    user_id: 'user-1',
    gateway_slug: 'stripe',
    status: 'succeeded',
    currency: 'USD',
    token: 'USDC',
    network: 'polygon',
    product_type: 'plan',
    product_id: 'starter',
    gross_cents: 999,
    fee_cents: 30,
    net_cents: 969,
    tx_hash: '0xaaa',
    confirmed_at: '2024-01-01T10:05:00Z',
    failure_reason: null,
    meta: { contract_slug: 'vault' },
  },
];

describe('useManagementPayments', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockedFetchKpi.mockResolvedValue(mockKpi);
    mockedFetchProviders.mockResolvedValue(mockProviders);
    mockedFetchContracts.mockResolvedValue(mockContracts);
    mockedFetchEvents.mockResolvedValue(mockEvents);
    mockedFetchCrypto.mockResolvedValue(mockCrypto);
    mockedFetchTransactions.mockResolvedValue(mockTransactions);
    mockedSaveProvider.mockResolvedValue();
    mockedDeleteProvider.mockResolvedValue();
    mockedSaveContract.mockResolvedValue();
    mockedDeleteContract.mockResolvedValue();
    mockedUpdateCrypto.mockResolvedValue();
  });

  it('loads initial data on refresh', async () => {
    const { result } = renderHook(() => useManagementPayments({ auto: false }));

    expect(result.current.loading).toBe(false);

    await act(async () => {
      await result.current.refresh();
    });

    expect(mockedFetchKpi).toHaveBeenCalledTimes(1);
    expect(mockedFetchProviders).toHaveBeenCalledTimes(1);
    expect(mockedFetchContracts).toHaveBeenCalledTimes(1);
    expect(mockedFetchEvents).toHaveBeenCalledTimes(1);
    expect(mockedFetchCrypto).toHaveBeenCalledTimes(1);
    expect(mockedFetchTransactions).toHaveBeenCalledWith({ limit: 200 });

    expect(result.current.kpi.success).toBe(10);
    expect(result.current.providers).toEqual(mockProviders);
    expect(result.current.contracts).toEqual(mockContracts);
    expect(result.current.contractEvents).toEqual(mockEvents);
    expect(result.current.cryptoConfig).toEqual(mockCrypto);
    expect(result.current.transactions).toEqual(mockTransactions);
  });

  it('applies transaction filters', async () => {
    const { result } = renderHook(() => useManagementPayments({ auto: false }));

    await act(async () => {
      await result.current.refresh();
    });

    await act(async () => {
      await result.current.loadTransactions({ status: 'failed', provider: 'stripe' });
    });

    expect(mockedFetchTransactions).toHaveBeenLastCalledWith({ limit: 200, status: 'failed', provider: 'stripe' });
  });

  it('handles transaction loading errors', async () => {
    const { result } = renderHook(() => useManagementPayments({ auto: false }));

    await act(async () => {
      await result.current.refresh();
    });

    mockedFetchTransactions.mockRejectedValueOnce(new Error('boom'));

    await act(async () => {
      await result.current.loadTransactions({ status: 'failed' });
    });

    expect(result.current.error).toBe('boom');
    expect(result.current.transactionsLoading).toBe(false);
  });

  it('saves provider and refreshes', async () => {
    const { result } = renderHook(() => useManagementPayments({ auto: false }));

    await act(async () => {
      await result.current.refresh();
    });

    await act(async () => {
      await result.current.saveProvider({ slug: 'stripe', type: 'stripe', enabled: true, priority: 10, config: {} });
    });

    expect(mockedSaveProvider).toHaveBeenCalledWith({ slug: 'stripe', type: 'stripe', enabled: true, priority: 10, config: {} });
    expect(mockedFetchProviders).toHaveBeenCalledTimes(2);
  });

  it('updates crypto config', async () => {
    const { result } = renderHook(() => useManagementPayments({ auto: false }));

    await act(async () => {
      await result.current.refresh();
    });

    await act(async () => {
      await result.current.updateCryptoConfig({ ...mockCrypto, retries: 5 });
    });

    expect(mockedUpdateCrypto).toHaveBeenCalledWith({ ...mockCrypto, retries: 5 });
    expect(mockedFetchCrypto).toHaveBeenCalledTimes(2);
  });
});

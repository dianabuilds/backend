import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../client', () => ({
  apiGet: vi.fn(),
}));

import { apiGet } from '../client';
import { fetchBillingHistory, fetchBillingSummary } from './profile';

beforeEach(() => {
  vi.mocked(apiGet).mockReset();
});

describe('billing profile api', () => {
  it('fetches billing summary', async () => {
    const response = { plan: null };
    vi.mocked(apiGet).mockResolvedValue(response);

    const result = await fetchBillingSummary();

    expect(apiGet).toHaveBeenCalledWith('/v1/billing/me/summary', { signal: undefined });
    expect(result).toEqual(response);
  });

  it('fetches billing history with default params', async () => {
    const response = { items: [] };
    vi.mocked(apiGet).mockResolvedValue(response);

    const result = await fetchBillingHistory();

    expect(apiGet).toHaveBeenCalledWith('/v1/billing/me/history?limit=10', { signal: undefined });
    expect(result).toEqual(response);
  });

  it('fetches billing history with custom params', async () => {
    const controller = new AbortController();
    const response = { items: [] };
    vi.mocked(apiGet).mockResolvedValue(response);

    await fetchBillingHistory({ limit: 5, signal: controller.signal });

    expect(apiGet).toHaveBeenCalledWith('/v1/billing/me/history?limit=5', { signal: controller.signal });
  });
});


import React, { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

vi.mock('@shared/api/notifications', () => ({
  fetchNotificationBroadcasts: vi.fn(),
}));

import { useNotificationBroadcasts } from '../common/hooks/useNotificationBroadcasts';
import type { UseNotificationBroadcastsOptions } from '../common/hooks/useNotificationBroadcasts';
import { fetchNotificationBroadcasts } from '@shared/api/notifications';

type HookValue = ReturnType<typeof useNotificationBroadcasts>;

describe('useNotificationBroadcasts', () => {
  let container: HTMLDivElement;
  let root: Root;
  let current: HookValue;

  function TestComponent({ options }: { options?: UseNotificationBroadcastsOptions }) {
    current = useNotificationBroadcasts(options);
    return null;
  }

  async function renderHook(options?: UseNotificationBroadcastsOptions) {
    await act(async () => {
      root.render(<TestComponent options={options} />);
    });

    await act(async () => {
      vi.runAllTimers();
      await Promise.resolve();
    });
  }

  beforeEach(() => {
    vi.useFakeTimers();
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('loads broadcasts and aggregates summary data', async () => {
    vi.mocked(fetchNotificationBroadcasts).mockResolvedValueOnce({
      items: [
        {
          id: 'br-1',
          title: 'Welcome',
          body: null,
          template_id: null,
          audience: { type: 'all_users' },
          status: 'draft',
          created_by: 'admin',
          created_at: '2025-10-01T00:00:00Z',
          updated_at: '2025-10-01T00:00:00Z',
          scheduled_at: null,
          started_at: null,
          finished_at: null,
          total: 42,
          sent: 0,
          failed: 0,
        },
      ],
      total: 15,
      has_next: true,
      status_counts: { draft: 5, sent: 2 },
      recipients: 100,
    });

    await renderHook({ status: 'all', search: '', pageSize: 10, debounceMs: 0 });

    expect(fetchNotificationBroadcasts).toHaveBeenCalledTimes(1);
    expect(current.broadcasts).toHaveLength(1);
    expect(current.statusCounts.draft).toBe(5);
    expect(current.total).toBe(15);
    expect(current.recipients).toBe(100);
    expect(current.hasNext).toBe(true);
    expect(current.loading).toBe(false);
    expect(current.error).toBeNull();
  });

  it('updates page and refreshes data with new offset', async () => {
    vi.mocked(fetchNotificationBroadcasts)
      .mockResolvedValueOnce({ items: [], total: 30, has_next: true })
      .mockResolvedValueOnce({ items: [], total: 30, has_next: false });

    await renderHook({ status: 'all', pageSize: 10, debounceMs: 0 });

    await act(async () => {
      current.setPage(2);
    });

    await act(async () => {
      vi.runAllTimers();
      await Promise.resolve();
    });

    expect(fetchNotificationBroadcasts).toHaveBeenNthCalledWith(1, {
      limit: 10,
      offset: 0,
      status: undefined,
      search: undefined,
      signal: expect.any(AbortSignal),
    });
    expect(fetchNotificationBroadcasts).toHaveBeenNthCalledWith(2, {
      limit: 10,
      offset: 10,
      status: undefined,
      search: undefined,
      signal: expect.any(AbortSignal),
    });
  });

  it('handles fetch errors with provided mapper', async () => {
    vi.mocked(fetchNotificationBroadcasts).mockRejectedValueOnce(new Error('boom'));

    await renderHook({ debounceMs: 0, mapError: (err) => (err instanceof Error ? err.message : 'error') });

    expect(current.error).toBe('boom');
    expect(current.broadcasts).toHaveLength(0);
    expect(current.total).toBe(0);
    expect(current.statusCounts.sent).toBe(0);
  });
});

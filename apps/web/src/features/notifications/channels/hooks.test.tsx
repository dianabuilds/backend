import React, { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useNotificationsChannelsOverview } from './hooks';
import { fetchNotificationsChannelsOverview } from '@shared/api/notifications';
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

vi.mock('@shared/api/notifications', () => ({
  fetchNotificationsChannelsOverview: vi.fn(),
}));
type HookValue = ReturnType<typeof useNotificationsChannelsOverview>;

describe('useNotificationsChannelsOverview', () => {
  let container: HTMLDivElement;
  let root: Root;
  let current: HookValue;

  function TestComponent() {
    current = useNotificationsChannelsOverview();
    return null;
  }

  beforeEach(async () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    vi.mocked(fetchNotificationsChannelsOverview).mockResolvedValueOnce({
      channels: [],
      topics: [],
      summary: { active_channels: 1, total_channels: 2 },
    });

    await act(async () => {
      root.render(<TestComponent />);
    });

    await act(async () => {
      await Promise.resolve();
    });
  });

  afterEach(async () => {
    await act(async () => {
      root.unmount();
    });
    container.remove();
    vi.clearAllMocks();
  });

  it('loads overview data on mount', () => {
    expect(fetchNotificationsChannelsOverview).toHaveBeenCalledTimes(1);
    expect(current.overview?.summary.active_channels).toBe(1);
    expect(current.loading).toBe(false);
    expect(current.error).toBeNull();
  });

  it('refreshes data', async () => {
    vi.mocked(fetchNotificationsChannelsOverview).mockResolvedValueOnce({
      channels: [{ key: 'email', label: 'Email', status: 'required', opt_in: true }],
      topics: [],
      summary: { active_channels: 2, total_channels: 2 },
    });

    await act(async () => {
      await current.reload('refresh');
    });

    expect(fetchNotificationsChannelsOverview).toHaveBeenCalledTimes(2);
    expect(current.overview?.channels).toHaveLength(1);
    expect(current.refreshing).toBe(false);
  });

  it('captures errors', async () => {
    vi.mocked(fetchNotificationsChannelsOverview).mockRejectedValueOnce(new Error('unavailable'));

    await act(async () => {
      await current.reload();
    });

    expect(current.overview).toBeNull();
    expect(current.error).toBe('unavailable');
    expect(current.loading).toBe(false);
  });
});

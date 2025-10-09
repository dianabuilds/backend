import React, { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useNotificationsHistory } from './hooks';
import {
  fetchNotificationsHistory,
  markNotificationAsRead,
} from '@shared/api/notifications';

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

vi.mock('@shared/api/notifications', () => ({
  fetchNotificationsHistory: vi.fn(),
  markNotificationAsRead: vi.fn(),
}));

type HookValue = ReturnType<typeof useNotificationsHistory>;

describe('useNotificationsHistory', () => {
  let container: HTMLDivElement;
  let root: Root;
  let current: HookValue;

  function TestComponent() {
    current = useNotificationsHistory({ pageSize: 10 });
    return null;
  }

  beforeEach(async () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    vi.mocked(fetchNotificationsHistory).mockResolvedValueOnce({
      items: [{ id: 'h-1', message: 'hello' }],
      nextOffset: 1,
      hasMore: true,
    });

    vi.mocked(markNotificationAsRead).mockResolvedValue(undefined as any);

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

  it('loads history items on mount', () => {
    expect(fetchNotificationsHistory).toHaveBeenCalledWith(
      expect.objectContaining({ limit: 10, offset: 0 }),
    );
    expect(current.items).toHaveLength(1);
    expect(current.loading).toBe(false);
    expect(current.hasMore).toBe(true);
    expect(current.error).toBeNull();
  });

  it('appends items when loadMore succeeds', async () => {
    vi.mocked(fetchNotificationsHistory).mockResolvedValueOnce({
      items: [{ id: 'h-2', message: 'world' }],
      nextOffset: 2,
      hasMore: false,
    });

    await act(async () => {
      await current.loadMore();
    });

    expect(fetchNotificationsHistory).toHaveBeenCalledTimes(2);
    expect(fetchNotificationsHistory).toHaveBeenLastCalledWith(
      expect.objectContaining({ limit: 10, offset: 1 }),
    );
    expect(current.items.map((item) => item.id)).toEqual(['h-1', 'h-2']);
    expect(current.hasMore).toBe(false);
    expect(current.loadingMore).toBe(false);
  });

  it('captures error on refresh', async () => {
    vi.mocked(fetchNotificationsHistory).mockRejectedValueOnce(new Error('boom'));

    await act(async () => {
      await current.refresh();
    });

    expect(current.items).toHaveLength(0);
    expect(current.error).toBe('boom');
    expect(current.loading).toBe(false);
  });

  it('marks notification as read and updates state', async () => {
    vi.mocked(markNotificationAsRead).mockResolvedValueOnce({
      id: 'h-1',
      read_at: '2025-10-08T00:00:00Z',
    } as any);

    await act(async () => {
      await current.markAsRead('h-1');
    });

    expect(markNotificationAsRead).toHaveBeenCalledWith('h-1');
    expect(current.items[0].read_at).toBe('2025-10-08T00:00:00Z');
  });
});

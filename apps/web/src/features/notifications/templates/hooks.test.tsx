import React, { act } from 'react';
import { createRoot, Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useNotificationTemplates } from './hooks';
import {
  fetchNotificationTemplates,
  saveNotificationTemplate,
  deleteNotificationTemplate,
} from "@shared/api";

globalThis.IS_REACT_ACT_ENVIRONMENT = true;

vi.mock('@shared/api/notifications', () => ({
  fetchNotificationTemplates: vi.fn(),
  saveNotificationTemplate: vi.fn(),
  deleteNotificationTemplate: vi.fn(),
}));

type HookValue = ReturnType<typeof useNotificationTemplates>;

describe('useNotificationTemplates', () => {
  let container: HTMLDivElement;
  let root: Root;
  let current: HookValue;

  function TestComponent() {
    current = useNotificationTemplates();
    return null;
  }

  beforeEach(async () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);

    vi.mocked(fetchNotificationTemplates).mockResolvedValueOnce([
      {
        id: 'tpl-1',
        slug: 'welcome',
        name: 'Welcome',
        body: 'Hello',
        description: null,
        subject: null,
        locale: null,
        variables: {},
        meta: {},
        created_by: 'system',
        created_at: '2025-10-01T00:00:00Z',
        updated_at: '2025-10-01T00:00:00Z',
      },
    ]);

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

  it('loads templates on mount', () => {
    expect(fetchNotificationTemplates).toHaveBeenCalledTimes(1);
    expect(current.templates).toHaveLength(1);
    expect(current.templates[0]?.name).toBe('Welcome');
    expect(current.loading).toBe(false);
  });

  it('saves template and refreshes list', async () => {
    vi.mocked(fetchNotificationTemplates).mockResolvedValueOnce([
      {
        id: 'tpl-1',
        slug: 'welcome',
        name: 'Welcome',
        body: 'Hello',
        description: null,
        subject: null,
        locale: null,
        variables: {},
        meta: {},
        created_by: 'system',
        created_at: '2025-10-01T00:00:00Z',
        updated_at: '2025-10-01T00:00:00Z',
      },
      {
        id: 'tpl-2',
        slug: 'promo',
        name: 'Promo',
        body: 'Promo body',
        description: null,
        subject: 'Promo',
        locale: 'en',
        variables: {},
        meta: {},
        created_by: 'system',
        created_at: '2025-10-02T00:00:00Z',
        updated_at: '2025-10-02T00:00:00Z',
      },
    ]);

    vi.mocked(saveNotificationTemplate).mockResolvedValue(undefined);

    await act(async () => {
      await current.saveTemplate({
        name: 'Promo',
        body: 'Promo body',
        description: null,
        subject: 'Promo',
        locale: 'en',
        variables: null,
        meta: null,
      });
    });

    expect(saveNotificationTemplate).toHaveBeenCalledWith({
      name: 'Promo',
      body: 'Promo body',
      description: null,
      subject: 'Promo',
      locale: 'en',
      variables: null,
      meta: null,
    });
    expect(fetchNotificationTemplates).toHaveBeenCalledTimes(2);
    expect(current.templates).toHaveLength(2);
  });

  it('deletes template and refreshes list', async () => {
    vi.mocked(fetchNotificationTemplates).mockResolvedValueOnce([]);
    vi.mocked(deleteNotificationTemplate).mockResolvedValue(undefined);

    await act(async () => {
      await current.deleteTemplate('tpl-1');
    });

    expect(deleteNotificationTemplate).toHaveBeenCalledWith('tpl-1');
    expect(fetchNotificationTemplates).toHaveBeenCalledTimes(2);
    expect(current.templates).toHaveLength(0);
  });

  it('exposes error when save fails', async () => {
    const error = new Error('boom');
    vi.mocked(saveNotificationTemplate).mockRejectedValue(error);

    await act(async () => {
      try {
        await current.saveTemplate({
          name: 'Broken',
          body: 'Body',
          description: null,
          subject: null,
          locale: null,
          variables: null,
          meta: null,
        });
      } catch (err) {
        expect((err as Error).message).toBe('boom');
      }
    });

    expect(current.error).toBe('boom');
    expect(current.saving).toBe(false);
  });
});

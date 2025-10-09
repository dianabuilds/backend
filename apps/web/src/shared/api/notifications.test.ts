import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./client', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  apiRequestRaw: vi.fn(),
}));

import { apiDelete, apiGet, apiPost, apiPut, apiRequestRaw } from './client';
import {
  cancelNotificationBroadcast,
  createNotificationBroadcast,
  deleteNotificationTemplate,
  fetchNotificationBroadcasts,
  fetchNotificationPreferences,
  fetchNotificationTemplates,
  fetchNotificationsChannelsOverview,
  fetchNotificationsHistory,
  markNotificationAsRead,
  saveNotificationTemplate,
  sendNotificationBroadcastNow,
  updateNotificationBroadcast,
  updateNotificationPreferences,
} from './notifications';

beforeEach(() => {
  vi.mocked(apiGet).mockReset();
  vi.mocked(apiPost).mockReset();
  vi.mocked(apiPut).mockReset();
  vi.mocked(apiDelete).mockReset();
  vi.mocked(apiRequestRaw).mockReset();
});

describe('notifications api', () => {
  it('normalizes channels overview response', async () => {
    vi.mocked(apiGet).mockResolvedValue({
      overview: {
        channels: [
          { key: 'email', label: 'Email', status: 'required', opt_in: true },
          { key: 'sms', label: null, status: 'mystery', opt_in: 'noop' },
        ],
        topics: [
          {
            key: 'security',
            label: 'Security',
            description: 'Alerts',
            channels: [
              {
                key: 'email',
                label: 'Email',
                delivery: 'mandatory',
                opt_in: true,
                supports_digest: true,
                digest: 'weekly',
              },
              {
                key: 'sms',
                label: null,
                delivery: 'opt_in',
                opt_in: false,
                locked: 'no',
              },
            ],
          },
          { key: null },
        ],
        summary: {
          active_channels: 2,
          total_channels: 5,
          email_digest: 'daily',
          updated_at: '2025-10-07T10:00:00Z',
        },
      },
    });

    const result = await fetchNotificationsChannelsOverview();

    expect(apiGet).toHaveBeenCalledWith('/v1/me/settings/notifications/preferences', { signal: undefined });
    expect(result).toEqual({
      channels: [
        { key: 'email', label: 'Email', status: 'required', opt_in: true },
        { key: 'sms', label: 'sms', status: 'optional', opt_in: false },
      ],
      topics: [
        {
          key: 'security',
          label: 'Security',
          description: 'Alerts',
          channels: [
            {
              key: 'email',
              label: 'Email',
              delivery: 'mandatory',
              opt_in: true,
              supports_digest: true,
              digest: 'weekly',
            },
            {
              key: 'sms',
              label: 'sms',
              delivery: 'opt_in',
              opt_in: false,
            },
          ],
        },
      ],
      summary: {
        active_channels: 2,
        total_channels: 5,
        email_digest: 'daily',
        updated_at: '2025-10-07T10:00:00Z',
      },
    });
  });

  it('throws when overview is missing', async () => {
    vi.mocked(apiGet).mockResolvedValue({ overview: undefined });

    await expect(fetchNotificationsChannelsOverview()).rejects.toThrow('notifications_overview_malformed');
  });

  it('fetches notifications history with normalization and pagination metadata', async () => {
    vi.mocked(apiGet).mockResolvedValue({
      items: [
        { id: 'n-1', title: 'Hello', message: 42, created_at: '2025-10-01T00:00:00Z' },
        { id: 'n-2', title: 'World', message: 'Second', read_at: null },
      ],
    });

    const result = await fetchNotificationsHistory({ limit: 200, offset: -5 });

    expect(apiGet).toHaveBeenCalledWith('/v1/notifications?limit=100&offset=0', { signal: undefined });
    expect(result).toEqual({
      items: [
        { id: 'n-1', title: 'Hello', created_at: '2025-10-01T00:00:00Z' },
        { id: 'n-2', title: 'World', message: 'Second', read_at: null },
      ],
      nextOffset: 2,
      hasMore: false,
    });
  });

  it('marks notification as read and returns normalized payload', async () => {
    vi.mocked(apiPost).mockResolvedValue({
      notification: {
        id: 'notif/1',
        title: 'Marked',
        message: 'Done',
        read_at: '2025-10-08T00:00:00Z',
        meta: { topic: 'alerts' },
      },
    });

    const result = await markNotificationAsRead('notif/1', { payload: { force: true } });

    expect(apiPost).toHaveBeenCalledWith(
      '/v1/notifications/read/notif%2F1',
      { force: true },
      { signal: undefined },
    );
    expect(result).toEqual({
      id: 'notif/1',
      title: 'Marked',
      message: 'Done',
      read_at: '2025-10-08T00:00:00Z',
      meta: { topic: 'alerts' },
    });
  });

  it('throws when markNotificationAsRead receives empty id', async () => {
    await expect(markNotificationAsRead('')).rejects.toThrow('notification_id_missing');
  });

  it('fetches broadcasts with parameters and forwards signal', async () => {
    const controller = new AbortController();
    vi.mocked(apiGet).mockResolvedValue({ items: [] });

    const result = await fetchNotificationBroadcasts({
      limit: 25,
      offset: 50,
      status: 'draft',
      search: 'promo',
      signal: controller.signal,
    });

    expect(apiGet).toHaveBeenCalledWith('/v1/notifications/admin/broadcasts?limit=25&offset=50&status=draft&q=promo', {
      signal: controller.signal,
    });
    expect(result).toEqual({ items: [] });
  });

  it('creates, updates, sends and cancels broadcasts', async () => {
    vi.mocked(apiPost).mockResolvedValue(undefined);
    vi.mocked(apiPut).mockResolvedValue(undefined);

    await createNotificationBroadcast({
      title: 'Test',
      body: 'Body',
      template_id: null,
      audience: { type: 'all_users' },
      scheduled_at: null,
      created_by: 'admin',
    });
    await updateNotificationBroadcast('br-1', {
      title: 'Updated',
      body: null,
      template_id: 'tpl-1',
      audience: { type: 'segment', filters: { region: 'emea' } },
      scheduled_at: '2025-10-01T00:00:00Z',
    });
    await sendNotificationBroadcastNow('br-1');
    await cancelNotificationBroadcast('br-1');

    expect(apiPost).toHaveBeenNthCalledWith(1, '/v1/notifications/admin/broadcasts', {
      title: 'Test',
      body: 'Body',
      template_id: null,
      audience: { type: 'all_users' },
      scheduled_at: null,
      created_by: 'admin',
    });
    expect(apiPut).toHaveBeenCalledWith('/v1/notifications/admin/broadcasts/br-1', {
      title: 'Updated',
      body: null,
      template_id: 'tpl-1',
      audience: { type: 'segment', filters: { region: 'emea' } },
      scheduled_at: '2025-10-01T00:00:00Z',
    });
    expect(apiPost).toHaveBeenNthCalledWith(2, '/v1/notifications/admin/broadcasts/br-1/actions/send-now', {});
    expect(apiPost).toHaveBeenNthCalledWith(3, '/v1/notifications/admin/broadcasts/br-1/actions/cancel', {});
  });

  it('fetches notification templates and filters invalid entries', async () => {
    vi.mocked(apiGet).mockResolvedValue({
      items: [
        {
          id: 'tpl-1',
          slug: 'welcome',
          name: 'Welcome',
          body: 'Hello',
          created_at: '2025-10-01T00:00:00Z',
          updated_at: '2025-10-01T00:00:00Z',
        },
        {
          id: null,
        },
      ],
    });

    const result = await fetchNotificationTemplates();

    expect(apiGet).toHaveBeenCalledWith('/v1/notifications/admin/templates', expect.objectContaining({ signal: undefined }));
    expect(result).toEqual([
      {
        id: 'tpl-1',
        slug: 'welcome',
        name: 'Welcome',
        body: 'Hello',
        created_at: '2025-10-01T00:00:00Z',
        updated_at: '2025-10-01T00:00:00Z',
      },
    ]);
  });

  it('saves and deletes notification template', async () => {
    vi.mocked(apiPost).mockResolvedValue(undefined);
    vi.mocked(apiDelete).mockResolvedValue(undefined);
    const payload = { name: 'Test', body: 'Hello' } as any;

    await saveNotificationTemplate(payload);
    await deleteNotificationTemplate(' tpl-1 ');

    expect(apiPost).toHaveBeenCalledWith('/v1/notifications/admin/templates', payload);
    expect(apiDelete).toHaveBeenCalledWith('/v1/notifications/admin/templates/tpl-1');
  });

  it('throws when deleting template without id', async () => {
    await expect(deleteNotificationTemplate('   ')).rejects.toThrow('template_id_missing');
  });

  it('fetches notification preferences and returns etag', async () => {
    const response = new Response(JSON.stringify({ preferences: { 'email.digest': { enabled: true } } }), {
      headers: { ETag: 'etag-123' },
    });
    vi.mocked(apiRequestRaw).mockResolvedValue(response as any);

    const result = await fetchNotificationPreferences();

    expect(apiRequestRaw).toHaveBeenCalledWith('/v1/me/settings/notifications/preferences', { signal: undefined });
    expect(result.preferences).toStrictEqual({ 'email.digest': { enabled: true } });
    expect(result.etag).toBe('etag-123');
  });

  it('updates notification preferences and falls back to sent payload when missing', async () => {
    const response = new Response(JSON.stringify({}), {
      headers: { ETag: 'etag-456' },
    });
    vi.mocked(apiRequestRaw).mockResolvedValue(response as any);

    const payload = { 'email.digest': { enabled: true } } as any;
    const result = await updateNotificationPreferences(payload, { headers: { 'If-Match': 'etag-123' } });

    expect(apiRequestRaw).toHaveBeenCalledWith('/v1/me/settings/notifications/preferences', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'If-Match': 'etag-123' },
      body: JSON.stringify({ preferences: payload }),
      signal: undefined,
    });
    expect(result.preferences).toStrictEqual(payload);
    expect(result.etag).toBe('etag-456');
  });
});

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
        {
          id: 'n-1',
          user_id: 'user-1',
          channel: 'email',
          title: 'Hello',
          message: '42',
          priority: 'high',
          created_at: '2025-10-01T00:00:00Z',
          meta: { topic: 'alerts' },
          is_read: false,
        },
        {
          id: 'n-2',
          user_id: 'user-2',
          message: 'Second',
          read_at: '2025-10-02T00:00:00Z',
        },
      ],
      unread: '5',
    });

    const result = await fetchNotificationsHistory({ limit: 200, offset: -5 });

    expect(apiGet).toHaveBeenCalledWith('/v1/notifications?limit=100&offset=0', { signal: undefined });
    expect(result).toEqual({
      items: [
        {
          id: 'n-1',
          user_id: 'user-1',
          channel: 'email',
          title: 'Hello',
          message: '42',
          type: null,
          priority: 'high',
          meta: { topic: 'alerts' },
          created_at: '2025-10-01T00:00:00Z',
          updated_at: null,
          read_at: null,
          is_read: false,
        },
        {
          id: 'n-2',
          user_id: 'user-2',
          channel: null,
          title: null,
          message: 'Second',
          type: null,
          priority: 'normal',
          meta: {},
          created_at: null,
          updated_at: null,
          read_at: '2025-10-02T00:00:00Z',
          is_read: true,
        },
      ],
      nextOffset: 2,
      hasMore: false,
      unread: 5,
    });
  });

  it('marks notification as read and returns normalized payload', async () => {
    vi.mocked(apiPost).mockResolvedValue({
      notification: {
        id: 'notif/1',
        user_id: 'user-5',
        channel: 'push',
        title: 'Marked',
        message: 'Done',
        type: 'system',
        priority: 'low',
        read_at: '2025-10-08T00:00:00Z',
        updated_at: '2025-10-08T00:00:00Z',
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
      user_id: 'user-5',
      channel: 'push',
      title: 'Marked',
      message: 'Done',
      type: 'system',
      priority: 'low',
      meta: { topic: 'alerts' },
      created_at: null,
      updated_at: '2025-10-08T00:00:00Z',
      read_at: '2025-10-08T00:00:00Z',
      is_read: true,
    });
  });

  it('throws when markNotificationAsRead receives empty id', async () => {
    await expect(markNotificationAsRead('')).rejects.toThrow('notification_id_missing');
  });

  it('fetches broadcasts with parameters and forwards signal', async () => {
    const controller = new AbortController();
    vi.mocked(apiGet).mockResolvedValue({
      items: [
        {
          id: 'br-1',
          title: 'Promo',
          body: null,
          template_id: 'tpl-1',
          audience: { type: 'all_users', filters: null, user_ids: null },
          status: 'draft',
          created_by: 'admin',
          created_at: '2025-10-11T00:00:00Z',
          updated_at: '2025-10-11T00:00:00Z',
          scheduled_at: null,
          started_at: null,
          finished_at: null,
          total: 0,
          sent: 0,
          failed: 0,
        },
      ],
      total: '10',
      offset: 50,
      limit: 25,
      has_next: true,
      status_counts: { draft: '8', sent: 2 },
      recipients: '1200',
    });

    const result = await fetchNotificationBroadcasts({
      limit: 25,
      offset: 50,
      statuses: ['draft'],
      search: 'promo',
      signal: controller.signal,
    });

    expect(apiGet).toHaveBeenCalledWith('/v1/notifications/admin/broadcasts?limit=25&offset=50&statuses=draft&q=promo', {
      signal: controller.signal,
    });
    expect(result).toEqual({
      items: [
        {
          id: 'br-1',
          title: 'Promo',
          body: null,
          template_id: 'tpl-1',
          audience: { type: 'all_users', filters: null, user_ids: null },
          status: 'draft',
          created_by: 'admin',
          created_at: '2025-10-11T00:00:00Z',
          updated_at: '2025-10-11T00:00:00Z',
          scheduled_at: null,
          started_at: null,
          finished_at: null,
          total: 0,
          sent: 0,
          failed: 0,
        },
      ],
      total: 10,
      offset: 50,
      limit: 25,
      has_next: true,
      status_counts: { draft: 8, sent: 2 },
      recipients: 1200,
    });
  });

  it('creates, updates, sends and cancels broadcasts', async () => {
    const createResponse = {
      id: 'br-1',
      title: 'Test',
      body: 'Body',
      template_id: null,
      audience: { type: 'all_users', filters: null, user_ids: null },
      status: 'draft',
      created_by: 'admin',
      created_at: '2025-10-11T00:00:00Z',
      updated_at: '2025-10-11T00:00:00Z',
      scheduled_at: null,
      started_at: null,
      finished_at: null,
      total: 0,
      sent: 0,
      failed: 0,
    };
    const updateResponse = {
      ...createResponse,
      title: 'Updated',
      status: 'scheduled',
      scheduled_at: '2025-10-12T00:00:00Z',
      audience: { type: 'segment', filters: { region: 'emea' }, user_ids: null },
      template_id: 'tpl-1',
    };
    const sendResponse = {
      ...createResponse,
      status: 'sending',
      started_at: '2025-10-11T12:00:00Z',
    };
    const cancelResponse = {
      ...createResponse,
      status: 'cancelled',
      finished_at: '2025-10-11T12:05:00Z',
    };

    vi.mocked(apiPost)
      .mockResolvedValueOnce(createResponse)
      .mockResolvedValueOnce(sendResponse)
      .mockResolvedValueOnce(cancelResponse);
    vi.mocked(apiPut).mockResolvedValue(updateResponse);

    const created = await createNotificationBroadcast({
      title: 'Test',
      body: 'Body',
      template_id: null,
      audience: { type: 'all_users' },
      scheduled_at: null,
      created_by: 'admin',
    });
    const updated = await updateNotificationBroadcast('br-1', {
      title: 'Updated',
      body: null,
      template_id: 'tpl-1',
      audience: { type: 'segment', filters: { region: 'emea' } },
      scheduled_at: '2025-10-12T00:00:00Z',
    });
    const sent = await sendNotificationBroadcastNow('br-1');
    const cancelled = await cancelNotificationBroadcast('br-1');

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
      scheduled_at: '2025-10-12T00:00:00Z',
    });
    expect(apiPost).toHaveBeenNthCalledWith(2, '/v1/notifications/admin/broadcasts/br-1/actions/send-now', {});
    expect(apiPost).toHaveBeenNthCalledWith(3, '/v1/notifications/admin/broadcasts/br-1/actions/cancel', {});

    expect(created).toEqual(createResponse);
    expect(updated).toEqual(updateResponse);
    expect(sent).toEqual(sendResponse);
    expect(cancelled).toEqual(cancelResponse);
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
        description: null,
        subject: null,
        locale: null,
        variables: {},
        meta: {},
        created_by: null,
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

    expect(apiPost).toHaveBeenCalledWith('/v1/notifications/admin/templates', {
      name: 'Test',
      body: 'Hello',
      slug: null,
      description: null,
      subject: null,
      locale: null,
      variables: null,
      meta: null,
      created_by: null,
    });
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

import { describe, expect, it, vi, afterEach } from 'vitest';
import { setAccessToken } from './client';
import {
  cancelScheduledPublish,
  getPublishInfo,
  publishNow,
  schedulePublish,
} from './publish';

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
  window.sessionStorage.clear();
});

describe('getPublishInfo', () => {
  it('requests publish info with auth header', async () => {
    window.localStorage.setItem('workspaceId', 'ws1');
    setAccessToken('at');
    const fetchSpy = vi
      .spyOn(global, 'fetch')
      .mockResolvedValue(
        new Response('{"status":"draft"}', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      );
    await getPublishInfo('ws1', 42);
    expect(fetchSpy).toHaveBeenCalledWith(
      '/admin/workspaces/ws1/nodes/42/publish_info',
      expect.objectContaining({
        method: 'GET',
        headers: expect.objectContaining({
          Accept: 'application/json',
          Authorization: 'Bearer at',
        }),
      }),
    );
  });
});

describe('publishNow', () => {
  it('posts access with auth header', async () => {
    window.localStorage.setItem('workspaceId', 'ws1');
    setAccessToken('at');
    const fetchSpy = vi
      .spyOn(global, 'fetch')
      .mockResolvedValue(new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }));
    await publishNow('ws1', 42, 'early_access');
    expect(fetchSpy).toHaveBeenCalledWith(
      '/admin/workspaces/ws1/nodes/42/publish',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Accept: 'application/json',
          'Content-Type': 'application/json',
          Authorization: 'Bearer at',
        }),
        body: JSON.stringify({ access: 'early_access' }),
      }),
    );
  });
});

describe('schedulePublish', () => {
  it('posts schedule with auth header', async () => {
    window.localStorage.setItem('workspaceId', 'ws1');
    setAccessToken('at');
    const fetchSpy = vi
      .spyOn(global, 'fetch')
      .mockResolvedValue(
        new Response('{"status":"scheduled"}', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      );
    await schedulePublish('ws1', 42, '2025-01-01T00:00:00Z', 'premium_only');
    expect(fetchSpy).toHaveBeenCalledWith(
      '/admin/workspaces/ws1/nodes/42/schedule_publish',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Accept: 'application/json',
          'Content-Type': 'application/json',
          Authorization: 'Bearer at',
        }),
        body: JSON.stringify({ run_at: '2025-01-01T00:00:00Z', access: 'premium_only' }),
      }),
    );
  });
});

describe('cancelScheduledPublish', () => {
  it('sends delete with auth header', async () => {
    window.localStorage.setItem('workspaceId', 'ws1');
    setAccessToken('at');
    const fetchSpy = vi
      .spyOn(global, 'fetch')
      .mockResolvedValue(
        new Response('{"canceled":true}', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      );
    await cancelScheduledPublish('ws1', 42);
    expect(fetchSpy).toHaveBeenCalledWith(
      '/admin/workspaces/ws1/nodes/42/schedule_publish',
      expect.objectContaining({
        method: 'DELETE',
        headers: expect.objectContaining({
          Accept: 'application/json',
          Authorization: 'Bearer at',
        }),
      }),
    );
  });
});

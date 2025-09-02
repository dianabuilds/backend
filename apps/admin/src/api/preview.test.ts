import { describe, expect, it, vi, afterEach } from 'vitest';
import { setAccessToken, setPreviewToken } from './client';
import * as preview from './preview';

afterEach(() => {
  vi.restoreAllMocks();
  window.sessionStorage.clear();
});

describe('simulatePreview', () => {
  it('uses proper URL, body and headers with tokens', async () => {
    setAccessToken('at');
    setPreviewToken('pt');
    const fetchSpy = vi
      .spyOn(global, 'fetch')
      .mockResolvedValue(new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }));
    await preview.simulatePreview({ workspace_id: 'ws1', start: 'start-node' });
    expect(fetchSpy).toHaveBeenCalledWith(
      '/admin/preview/transitions/simulate',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Accept: 'application/json',
          'Content-Type': 'application/json',
          Authorization: 'Bearer at',
          'X-Preview-Token': 'pt',
        }),
        body: JSON.stringify({ workspace_id: 'ws1', start: 'start-node' }),
      }),
    );
  });
});

describe('createPreviewLink', () => {
  it('posts workspace id with tokens', async () => {
    setAccessToken('at');
    setPreviewToken('pt');
    const fetchSpy = vi
      .spyOn(global, 'fetch')
      .mockResolvedValue(
        new Response('{"url":"https://example/preview"}', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      );
    await preview.createPreviewLink('ws1');
    expect(fetchSpy).toHaveBeenCalledWith(
      '/admin/preview/link',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Accept: 'application/json',
          'Content-Type': 'application/json',
          Authorization: 'Bearer at',
          'X-Preview-Token': 'pt',
        }),
        body: JSON.stringify({ workspace_id: 'ws1' }),
      }),
    );
  });
});

describe('openNodePreview', () => {
  it('opens assembled URL with encoded slug', async () => {
    setAccessToken('at');
    setPreviewToken('pt');
    vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response('{"url":"https://example/preview"}', {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    await preview.openNodePreview('ws1', 'start node');
    expect(openSpy).toHaveBeenCalledWith(
      'https://example/preview?start=start%20node',
      '_blank',
      'noopener',
    );
  });
});

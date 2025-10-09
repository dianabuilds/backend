import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiFetch, apiGet } from './base';
import { clearCsrfToken, setCsrfToken } from './csrf';
import { setAuthLostHandler } from './auth';

function mockResponse(body: string, status = 200, headers: Record<string, string> = {}) {
  return new Response(body, { status, headers });
}

function createStorage() {
  const store = new Map<string, string>();
  return {
    getItem(key: string) {
      return store.has(key) ? store.get(key)! : null;
    },
    setItem(key: string, value: string) {
      store.set(String(key), String(value));
    },
    removeItem(key: string) {
      store.delete(key);
    },
    clear() {
      store.clear();
    },
  } as Storage;
}

beforeEach(() => {
  Object.defineProperty(window, 'sessionStorage', {
    configurable: true,
    value: createStorage(),
  });
  Object.defineProperty(window, 'localStorage', {
    configurable: true,
    value: createStorage(),
  });
  clearCsrfToken();
  vi.stubGlobal('fetch', vi.fn());
  delete (window as any).__ADMIN_API_KEY;
});

afterEach(() => {
  setAuthLostHandler(undefined);
  vi.unstubAllGlobals();
});

describe('api base client', () => {
  it('sends json payload with csrf header', async () => {
    setCsrfToken('csrf-token');
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValue(mockResponse('{"ok": true}', 200));

    await apiFetch('/v1/test', { method: 'POST', json: { foo: 'bar' } });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/v1/test');
    expect(init?.method).toBe('POST');
    expect(init?.body).toBe(JSON.stringify({ foo: 'bar' }));
    expect(init?.headers).toMatchObject({
      'Content-Type': 'application/json',
      'X-CSRF-Token': 'csrf-token',
    });
  });

  it('does not attach csrf header to get requests', async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValue(mockResponse('[]', 200));

    await apiGet('/v1/items', { headers: { 'X-Test': 'yes' } });

    const [, init] = fetchMock.mock.calls[0];
    expect(init?.method).toBe('GET');
    expect(init?.headers).toMatchObject({ 'X-Test': 'yes' });
    expect(Object.keys(init?.headers || {})).not.toContain('X-CSRF-Token');
  });

  it('notifies auth handler on unauthorized response', async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValue(mockResponse('{"detail":"missing_token"}', 403));
    const handler = vi.fn();
    setAuthLostHandler(handler);

    await expect(apiFetch('/v1/protected')).rejects.toThrow('missing_token');
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('injects admin key for admin endpoints', async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValue(mockResponse('[]', 200));
    (window as any).__ADMIN_API_KEY = 'secret';

    await apiGet('/admin/metrics');

    const [, init] = fetchMock.mock.calls[0];
    expect(init?.headers).toMatchObject({ 'X-Admin-Key': 'secret' });
  });
});
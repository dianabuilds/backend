import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest';

vi.mock('@shared/ui/toastBus', () => ({
  pushGlobalToast: vi.fn(),
}));

import { pushGlobalToast } from '@shared/ui/toastBus';
import { apiFetch, ApiRequestError } from './base';
import { clearCsrfToken, setCsrfToken } from './csrf';

function createStorage(): Storage {
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

const nativeFetch = globalThis.fetch;
let fetchMock: Mock;

beforeEach(() => {
  fetchMock = vi.fn();
  globalThis.fetch = fetchMock as unknown as typeof fetch;
  Object.defineProperty(window, 'sessionStorage', {
    configurable: true,
    value: createStorage(),
  });
  Object.defineProperty(window, 'localStorage', {
    configurable: true,
    value: createStorage(),
  });
  clearCsrfToken();
  setCsrfToken(null, { headerName: 'X-CSRF-Token', cookieName: 'XSRF-TOKEN' });
  vi.mocked(pushGlobalToast).mockReset();
});

afterEach(() => {
  globalThis.fetch = nativeFetch;
  vi.useRealTimers();
});

describe('rate limit handling', () => {
  it('retries once with retry-after header and resolves', async () => {
    vi.useFakeTimers();

    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ error: { code: 'rate_limited', message: 'Slow down' } }),
          { status: 429, headers: { 'Retry-After': '1' } },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));

    const promise = apiFetch<{ ok: boolean }>('/v1/test', { method: 'POST', json: { foo: 'bar' } });

    await vi.advanceTimersByTimeAsync(1000);

    await expect(promise).resolves.toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(vi.mocked(pushGlobalToast)).toHaveBeenCalledWith(
      expect.objectContaining({ intent: 'info', description: expect.stringContaining('Повторим') }),
    );
  });

  it('surfaces error when retry-after missing', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ error: { code: 'rate_limited', message: 'Too fast' } }),
        { status: 429 },
      ),
    );

    await expect(apiFetch('/v1/test')).rejects.toBeInstanceOf(ApiRequestError);
    expect(vi.mocked(pushGlobalToast)).toHaveBeenCalledWith(
      expect.objectContaining({ intent: 'error', description: expect.stringContaining('Превышен лимит') }),
    );
  });

  it('emits csrf toast on forbidden response', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({ error: { code: 'csrf_failed', message: 'Denied' } }),
        { status: 403 },
      ),
    );

    await expect(apiFetch('/v1/test', { method: 'POST', json: {} })).rejects.toBeInstanceOf(ApiRequestError);
    expect(vi.mocked(pushGlobalToast)).toHaveBeenCalledWith(
      expect.objectContaining({ description: expect.stringContaining('CSRF') }),
    );
  });
});

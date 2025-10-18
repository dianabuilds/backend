import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  clearCsrfToken,
  csrfHeaders,
  getCookie,
  getCsrfToken,
  getCsrfCookieName,
  getCsrfHeaderName,
  primeCsrfFromCookies,
  setCsrfToken,
  syncCsrfFromResponse,
} from './csrf';

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

function resetCookies() {
  document.cookie = 'XSRF-TOKEN=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
  document.cookie = 'CUSTOM-CSRF=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
  document.cookie = 'foo=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
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
  resetCookies();
  clearCsrfToken();
  setCsrfToken(null, { headerName: 'X-CSRF-Token', cookieName: 'XSRF-TOKEN' });
});

describe('csrf utilities', () => {
  it('reads cookies by partial name match', () => {
    document.cookie = 'foo=123';
    document.cookie = 'XSRF-TOKEN=abc123';
    expect(getCookie('xsrf')).toBe('abc123');
  });

  it('returns csrf header when token cached', () => {
    setCsrfToken('token-value');
    expect(csrfHeaders()).toStrictEqual({ 'X-CSRF-Token': 'token-value' });
  });

  it('primes token from cookies and detects cookie name', () => {
    document.cookie = 'CUSTOM-CSRF=from-cookie';
    primeCsrfFromCookies();
    expect(getCsrfToken()).toBe('from-cookie');
    expect(getCsrfCookieName()).toBe('CUSTOM-CSRF');
  });

  it('syncs token from response headers and stores metadata', () => {
    const response = new Response('', { headers: { 'X-Test-CSRF': 'from-response' } });
    syncCsrfFromResponse(response);
    expect(getCsrfToken()).toBe('from-response');
    expect(getCsrfHeaderName()).toBe('X-Test-CSRF');
    const raw = window.sessionStorage.getItem('auth.csrf_token');
    expect(raw).toBeTypeOf('string');
    const parsed = JSON.parse(raw as string);
    expect(parsed).toMatchObject({ token: 'from-response', header: 'X-Test-CSRF' });
  });

  it('expires cached token after ttl', async () => {
    vi.useFakeTimers();
    const now = new Date('2025-01-01T00:00:00Z').getTime();
    vi.setSystemTime(now);
    setCsrfToken('short-lived', { ttlSeconds: 1 });
    expect(getCsrfToken()).toBe('short-lived');
    vi.advanceTimersByTime(1100);
    expect(getCsrfToken()).toBeNull();
    expect(csrfHeaders()).toStrictEqual({});
    vi.useRealTimers();
  });
});

import { beforeEach, describe, expect, it } from 'vitest';
import {
  clearCsrfToken,
  csrfHeaders,
  getCookie,
  getCsrfToken,
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

  it('primes token from cookies', () => {
    document.cookie = 'XSRF-TOKEN=from-cookie';
    primeCsrfFromCookies();
    expect(getCsrfToken()).toBe('from-cookie');
  });

  it('syncs token from response headers', () => {
    const response = new Response('', { headers: { 'X-CSRF-Token': 'from-response' } });
    syncCsrfFromResponse(response);
    expect(getCsrfToken()).toBe('from-response');
    expect(window.sessionStorage.getItem('auth.csrf_token')).toBe('from-response');
  });
});
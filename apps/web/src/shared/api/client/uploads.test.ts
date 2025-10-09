import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { apiUploadMedia } from './uploads';
import { clearCsrfToken } from './csrf';

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
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('api upload client', () => {
  it('builds form data from payload', async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValue(mockResponse('{"ok": true}', 200, { 'Content-Type': 'application/json' }));
    const blob = new Blob(['hello'], { type: 'text/plain' });

    await apiUploadMedia('/v1/files', { file: blob });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('/v1/files');
    expect(init?.method).toBe('POST');
    expect(init?.headers).not.toHaveProperty('Content-Type');
    expect(init?.body).toBeInstanceOf(FormData);
    const formEntries = Array.from((init?.body as FormData).entries());
    expect(formEntries).toHaveLength(1);
    const [field, value] = formEntries[0];
    expect(field).toBe('file');
    expect(value).toBeInstanceOf(Blob);
    expect((value as Blob).size).toBe(blob.size);
  });

  it('defaults upload path when omitted', async () => {
    const fetchMock = vi.mocked(globalThis.fetch);
    fetchMock.mockResolvedValue(mockResponse('{"ok": true}', 200));
    const blob = new Blob(['hello']);

    await apiUploadMedia({ file: blob });

    expect(fetchMock.mock.calls[0][0]).toBe('/v1/media');
  });

  it('throws when payload missing', async () => {
    await expect(apiUploadMedia('/v1/files', undefined as any)).rejects.toThrow('payload_required');
    expect(globalThis.fetch).not.toHaveBeenCalled();
  });
});
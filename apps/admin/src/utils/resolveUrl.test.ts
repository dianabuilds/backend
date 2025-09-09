import { afterEach, describe, expect, it, vi } from 'vitest';

import { resolveUrl } from './resolveUrl';

const originalWindow = global.window;

afterEach(() => {
  global.window = originalWindow;
  vi.unstubAllEnvs();
});

describe('resolveUrl', () => {
  it('maps Vite dev ports to backend :8000', () => {
    vi.stubEnv('VITE_API_BASE', '');
    global.window = {
      location: {
        port: '5173',
        hostname: 'localhost',
        protocol: 'https:',
        host: 'localhost:5173',
        origin: 'https://localhost:5173',
      } as unknown as Location,
    } as unknown as Window & typeof globalThis;
    expect(resolveUrl('/static/img.png')).toBe('http://localhost:8000/static/img.png');
  });

  it('uses current origin in production', () => {
    vi.stubEnv('VITE_API_BASE', '');
    global.window = {
      location: {
        port: '',
        hostname: 'example.com',
        protocol: 'https:',
        host: 'example.com',
        origin: 'https://example.com',
      } as unknown as Location,
    } as unknown as Window & typeof globalThis;
    expect(resolveUrl('/static/img.png')).toBe('https://example.com/static/img.png');
  });
});

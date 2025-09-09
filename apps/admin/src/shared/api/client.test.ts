import { describe, expect, it, vi } from 'vitest';

vi.mock('../../api/client', () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from '../../api/client';
import { client } from './client';

describe('client', () => {
  it('throws Error with response.detail', async () => {
    vi.mocked(
      apiFetch as unknown as typeof apiFetch & { mockResolvedValue: (v: unknown) => unknown },
    ).mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      headers: { get: () => 'application/json' },
      json: async () => ({ detail: 'invalid' }),
    } as unknown as Response);

    await expect(client.get('/foo')).rejects.toThrow('invalid');
  });
});

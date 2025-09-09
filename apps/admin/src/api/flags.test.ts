import { api } from './client';
import { listFlags } from './flags';

vi.mock('./client', () => ({
  api: { get: vi.fn() },
}));

describe('listFlags', () => {
  it('passes query params', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] });
    await listFlags({ q: 'foo', limit: 10, offset: 20 });
    expect(api.get).toHaveBeenCalledWith('/admin/flags?q=foo&limit=10&offset=20');
  });
});

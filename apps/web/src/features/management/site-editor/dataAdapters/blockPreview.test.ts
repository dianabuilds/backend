import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getBlockPreview } from './blockPreview';

vi.mock('@shared/api/management', () => ({
  managementSiteEditorApi: {
    previewSiteBlock: vi.fn(),
  },
}));

let mockedApi: any;

beforeEach(async () => {
  const module = await import('@shared/api/management');
  mockedApi = vi.mocked(module.managementSiteEditorApi);
  mockedApi.previewSiteBlock.mockReset();
});

describe('blockPreview adapters', () => {
  it('uses server preview when available', async () => {
    mockedApi.previewSiteBlock.mockResolvedValueOnce({
      block: 'nodes_carousel',
      locale: 'en',
      source: 'live',
      fetched_at: '2025-10-26T11:00:00Z',
      items: [
        { title: 'Server item', href: '/n/server-item', subtitle: 'Source · 2025-10-26' },
      ],
      meta: { adapter: 'test' },
    });

    const preview = await getBlockPreview('nodes_carousel', { locale: 'en', useLive: true });
    expect(preview.source).toBe('live');
    expect(preview.items[0]?.title).toBe('Server item');
    expect(preview.meta?.adapter).toBe('test');
  });

  it('falls back to mocks when server fails', async () => {
    mockedApi.previewSiteBlock.mockRejectedValueOnce(new Error('offline'));

    const preview = await getBlockPreview('recommendations', { locale: 'ru', useLive: true });
    expect(['mock', 'error']).toContain(preview.source);
    expect(preview.items.length).toBeGreaterThan(0);
  });
});

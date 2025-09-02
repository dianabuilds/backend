import { describe, expect, it, vi } from 'vitest';
import { wsApi } from './wsApi';
import * as preview from './preview';

describe('simulatePreview', () => {
  it('sends workspace_id in body and hits correct URL', async () => {
    const spy = vi.spyOn(wsApi, 'post').mockResolvedValue({} as any);
    await preview.simulatePreview({ workspace_id: 'ws1', start: 'start-node' });
    expect(spy).toHaveBeenCalledWith(
      '/admin/preview/transitions/simulate',
      { workspace_id: 'ws1', start: 'start-node' },
      { workspace: false },
    );
  });
});

describe('createPreviewLink', () => {
  it('requests link without workspace prefix', async () => {
    const spy = vi
      .spyOn(wsApi, 'post')
      .mockResolvedValue({ url: 'https://example/preview' } as any);
    await preview.createPreviewLink('ws1');
    expect(spy).toHaveBeenCalledWith(
      '/admin/preview/link',
      { workspace_id: 'ws1' },
      { workspace: false },
    );
  });
});

describe('openNodePreview', () => {
  it('opens assembled URL with encoded slug', async () => {
    const postSpy = vi
      .spyOn(wsApi, 'post')
      .mockResolvedValue({ url: 'https://example/preview' } as any);
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
    await preview.openNodePreview('ws1', 'start node');
    expect(postSpy).toHaveBeenCalledWith(
      '/admin/preview/link',
      { workspace_id: 'ws1' },
      { workspace: false },
    );
    expect(openSpy).toHaveBeenCalledWith(
      'https://example/preview?start=start%20node',
      '_blank',
      'noopener',
    );
  });
});

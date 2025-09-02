import { vi, describe, it, expect } from 'vitest';
import { api } from './client';
import { simulatePreview } from './preview';

describe('simulatePreview', () => {
  it('sends workspace_id in body and hits correct URL', async () => {
    const spy = vi.spyOn(api, 'post').mockResolvedValue({ data: {} } as any);
    await simulatePreview({ workspace_id: 'ws1', start: 'start-node' });
    expect(spy).toHaveBeenCalledWith(
      '/admin/preview/transitions/simulate',
      { workspace_id: 'ws1', start: 'start-node' },
    );
  });
});

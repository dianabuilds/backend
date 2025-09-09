import { afterEach, describe, expect, it, vi } from 'vitest';

import { accountApi } from './accountApi';
import { listNodes, patchNode } from './nodes';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('patchNode', () => {
  it('sends payload to /admin/nodes with next=1', async () => {
    const spy = vi.spyOn(accountApi, 'patch').mockResolvedValue({} as never);
    await patchNode('ws1', 1, {
      coverUrl: 'x',
      media: ['m1'],
      tags: ['t1'],
      content: { foo: 'bar' },
    });
    expect(spy).toHaveBeenCalledWith(
      '/admin/nodes/1',
      { coverUrl: 'x', media: ['m1'], tags: ['t1'], content: { foo: 'bar' } },
      expect.objectContaining({ accountId: '', account: false, params: { next: 1 } }),
    );
  });
});

describe('listNodes', () => {
  it('requests unified admin route', async () => {
    const spy = vi.spyOn(accountApi, 'get').mockResolvedValue({
      status: 200,
      data: [
        {
          status: 'ok',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      ],
    } as never);
    const res = await listNodes('ws1');
    expect(spy).toHaveBeenCalledTimes(1);
    expect(spy).toHaveBeenCalledWith(
      '/admin/nodes',
      expect.objectContaining({
        accountId: 'ws1',
        account: false,
        raw: true,
        acceptNotModified: true,
      }),
    );
    expect(res).toEqual([
      {
        status: 'ok',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-02T00:00:00Z',
      },
    ]);
  });

  it('propagates 404 errors', async () => {
    vi.spyOn(accountApi, 'get').mockResolvedValue({ status: 404 } as never);
    await expect(listNodes('ws1')).rejects.toMatchObject({ response: { status: 404 } });
  });
});

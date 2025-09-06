import { afterEach, describe, expect, it, vi } from 'vitest';

import { AdminService } from '../openapi';
import { listNodes, patchNode } from './nodes';
import { wsApi } from './wsApi';

afterEach(() => {
  vi.restoreAllMocks();
});

describe('patchNode', () => {
  it('sends payload without legacy aliases', async () => {
    const spy = vi
      .spyOn(AdminService, 'updateNodeByIdAdminWorkspacesWorkspaceIdNodesNodeIdPatch')
      .mockResolvedValue({} as never);
    await patchNode('ws1', 1, {
      coverUrl: 'x',
      media: ['m1'],
      tags: ['t1'],
      content: { foo: 'bar' },
    });
    expect(spy).toHaveBeenCalledWith(
      1,
      'ws1',
      { coverUrl: 'x', media: ['m1'], tags: ['t1'], content: { foo: 'bar' } },
      1,
    );
  });
});

describe('listNodes', () => {
  it('requests admin workspace route only', async () => {
    const spy = vi.spyOn(wsApi, 'get').mockResolvedValue({
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
      '/admin/accounts/ws1/nodes',
      expect.objectContaining({ workspace: false, raw: true, acceptNotModified: true }),
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
    vi.spyOn(wsApi, 'get').mockResolvedValue({ status: 404 } as never);
    await expect(listNodes('ws1')).rejects.toMatchObject({ response: { status: 404 } });
  });
});

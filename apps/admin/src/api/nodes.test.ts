import { vi, describe, it, expect } from 'vitest';
import { AdminService } from '../openapi';
import { patchNode } from './nodes';

describe('patchNode', () => {
  it('sends payload without legacy aliases', async () => {
    const spy = vi
      .spyOn(AdminService, 'updateNodeByIdAdminWorkspacesWorkspaceIdNodesNodeIdPatch')
      .mockResolvedValue({} as any);
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

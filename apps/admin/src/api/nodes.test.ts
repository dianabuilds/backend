import { vi, describe, it, expect } from 'vitest';
import { AdminService } from '../openapi';
import { patchNode } from './nodes';

describe('patchNode', () => {
  it('maps content field to nodes before sending', async () => {
    const spy = vi
      .spyOn(AdminService, 'updateNodeByIdAdminWorkspacesWorkspaceIdNodesNodeIdPatch')
      .mockResolvedValue({} as any);
    await patchNode('ws1', 123, { content: { foo: 'bar' } });
    expect(spy).toHaveBeenCalledWith(123, 'ws1', { nodes: { foo: 'bar' } }, 1);
  });

  it('expands tag aliases and waits for echo by default', async () => {
    const spy = vi
      .spyOn(AdminService, 'updateNodeByIdAdminWorkspacesWorkspaceIdNodesNodeIdPatch')
      .mockResolvedValue({} as any);
    await patchNode('ws1', 1, {
      coverUrl: 'x',
      media: ['m1'],
      tags: ['t1'],
    });
    expect(spy).toHaveBeenCalledWith(
      1,
      'ws1',
      {
        coverUrl: 'x',
        media: ['m1'],
        tags: ['t1'],
        tagSlugs: ['t1'],
        tag_slugs: ['t1'],
      },
      1,
    );
  });
});

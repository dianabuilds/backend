import { vi, describe, it, expect } from 'vitest';
import { AdminService } from '../openapi';
import { patchNode } from './nodes';

describe('patchNode', () => {
  it('maps content field to nodes before sending', async () => {
    const spy = vi
      .spyOn(AdminService, 'updateNodeByIdAdminWorkspacesWorkspaceIdNodesNodeIdPatch')
      .mockResolvedValue({} as any);
    await patchNode('ws1', '123', { content: { foo: 'bar' } });
    expect(spy).toHaveBeenCalledWith('123', 'ws1', { nodes: { foo: 'bar' } }, undefined);
  });
});

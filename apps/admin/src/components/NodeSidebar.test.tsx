import '@testing-library/jest-dom';

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import NodeSidebar from './NodeSidebar';

vi.mock('../api/flags', () => ({
  listFlags: vi.fn().mockResolvedValue([]),
}));

vi.mock('../api/nodes', () => ({
  patchNode: vi.fn().mockResolvedValue({}),
  publishNode: vi.fn().mockResolvedValue({}),
  archiveNode: vi.fn().mockResolvedValue({}),
  duplicateNode: vi.fn().mockResolvedValue({}),
  previewNode: vi.fn().mockResolvedValue({}),
}));

vi.mock('../api/accountApi', () => ({
  accountApi: { request: vi.fn() },
}));

vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({ user: { role: 'admin' } }),
}));

vi.mock('../utils/compressImage', () => ({
  compressImage: vi.fn(),
}));

describe('NodeSidebar', () => {
  const node = {
    id: '1',
    slug: 'node-1',
    authorId: 'user',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    isPublic: true,
    publishedAt: null,
    nodeType: 'text',
    coverUrl: null,
    coverAssetId: null,
    coverAlt: '',
    coverMeta: null,
    allowFeedback: true,
    premiumOnly: false,
  };

  it('renders actions menu and calls publish', async () => {
    const { publishNode } = await import('../api/nodes');
    render(<NodeSidebar node={node} accountId="ws" />);
    await screen.findByText('Visibility');
    const btn = screen.getByRole('button', { name: /Publish/i });
    fireEvent.click(btn);
    expect(publishNode).toHaveBeenCalled();
  });
});

import '@testing-library/jest-dom';

import { render, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import NodeEditorPage from './NodeEditor';

vi.mock('../../../components/publish/PublishControls', () => ({
  default: () => <div data-testid="publish-controls" />,
}));

vi.mock('../../../account/AccountContext', () => ({
  useAccount: () => ({ accountId: 'ws1' }),
}));

vi.mock('../hooks/useNodeEditor', () => ({
  default: () => ({
    node: {
      id: 1,
      title: 'Test',
      slug: '',
      coverUrl: null,
      media: [],
      tags: [],
      isPublic: false,
      content: { time: 0, blocks: [], version: '2.30.7' },
    },
    update: vi.fn(),
    save: vi.fn(),
    loading: false,
    error: null,
    isSaving: false,
    isNew: false,
  }),
}));

describe('NodeEditorPage', () => {
  it('renders publish controls for existing node', () => {
    const { getByTestId } = render(
      <MemoryRouter initialEntries={['/nodes/article/1']}>
        <Routes>
          <Route path="/nodes/:type/:id" element={<NodeEditorPage />} />
        </Routes>
      </MemoryRouter>
    );
    const sidebar = getByTestId('sidebar');
    expect(within(sidebar).getByTestId('publish-controls')).toBeInTheDocument();
  });
  it('renders access controls and context switcher', () => {
    const { getByTestId } = render(
      <MemoryRouter initialEntries={['/nodes/article/1']}>
        <Routes>
          <Route path="/nodes/:type/:id" element={<NodeEditorPage />} />
        </Routes>
      </MemoryRouter>
    );
    const sidebar = getByTestId('sidebar');
    expect(within(sidebar).getByTestId('space-selector')).toBeInTheDocument();
    expect(within(sidebar).getByTestId('role-reader')).toBeInTheDocument();
    expect(within(sidebar).getByTestId('override-toggle')).toBeInTheDocument();
    expect(getByTestId('context-switcher')).toBeInTheDocument();
  });
});

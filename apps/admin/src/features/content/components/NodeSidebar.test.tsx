import '@testing-library/jest-dom';

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import NodeSidebar from './NodeSidebar';

vi.mock('../../../components/publish/PublishControls', () => ({
  default: () => <div data-testid="publish-controls" />,
}));

describe('NodeSidebar', () => {
  const node = { id: 1, title: 'Test', slug: 'test' };

  it('omits validation and advanced sections', () => {
    render(<NodeSidebar node={node} accountId="ws" onChange={() => {}} />);
    expect(screen.queryByText('Validation')).toBeNull();
    expect(screen.queryByText('Advanced')).toBeNull();
  });
});

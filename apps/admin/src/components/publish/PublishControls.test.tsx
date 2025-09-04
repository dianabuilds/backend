import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

import PublishControls from './PublishControls';

vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn().mockReturnValue({
    data: { status: 'draft' },
    isLoading: false,
    refetch: vi.fn(),
  }),
  useMutation: () => ({ mutate: vi.fn(), isPending: false }),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

vi.mock('../../api/publish', () => ({
  cancelScheduledPublish: vi.fn(),
  getPublishInfo: vi.fn(),
  publishNow: vi.fn(),
  schedulePublish: vi.fn(),
}));

vi.mock('../../api/nodes', () => ({ patchNode: vi.fn() }));

vi.mock('../ToastProvider', () => ({ useToast: () => ({ addToast: vi.fn() }) }));

describe('PublishControls', () => {
  it('renders status section', () => {
    render(<PublishControls workspaceId="ws" nodeId={1} />);
    expect(screen.getByText('Статус:')).toBeInTheDocument();
  });
});

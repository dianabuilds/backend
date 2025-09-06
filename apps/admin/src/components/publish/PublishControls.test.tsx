import '@testing-library/jest-dom';

import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import PublishControls from './PublishControls';

const mockUseMutation = vi.fn();
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn().mockReturnValue({
    data: { status: 'draft' },
    isLoading: false,
    refetch: vi.fn(),
  }),
  useMutation: (...args: unknown[]) => mockUseMutation(...args),
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
    mockUseMutation.mockReturnValue({ mutate: vi.fn(), isPending: false });
    render(<PublishControls accountId="ws" nodeId={1} />);
    expect(screen.getByText('Статус:')).toBeInTheDocument();
  });

  it('shows spinner while publish mutation pending', () => {
    mockUseMutation.mockReset();
    mockUseMutation
      .mockReturnValueOnce({ mutate: vi.fn(), isPending: true })
      .mockReturnValue({ mutate: vi.fn(), isPending: false });
    render(<PublishControls accountId="ws" nodeId={1} />);
    expect(screen.getByTestId('publish-spinner')).toBeInTheDocument();
  });
});

import '@testing-library/jest-dom';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import { listFlags, updateFlag } from '../api/flags';
import FeatureFlagsPage from './FeatureFlags';

vi.mock('../api/flags', () => ({
  listFlags: vi.fn(),
  updateFlag: vi.fn(),
}));

vi.mock('../account/AccountContext', () => ({
  useAccount: () => ({ accountId: '' }),
}));

function renderPage() {
  const qc = new QueryClient();
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <FeatureFlagsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('FeatureFlagsPage', () => {
  afterEach(() => vi.restoreAllMocks());

  it('filters flags by key via API', async () => {
    vi.mocked(listFlags)
      .mockResolvedValueOnce([
        {
          key: 'a',
          value: false,
          description: 'A',
          audience: 'all',
          updated_at: null,
          updated_by: null,
        },
        {
          key: 'b',
          value: false,
          description: 'B',
          audience: 'all',
          updated_at: null,
          updated_by: null,
        },
      ])
      .mockResolvedValueOnce([
        {
          key: 'a',
          value: false,
          description: 'A',
          audience: 'all',
          updated_at: null,
          updated_by: null,
        },
      ]);
    renderPage();
    await waitFor(() => expect(listFlags).toHaveBeenCalled());
    fireEvent.change(screen.getByLabelText(/filter by key/i), {
      target: { value: 'a' },
    });
    await waitFor(() =>
      expect(listFlags).toHaveBeenLastCalledWith({
        q: 'a',
        limit: 50,
        offset: 0,
      }),
    );
  });

  it('allows editing flag in modal', async () => {
    vi.mocked(listFlags).mockResolvedValue([
      {
        key: 'test',
        value: false,
        description: '',
        audience: 'all',
        updated_at: null,
        updated_by: null,
      },
    ]);
    const updateSpy = vi.mocked(updateFlag).mockResolvedValue({
      key: 'test',
      value: true,
      description: 'new',
      audience: 'beta',
      updated_at: '2024-01-01T00:00:00Z',
      updated_by: 'me',
    });
    renderPage();
    await waitFor(() => screen.getByText('test'));
    fireEvent.click(screen.getByText('test'));
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: 'new' },
    });
    fireEvent.click(screen.getByLabelText(/enabled/i));
    fireEvent.change(screen.getByLabelText(/audience/i), {
      target: { value: 'beta' },
    });
    fireEvent.click(screen.getByRole('button', { name: /save/i }));
    await waitFor(() =>
      expect(updateSpy).toHaveBeenCalledWith('test', {
        description: 'new',
        value: true,
        audience: 'beta',
      }),
    );
  });

  it('renders referrals program flag', async () => {
    vi.mocked(listFlags).mockResolvedValue([
      {
        key: 'referrals.program',
        value: false,
        description: '',
        audience: 'all',
        updated_at: null,
        updated_by: null,
      },
    ]);
    renderPage();
    await waitFor(() => screen.getByText('referrals.program'));
    expect(screen.getByText('referrals.program')).toBeInTheDocument();
  });
});

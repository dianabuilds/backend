import '@testing-library/jest-dom';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import { type AlertItem, getAlerts } from '../api/alerts';
import AlertsBadge from './AlertsBadge';

vi.mock('../api/alerts', () => ({
  getAlerts: vi.fn(),
}));

function renderWithClient() {
  const qc = new QueryClient();
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AlertsBadge />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('AlertsBadge', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows badge when alerts exist', async () => {
    vi.mocked(getAlerts).mockResolvedValue([
      { id: '1', startsAt: '2024-01-01T00:00:00Z', description: 'boom' },
    ] as AlertItem[]);
    renderWithClient();
    await waitFor(() => expect(screen.getByTestId('alerts-badge')).toHaveTextContent('1'));
  });

  it('hides badge when no alerts', async () => {
    vi.mocked(getAlerts).mockResolvedValue([]);
    renderWithClient();
    await waitFor(() => {
      expect(screen.queryByTestId('alerts-badge')).toBeNull();
    });
  });
});

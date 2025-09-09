import '@testing-library/jest-dom';

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import { api } from '../api/client';
import SystemStatus from './SystemStatus';

describe('SystemStatus', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows green and red indicators', async () => {
    vi.spyOn(api, 'get').mockResolvedValue({
      data: {
        ready: { db: 'ok', redis: 'fail', queue: 'ok', ai: 'ok', payment: 'ok' },
      },
    } as unknown as import('../api/client').ApiResponse<{ ready: Record<string, string> }>);

    render(<SystemStatus />);
    await waitFor(() => expect(screen.getByTestId('status-dot-db')).toHaveClass('bg-green-500'));
    expect(screen.getByTestId('status-dot-redis')).toHaveClass('bg-red-500');
  });

  it('displays error text on fetch failure', async () => {
    vi.spyOn(api, 'get').mockRejectedValue(new Error('boom'));
    render(<SystemStatus />);
    await waitFor(() => expect(screen.getByTestId('status-dot-db')).toHaveClass('bg-red-500'));
    fireEvent.click(screen.getByTestId('system-status-button'));
    expect(await screen.findByTestId('error-text')).toHaveTextContent('boom');
  });
});

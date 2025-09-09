import '@testing-library/jest-dom';

import { act, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import { api } from '../api/client';
import LimitBadge from './LimitBadge';
import { handleLimit429, refreshLimits } from './LimitBadgeController';

describe('LimitBadge', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('updates count and message', async () => {
    const getSpy = vi
      .spyOn(api, 'get')
      .mockResolvedValueOnce({ data: { compass_calls: 5 } } as unknown as {
        data: Record<string, number>;
      })
      .mockResolvedValueOnce({ data: { compass_calls: 3 } } as unknown as {
        data: Record<string, number>;
      })
      .mockResolvedValueOnce({ data: { compass_calls: 3 } } as unknown as {
        data: Record<string, number>;
      })
      .mockResolvedValueOnce({ data: { compass_calls: 2 } } as unknown as {
        data: Record<string, number>;
      });

    render(<LimitBadge limitKey="compass_calls" />);

    await waitFor(() => expect(screen.getByTestId('limit-compass_calls')).toHaveTextContent('5'));

    await act(async () => {
      await refreshLimits();
    });
    await waitFor(() => expect(screen.getByTestId('limit-compass_calls')).toHaveTextContent('3'));

    await act(async () => {
      await handleLimit429('compass_calls', 9);
    });
    await waitFor(() =>
      expect(screen.getByTestId('limit-compass_calls')).toHaveAttribute('title', 'try again in 9s'),
    );

    await act(async () => {
      await refreshLimits();
    });
    await waitFor(() => expect(screen.getByTestId('limit-compass_calls')).toHaveTextContent('2'));
    expect(screen.getByTestId('limit-compass_calls')).not.toHaveAttribute('title');
    expect(getSpy).toHaveBeenCalledTimes(4);
  });
});

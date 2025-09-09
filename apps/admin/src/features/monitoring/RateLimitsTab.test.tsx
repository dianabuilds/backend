import '@testing-library/jest-dom';

import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import { api } from '../../api/client';
import RateLimitsTab from './RateLimitsTab';

describe('RateLimitsTab', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('displays status and saves rule', async () => {
    vi.spyOn(api, 'get').mockImplementation((url: string) => {
      if (url === '/admin/ratelimit/rules') {
        return Promise.resolve({
          data: { enabled: true, rules: { foo: '5/min' } },
        } as unknown as import('../../api/client').ApiResponse<{
          enabled: boolean;
          rules: Record<string, string>;
        }>);
      }
      if (url === '/admin/ratelimit/recent429') {
        return Promise.resolve({ data: [] } as unknown as import('../../api/client').ApiResponse<
          unknown[]
        >);
      }
      throw new Error('unexpected url ' + url);
    });
    const patch = vi
      .spyOn(api, 'patch')
      .mockResolvedValue({} as unknown as import('../../api/client').ApiResponse<unknown>);

    render(<RateLimitsTab />);

    await screen.findByText('Enabled');
    const input = await screen.findByDisplayValue('5/min');
    fireEvent.change(input, { target: { value: '10/min' } });
    fireEvent.click(screen.getByText('Save'));

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith('/admin/ratelimit/rules', {
        key: 'foo',
        rule: '10/min',
      }),
    );
  });
});

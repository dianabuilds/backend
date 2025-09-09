import '@testing-library/jest-dom';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import { api } from '../api/client';
import Profile from './Profile';

vi.mock('../api/client', () => ({
  api: { get: vi.fn(), patch: vi.fn() },
}));

const addToast = vi.fn();
vi.mock('../components/ToastProvider', () => ({
  useToast: () => ({ addToast }),
}));

describe('Profile', () => {
  it('validates and saves profile fields', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/users/me') {
        return {
          data: {
            username: 'user1',
            bio: 'bio1',
            avatar_url: 'http://a',
          },
        } as unknown as {
          data: { username: string; bio: string; avatar_url: string };
        };
      }
      if (url === '/users/me/profile') {
        return {
          data: { timezone: null, locale: null },
        } as unknown as {
          data: { timezone: string | null; locale: string | null };
        };
      }
      throw new Error('unknown url');
    });
    vi.mocked(api.patch).mockClear();
    vi.mocked(api.patch).mockResolvedValue({} as unknown);
    addToast.mockReset();

    const qc = new QueryClient();
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Profile />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    await waitFor(() =>
      expect((screen.getByLabelText(/username/i) as HTMLInputElement).value).toBe('user1'),
    );

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: '' },
    });
    fireEvent.click(screen.getByText(/save profile/i));
    await waitFor(() =>
      expect(addToast).toHaveBeenCalledWith({
        title: 'Username is required',
        variant: 'error',
      }),
    );
    expect(api.patch).not.toHaveBeenCalled();

    addToast.mockClear();
    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'newu' },
    });
    fireEvent.change(screen.getByLabelText(/bio/i), {
      target: { value: 'new bio' },
    });
    fireEvent.change(screen.getByLabelText(/avatar url/i), {
      target: { value: 'http://example.com/a.png' },
    });
    fireEvent.click(screen.getByText(/save profile/i));
    await waitFor(() =>
      expect(api.patch).toHaveBeenCalledWith('/users/me', {
        username: 'newu',
        bio: 'new bio',
        avatar_url: 'http://example.com/a.png',
      }),
    );
    expect(addToast).toHaveBeenCalledWith({
      title: 'Profile saved',
      variant: 'success',
    });
  });
});

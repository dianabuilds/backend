import '@testing-library/jest-dom';

import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';

import Sidebar from './Sidebar';

vi.mock('../api/client', () => ({
  getAdminMenu: vi.fn(),
}));

vi.mock('../auth/AuthContext', () => ({
  useAuth: () => ({
    user: { role: 'admin' },
    login: vi.fn(),
    logout: vi.fn(),
    ready: true,
  }),
}));

import { getAdminMenu } from '../api/client';

describe('Sidebar', () => {
  it('shows menu groups', async () => {
    const mocked = vi.mocked(
      getAdminMenu as unknown as typeof getAdminMenu & {
        mockResolvedValue: (v: unknown) => unknown;
      },
    );
    mocked.mockResolvedValue({
      items: [
        {
          id: 'content',
          label: 'Content',
          children: [
            { id: 'nodes', label: 'Nodes', path: '/nodes', order: 1 },
            { id: 'quests', label: 'Quests', path: '/quests', order: 2 },
          ],
        },
        {
          id: 'navigation',
          label: 'Navigation',
          children: [{ id: 'navigation-main', label: 'Navigation', path: '/navigation', order: 1 }],
        },
        {
          id: 'monitoring',
          label: 'Monitoring',
          children: [
            { id: 'dashboard', label: 'Dashboard', path: '/', order: 1 },
            { id: 'traces', label: 'Traces', path: '/traces', order: 2 },
          ],
        },
        {
          id: 'administration',
          label: 'Administration',
          children: [{ id: 'users-list', label: 'Users', path: '/users', order: 1 }],
        },
      ],
    } as unknown as Awaited<ReturnType<typeof getAdminMenu>>);

    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(await screen.findByText('Content')).toBeInTheDocument();
    expect(await screen.findByText('Navigation')).toBeInTheDocument();
    expect(await screen.findByText('Monitoring')).toBeInTheDocument();
  });

  it('can collapse and expand', async () => {
    const mocked = vi.mocked(
      getAdminMenu as unknown as typeof getAdminMenu & {
        mockResolvedValue: (v: unknown) => unknown;
      },
    );
    mocked.mockResolvedValue({ items: [] } as unknown as Awaited<ReturnType<typeof getAdminMenu>>);
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Sidebar />
      </MemoryRouter>,
    );
    const btn = await screen.findByLabelText('Collapse sidebar');
    fireEvent.click(btn);
    expect(await screen.findByLabelText('Expand sidebar')).toBeInTheDocument();
  });

  it('renders default icons for known items', async () => {
    const mocked = vi.mocked(
      getAdminMenu as unknown as typeof getAdminMenu & {
        mockResolvedValue: (v: unknown) => unknown;
      },
    );
    mocked.mockResolvedValue({
      items: [{ id: 'nodes', label: 'Nodes', path: '/nodes' }],
    } as unknown as Awaited<ReturnType<typeof getAdminMenu>>);
    const { container } = render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(await screen.findByText('Nodes')).toBeInTheDocument();
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg?.classList.contains('lucide-menu')).toBe(false);
  });
});

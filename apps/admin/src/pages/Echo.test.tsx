import '@testing-library/jest-dom';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import Echo from './Echo';

vi.mock('../api/client', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({}),
    del: vi.fn().mockResolvedValue({}),
  },
}));

function renderPage() {
  const qc = new QueryClient();
  render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <Echo />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('Echo page', () => {
  it('renders heading', async () => {
    renderPage();
    const heading = await screen.findByRole('heading', { name: /Эхо/i });
    expect(heading).toBeInTheDocument();
  });
});

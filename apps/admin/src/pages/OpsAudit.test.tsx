import '@testing-library/jest-dom';

import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

import { api } from '../api/client';
import OpsAudit from './OpsAudit';

vi.mock('../api/client', () => ({ api: { get: vi.fn() } }));

describe('OpsAudit page', () => {
  afterEach(() => vi.restoreAllMocks());

  it('loads audit entries', async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: { items: [{ id: '1', actor: 'u', action: 'a' }] },
    });
    render(
      <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <OpsAudit />
      </MemoryRouter>,
    );
    await waitFor(() => screen.getByText('u'));
    expect(api.get).toHaveBeenCalledWith('/admin/audit');
  });
});

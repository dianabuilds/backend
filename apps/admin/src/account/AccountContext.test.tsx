import '@testing-library/jest-dom';

import { render, screen, waitFor } from '@testing-library/react';
import type { Mock } from 'vitest';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { api } from '../api/client';
import type { Account } from '../api/types';
import { safeLocalStorage } from '../utils/safeStorage';
import { AccountBranchProvider, useAccount } from './AccountContext';

vi.mock('../api/client', () => ({
  api: { get: vi.fn() },
}));

function ShowAccount() {
  const { accountId } = useAccount();
  return <div data-testid="ws">{accountId}</div>;
}

describe('AccountBranchProvider', () => {
  beforeEach(() => {
    safeLocalStorage.clear();
    (api.get as Mock).mockReset();
    window.history.replaceState({}, '', '/');
  });

  it('uses server default account', async () => {
    (api.get as Mock).mockImplementation(async (url: string) => {
      if (url === '/users/me') return { data: { default_account_id: 'did' } };
      throw new Error('unknown url');
    });
    render(
      <AccountBranchProvider>
        <ShowAccount />
      </AccountBranchProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('ws').textContent).toBe('did'));
    expect(api.get).toHaveBeenCalledWith('/users/me');
  });
  it('falls back to global account', async () => {
    (api.get as Mock).mockImplementation(async (url: string) => {
      if (url === '/users/me') return { data: { default_account_id: null } };
      if (url === '/accounts') {
        const accounts: Account[] = [{ id: 'gid', slug: 'global', type: 'global' }];
        return { data: accounts };
      }
      throw new Error('unknown url');
    });
    render(
      <AccountBranchProvider>
        <ShowAccount />
      </AccountBranchProvider>,
    );
    await waitFor(() => expect(screen.getByTestId('ws').textContent).toBe('gid'));
    expect(api.get).toHaveBeenCalledWith('/accounts');
  });
});

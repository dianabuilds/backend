/* eslint react-refresh/only-export-components: off */
import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from 'react';

import { api } from '../api/client';
import type { Account } from '../api/types';
import { safeLocalStorage } from '../utils/safeStorage';

function persistAccountId(id: string | null) {
  if (id) safeLocalStorage.setItem('accountId', id);
  else safeLocalStorage.removeItem('accountId');
}

interface AccountContextType {
  accountId: string;
  setAccount: (account: Account | undefined) => void;
}

const AccountContext = createContext<AccountContextType>({
  accountId: '',
  setAccount: () => {},
});

function updateUrl(id: string) {
  try {
    const url = new URL(window.location.href);
    if (id) url.searchParams.set('account_id', id);
    else url.searchParams.delete('account_id');
    window.history.replaceState({}, '', url.pathname + url.search + url.hash);
  } catch {
    // ignore
  }
}

export function AccountBranchProvider({ children }: { children: ReactNode }) {
  const [accountId, setAccountIdState] = useState<string>(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const fromUrl = params.get('account_id') || '';
      const stored = safeLocalStorage.getItem('accountId') || '';
      return fromUrl || stored;
    } catch {
      return '';
    }
  });

  const setAccount = useCallback((account: Account | undefined) => {
    const id = account?.id ?? '';
    setAccountIdState(id);
    persistAccountId(id || null);
    updateUrl(id);
  }, []);

  // Persist and reflect in URL whenever accountId changes
  useEffect(() => {
    persistAccountId(accountId || null);
    updateUrl(accountId);
  }, [accountId]);

  // Bootstrap: if accountId not resolved from URL/storage, fetch defaults
  useEffect(() => {
    if (accountId) return; // already resolved
    let cancelled = false;
    (async () => {
      try {
        // Try server-provided default account
        const me = await api.get('/users/me');
        const did =
          (me?.data as { default_account_id?: string | null } | undefined)?.default_account_id ??
          null;
        if (!cancelled && did) {
          setAccountIdState(did);
          return;
        }
      } catch {
        // ignore and try fallback
      }
      try {
        // Fallback: query available accounts and pick global, then first
        const resp = await api.get('/accounts');
        const accounts = (resp?.data as Account[]) ?? [];
        const global = accounts.find((a) => a.type === 'global') ?? accounts[0];
        if (!cancelled && global) {
          setAccountIdState(global.id);
        }
      } catch {
        // ignore – leave accountId empty
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accountId]);

  return (
    <AccountContext.Provider value={{ accountId, setAccount }}>{children}</AccountContext.Provider>
  );
}

export function useAccount() {
  return useContext(AccountContext);
}

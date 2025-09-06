/* eslint react-refresh/only-export-components: off */
import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react";

import { api } from "../api/client";
import type { Account } from "../api/types";
import { safeLocalStorage } from "../utils/safeStorage";

function persistAccountId(id: string | null) {
  if (id) safeLocalStorage.setItem("accountId", id);
  else safeLocalStorage.removeItem("accountId");
}

interface AccountContextType {
  accountId: string;
  setAccount: (account: Account | undefined) => void;
}

const AccountContext = createContext<AccountContextType>({
  accountId: "",
  setAccount: () => {},
});

function updateUrl(id: string) {
  try {
    const url = new URL(window.location.href);
    if (id) url.searchParams.set("account_id", id);
    else url.searchParams.delete("account_id");
    window.history.replaceState({}, "", url.pathname + url.search + url.hash);
  } catch {
    // ignore
  }
}

export function AccountBranchProvider({ children }: { children: ReactNode }) {
  const [accountId, setAccountIdState] = useState<string>(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const fromUrl = params.get("account_id") || "";
      const stored = safeLocalStorage.getItem("accountId") || "";
      return fromUrl || stored;
    } catch {
      return "";
    }
  });

  const setAccount = useCallback((ws: Account | undefined) => {
    const id = ws?.id ?? "";
    setAccountIdState(id);
    persistAccountId(id || null);
    updateUrl(id);
  }, []);

  useEffect(() => {
    persistAccountId(accountId || null);
    updateUrl(accountId);
  }, [accountId]);

  useEffect(() => {
    if (accountId) return;
    (async () => {
      try {
        const me = await api.get<{ default_account_id: string | null }>(
          "/users/me",
        );
        const defId = me.data?.default_account_id;
        if (defId) {
          setAccountIdState(defId);
          persistAccountId(defId);
          updateUrl(defId);
          return;
        }
      } catch {
        // ignore
      }
      try {
        const res = await api.get<Account[] | { accounts: Account[] }>(
          "/accounts",
        );
        const payload = Array.isArray(res.data)
          ? res.data
          : res.data?.accounts || [];
        const globalWs = payload.find(
          (ws) => ws.type === "global" || ws.slug === "global",
        );
        if (globalWs) {
          setAccountIdState(globalWs.id);
          persistAccountId(globalWs.id);
          updateUrl(globalWs.id);
        }
      } catch {
        // ignore
      }
    })();
  }, [accountId]);

  return (
    <AccountContext.Provider value={{ accountId, setAccount }}>
      {children}
    </AccountContext.Provider>
  );
}

export function useAccount() {
  return useContext(AccountContext);
}

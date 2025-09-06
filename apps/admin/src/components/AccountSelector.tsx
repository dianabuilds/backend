import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAccount } from "../account/AccountContext";
import { api } from "../api/client";
import type { Account } from "../api/types";
import ErrorBanner from "./ErrorBanner";

export default function AccountSelector() {
  const { accountId, setAccount } = useAccount();

  const { data, error } = useQuery({
    queryKey: ["accounts"],
    queryFn: async () => {
      const res = await api.get<Account[] | { accounts: Account[] }>(
        "/admin/accounts",
      );
      const data = res.data;
      if (Array.isArray(data)) return data;
      return data?.accounts ?? [];
    },
  });

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (!accountId && data && data.length > 0) {
      setOpen(true);
    }
  }, [accountId, data]);

  useEffect(() => {
    if (accountId && data && !data.some((acc) => acc.id === accountId)) {
      setAccount(undefined);
    }
  }, [accountId, data, setAccount]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    const onMissing = () => setOpen(true);
    document.addEventListener("keydown", onKeyDown);
    window.addEventListener("account-missing", onMissing);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("account-missing", onMissing);
    };
  }, []);

  const selected = data?.find((acc) => acc.id === accountId);

  const items = (data || []).filter(
    (acc) =>
      acc.name.toLowerCase().includes(query.toLowerCase()) ||
      acc.slug.toLowerCase().includes(query.toLowerCase()),
  );

  const onSelect = (account: Account) => {
    setAccount(account);
    setOpen(false);
    setQuery("");
    setActive(0);
  };

  const onInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => (a + 1) % items.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => (a - 1 + items.length) % items.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      const acc = items[active];
      if (acc) onSelect(acc);
    }
  };

  if (error) {
    return (
      <ErrorBanner message="Не удалось загрузить список аккаунтов.">
        <span>Возможно, вы не авторизованы. </span>
        <Link to="/login" className="text-blue-600 hover:underline">
          Авторизоваться
        </Link>
      </ErrorBanner>
    );
  }

  if (data && data.length === 0) {
    return (
      <Link to="/accounts" className="text-blue-600 hover:underline">
        Создать аккаунт
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-2 mr-4">
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="px-2 py-1 border rounded bg-white text-sm dark:bg-gray-800"
        title={selected ? selected.name : "Выбрать аккаунт"}
      >
        {selected ? selected.name : "Select account"}
      </button>
      <Link
        to="/accounts"
        title="Список аккаунтов"
        className="text-gray-600 hover:text-gray-900"
      >
        📂
      </Link>
      {accountId && selected && (
        <Link
          to={`/accounts/${accountId}`}
          title={`Settings for ${selected.name}`}
          className="text-gray-600 hover:text-gray-900"
        >
          ⚙
        </Link>
      )}
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-24">
          <div className="w-80 rounded-lg bg-white dark:bg-gray-800 p-2">
            <input
              autoFocus
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setActive(0);
              }}
              onKeyDown={onInputKeyDown}
              placeholder="Search account..."
              className="w-full mb-2 px-2 py-1 border rounded bg-gray-50 dark:bg-gray-700"
            />
            <div className="max-h-60 overflow-y-auto">
              {items.map((acc, idx) => (
                <button
                  key={acc.id}
                  onClick={() => onSelect(acc)}
                  className={`block w-full px-2 py-1 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                    idx === active ? "bg-gray-100 dark:bg-gray-700" : ""
                  }`}
                >
                  <div className="font-medium">{acc.name}</div>
                  <div className="text-xs text-gray-500">
                    {acc.slug} • {acc.role}
                  </div>
                </button>
              ))}
              {items.length === 0 && (
                <div className="px-2 py-1 text-sm text-gray-500">No accounts</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


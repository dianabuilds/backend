import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { type Account,listAccounts } from "../api/accounts";
import { api } from "../api/client";
import { useToast } from "../components/ToastProvider";
import type { AccountMemberOut } from "../openapi";
import { confirmDialog, promptDialog } from "../shared/ui";
import PageLayout from "./_shared/PageLayout";

const PAGE_SIZE = 50;

export default function Accounts() {
  const { addToast } = useToast();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["accounts-list", search, typeFilter],
    queryFn: ({ pageParam = 0 }) =>
      listAccounts({
        q: search || undefined,
        type: typeFilter || undefined,
        limit: PAGE_SIZE,
        offset: pageParam * PAGE_SIZE,
      }),
    getNextPageParam: (lastPage, pages) =>
      lastPage.length === PAGE_SIZE ? pages.length : undefined,
    initialPageParam: 0,
  });

  const accounts = useMemo(() => data?.pages.flat() ?? [], [data]);

  const [memberCounts, setMemberCounts] = useState<Record<string, number>>({});
  useEffect(() => {
    if (accounts.length === 0) return;
    Promise.all(
      accounts.map(async (account) => {
        const res = await api.get<AccountMemberOut[]>(
          `/admin/accounts/${account.id}/members`,
        );
        return [account.id, (res.data ?? []).length] as [string, number];
      }),
    ).then((entries) => setMemberCounts(Object.fromEntries(entries)));
  }, [accounts]);

  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["accounts-list"] });

  const handleCreate = async () => {
    const name = await promptDialog("Название аккаунта?");
    if (!name) return;
    const slug =
      (await promptDialog(
        "Откуда (slug)?",
        name.toLowerCase().replace(/[^a-z0-9]+/g, "-"),
      )) || "";
    const type =
      ((await promptDialog("Тип (team/personal/global)?", "team")) as
        | "team"
        | "personal"
        | "global"
        | null) || "team";
    try {
      await api.post("/admin/accounts", { name, slug, type });
      refresh();
      addToast({ title: "Аккаунт создан", variant: "success" });
    } catch (e) {
      addToast({
        title: "Не удалось создать аккаунт",
        description: String(e),
        variant: "error",
      });
    }
  };

  const handleEdit = async (account: Account) => {
    const name = await promptDialog("Название аккаунта?", account.name);
    if (!name) return;
    const slug = (await promptDialog("Откуда (slug)?", account.slug)) || account.slug;
    const type =
      ((await promptDialog("Тип (team/personal/global)?", account.type)) as
        | "team"
        | "personal"
        | "global"
        | null) || account.type;
    try {
      await api.patch(`/admin/accounts/${account.id}`, { name, slug, type });
      refresh();
      addToast({ title: "Аккаунт обновлён", variant: "success" });
    } catch (e) {
      addToast({
        title: "Не удалось обновить аккаунт",
        description: String(e),
        variant: "error",
      });
    }
  };

  const handleDelete = async (account: Account) => {
    if (!(await confirmDialog(`Удалить аккаунт "${account.name}"?`))) return;
    try {
      await api.del(`/admin/accounts/${account.id}`);
      refresh();
      addToast({ title: "Аккаунт удалён", variant: "success" });
    } catch (e) {
      addToast({
        title: "Не удалось удалить аккаунт",
        description: String(e),
        variant: "error",
      });
    }
  };

  useEffect(() => {
    if (error) {
      addToast({
        title: "Не удалось загрузить аккаунты",
        description: String(error),
        variant: "error",
      });
    }
  }, [error, addToast]);

  return (
    <PageLayout title="Аккаунты">
      <div className="flex gap-2 mb-4">
        <input
          className="border rounded px-2 py-1"
          placeholder="Поиск..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="border rounded px-2 py-1"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">Все типы</option>
          <option value="team">командный</option>
          <option value="personal">персональный</option>
          <option value="global">глобальный</option>
        </select>
        <button
          className="px-2 py-1 bg-blue-500 text-white rounded"
          onClick={handleCreate}
        >
          Создать аккаунт
        </button>
      </div>
      {isLoading && <div>Загрузка...</div>}
      {!isLoading && !error && (
        <>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="p-2 text-left">Название</th>
                <th className="p-2 text-left">Тип</th>
                <th className="p-2 text-left">Участники</th>
                <th className="p-2 text-left">Действия</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account.id} className="border-b hover:bg-gray-50">
                  <td className="p-2">{account.name}</td>
                  <td className="p-2 capitalize">{account.type}</td>
                  <td className="p-2">{memberCounts[account.id] ?? "-"}</td>
                  <td className="p-2">
                    <button
                      className="text-blue-600 hover:underline mr-2"
                      onClick={() => handleEdit(account)}
                    >
                      Редактировать
                    </button>
                    <button
                      className="text-red-600 hover:underline"
                      onClick={() => handleDelete(account)}
                    >
                      Удалить
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {hasNextPage && (
            <div className="mt-4">
              <button
                className="px-4 py-2 bg-gray-200 rounded"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
              >
                {isFetchingNextPage ? "Загрузка..." : "Загрузить ещё"}
              </button>
            </div>
          )}
        </>
      )}
    </PageLayout>
  );
}


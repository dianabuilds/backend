import { useEffect, useMemo, useRef, useState } from "react";
import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useDebounce } from "../utils/useDebounce";

interface Restriction {
  id: string;
  type: string;
  expires_at?: string | null;
  reason?: string | null;
}

interface AdminUser {
  id: string;
  email?: string | null;
  username?: string | null;
  role: string;
  is_active: boolean;
  is_premium: boolean;
  premium_until?: string | null;
  created_at: string;
  wallet_address?: string | null;
  restrictions: Restriction[];
}

import { api } from "../api/client";
import { useToast } from "../components/ToastProvider";

function ensureArray<T>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    if (Array.isArray((obj as { items?: unknown[] }).items)) {
      return (obj as { items: T[] }).items;
    }
    if (Array.isArray((obj as { data?: unknown[] }).data)) {
      return (obj as { data: T[] }).data;
    }
  }
  return [];
}

const PAGE_SIZE = 50;

async function fetchUsers(search: string, page: number): Promise<AdminUser[]> {
  const params = new URLSearchParams();
  if (search) params.set("q", search);
  params.set("limit", PAGE_SIZE.toString());
  params.set("offset", (page * PAGE_SIZE).toString());
  const url = `/admin/users?${params.toString()}`;
  const res = await api.get(url);
  return ensureArray<AdminUser>(res.data);
}

async function updateRole(id: string, role: string) {
  await api.post(`/admin/users/${id}/role`, { role });
}

async function setPremium(id: string, is_premium: boolean, premium_until?: string | null) {
  await api.post(`/admin/users/${id}/premium`, {
    is_premium,
    premium_until: premium_until ?? null,
  });
}

async function createRestriction(user_id: string, type: string, reason?: string, expires_at?: string | null) {
  await api.post(`/admin/restrictions`, {
    user_id,
    type,
    reason: reason || undefined,
    expires_at: expires_at ?? undefined,
  });
}

async function deleteRestriction(id: string) {
  await api.del(`/admin/restrictions/${id}`);
}

export default function Users() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebounce(search, 300);
  const queryClient = useQueryClient();
  const { addToast } = useToast();
  const {
    data,
    isLoading,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["users", debouncedSearch],
    queryFn: ({ pageParam = 0 }) => fetchUsers(debouncedSearch, pageParam),
    getNextPageParam: (lastPage, pages) =>
      lastPage.length === PAGE_SIZE ? pages.length : undefined,
    initialPageParam: 0,
  });
  const users = useMemo(() => data?.pages.flat() ?? [], [data]);
  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: users.length + (hasNextPage ? 1 : 0),
    getScrollElement: () => parentRef.current,
    estimateSize: () => 56,
    overscan: 10,
  });

  useEffect(() => {
    const items = rowVirtualizer.getVirtualItems();
    if (items.length === 0) return;
    const last = items[items.length - 1];
    if (last.index >= users.length - 1 && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [rowVirtualizer, users.length, hasNextPage, isFetchingNextPage, fetchNextPage]);

  const virtualRows = rowVirtualizer.getVirtualItems();
  const totalSize = rowVirtualizer.getTotalSize();
  const paddingTop = virtualRows.length > 0 ? virtualRows[0].start : 0;
  const paddingBottom =
    virtualRows.length > 0
      ? totalSize - virtualRows[virtualRows.length - 1].end
      : 0;

  const handleRoleChange = async (id: string, role: string) => {
    try {
      await updateRole(id, role);
      queryClient.invalidateQueries({ queryKey: ["users"] });
      addToast({ title: "Role updated", description: `User role set to "${role}"`, variant: "success" });
    } catch (e) {
      addToast({ title: "Failed to update role", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  // Premium modal state
  const [premiumUser, setPremiumUser] = useState<AdminUser | null>(null);
  const [premiumFlag, setPremiumFlag] = useState<boolean>(false);
  const [premiumUntil, setPremiumUntil] = useState<string>("");

  const openPremium = (u: AdminUser) => {
    setPremiumUser(u);
    setPremiumFlag(!!u.is_premium);
    setPremiumUntil(u.premium_until ? new Date(u.premium_until).toISOString().slice(0, 16) : "");
  };
  const applyPremium = async () => {
    if (!premiumUser) return;
    try {
      await setPremium(
        premiumUser.id,
        premiumFlag,
        premiumUntil ? new Date(premiumUntil).toISOString() : null
      );
      addToast({ title: "Premium updated", variant: "success" });
      setPremiumUser(null);
      queryClient.invalidateQueries({ queryKey: ["users"] });
    } catch (e) {
      addToast({ title: "Failed to update premium", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  // Restriction modal state
  const [restrictUser, setRestrictUser] = useState<AdminUser | null>(null);
  const [restrictType, setRestrictType] = useState<string>("ban");
  const [restrictReason, setRestrictReason] = useState<string>("");
  const [restrictUntil, setRestrictUntil] = useState<string>("");

  const openRestrict = (u: AdminUser) => {
    setRestrictUser(u);
    setRestrictType("ban");
    setRestrictReason("");
    setRestrictUntil("");
  };
  const applyRestriction = async () => {
    if (!restrictUser) return;
    try {
      await createRestriction(
        restrictUser.id,
        restrictType,
        restrictReason || undefined,
        restrictUntil ? new Date(restrictUntil).toISOString() : undefined
      );
      addToast({ title: "Restriction applied", variant: "success" });
      setRestrictUser(null);
      queryClient.invalidateQueries({ queryKey: ["users"] });
    } catch (e) {
      addToast({ title: "Failed to apply restriction", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const firstBanRestriction = (u: AdminUser) => u.restrictions.find((r) => r.type === "ban");

  const unban = async (u: AdminUser) => {
    const r = firstBanRestriction(u);
    if (!r) return;
    try {
      await deleteRestriction(r.id);
      addToast({ title: "User unbanned", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["users"] });
    } catch (e) {
      addToast({ title: "Failed to unban", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Users</h1>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search by email or username"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border rounded px-3 py-1 w-64"
        />
      </div>
      {isLoading && <p>Loading...</p>}
      {error && (
        <p className="text-red-500">
          {error instanceof Error ? error.message : String(error)}
        </p>
      )}
      {!isLoading && !error && (
        <div ref={parentRef} className="max-h-[600px] overflow-auto">
          <table className="min-w-full text-sm text-left">
            <thead>
              <tr className="border-b">
                <th className="p-2">ID</th>
                <th className="p-2">Email</th>
                <th className="p-2">Username</th>
                <th className="p-2">Role</th>
                <th className="p-2">Active</th>
                <th className="p-2">Premium until</th>
                <th className="p-2">Created</th>
                <th className="p-2">Wallet</th>
                <th className="p-2">Restrictions</th>
                <th className="p-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {paddingTop > 0 && (
                <tr>
                  <td style={{ height: paddingTop }} />
                </tr>
              )}
              {virtualRows.map((virtualRow) => {
                const u = users[virtualRow.index];
                if (!u) {
                  return (
                    <tr key="loading">
                      <td colSpan={10} className="p-2 text-center">
                        {isFetchingNextPage ? "Loading..." : null}
                      </td>
                    </tr>
                  );
                }
                return (
                  <tr key={u.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="p-2 font-mono">{u.id}</td>
                    <td className="p-2">{u.email ?? ""}</td>
                    <td className="p-2">{u.username ?? ""}</td>
                    <td className="p-2">
                      <select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                        className="border rounded px-2 py-1"
                      >
                        <option value="user">user</option>
                        <option value="moderator">moderator</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                    <td className="p-2">{u.is_active ? "yes" : "no"}</td>
                    <td className="p-2">{u.premium_until ? new Date(u.premium_until).toLocaleDateString() : "-"}</td>
                    <td className="p-2">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="p-2">{u.wallet_address ?? ""}</td>
                    <td className="p-2">
                      {u.restrictions.length > 0
                        ? u.restrictions.map((r) => r.type).join(", ")
                        : "-"}
                    </td>
                    <td className="p-2 space-x-2">
                      <button
                        className="px-2 py-1 rounded border"
                        onClick={() => openPremium(u)}
                      >
                        Premium
                      </button>
                      {firstBanRestriction(u) ? (
                        <button
                          className="px-2 py-1 rounded border"
                          onClick={() => unban(u)}
                        >
                          Unban
                        </button>
                      ) : (
                        <button
                          className="px-2 py-1 rounded border"
                          onClick={() => openRestrict(u)}
                        >
                          Ban/Restrict
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
              {paddingBottom > 0 && (
                <tr>
                  <td style={{ height: paddingBottom }} />
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Premium modal */}
      {premiumUser && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 p-4 rounded shadow max-w-md w-full">
            <h2 className="text-lg font-bold mb-2">Update premium</h2>
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={premiumFlag} onChange={(e) => setPremiumFlag(e.target.checked)} />
                <span>is_premium</span>
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-sm text-gray-600">premium_until</span>
                <input
                  type="datetime-local"
                  value={premiumUntil}
                  onChange={(e) => setPremiumUntil(e.target.value)}
                  className="border rounded px-2 py-1"
                />
              </label>
            </div>
            <div className="mt-3 flex justify-end gap-2">
              <button className="px-3 py-1 rounded border" onClick={() => setPremiumUser(null)}>Cancel</button>
              <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={applyPremium}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Restriction modal */}
      {restrictUser && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 p-4 rounded shadow max-w-md w-full">
            <h2 className="text-lg font-bold mb-2">Apply restriction</h2>
            <div className="space-y-2">
              <label className="flex flex-col gap-1">
                <span className="text-sm text-gray-600">type</span>
                <select value={restrictType} onChange={(e) => setRestrictType(e.target.value)} className="border rounded px-2 py-1">
                  <option value="ban">ban</option>
                  <option value="post_restrict">post_restrict</option>
                </select>
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-sm text-gray-600">reason</span>
                <input value={restrictReason} onChange={(e) => setRestrictReason(e.target.value)} className="border rounded px-2 py-1" />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-sm text-gray-600">expires_at</span>
                <input
                  type="datetime-local"
                  value={restrictUntil}
                  onChange={(e) => setRestrictUntil(e.target.value)}
                  className="border rounded px-2 py-1"
                />
              </label>
            </div>
            <div className="mt-3 flex justify-end gap-2">
              <button className="px-3 py-1 rounded border" onClick={() => setRestrictUser(null)}>Cancel</button>
              <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={applyRestriction}>Apply</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

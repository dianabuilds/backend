import type { Account } from "./types";
import { api } from "./client";

export interface ListAccountsParams {
  q?: string;
  type?: string;
  limit?: number;
  offset?: number;
}

export async function listAccounts(
  params: ListAccountsParams = {},
): Promise<Account[]> {
  const qs = new URLSearchParams();
  if (params.q) qs.set("q", params.q);
  if (params.type) qs.set("type", params.type);
  if (typeof params.limit === "number") qs.set("limit", String(params.limit));
  if (typeof params.offset === "number") qs.set("offset", String(params.offset));
  const res = await api.get<Account[] | { accounts: Account[] }>(
    `/admin/accounts${qs.size ? `?${qs.toString()}` : ""}`,
  );
  const data = res.data;
  if (Array.isArray(data)) return data;
  if (data && Array.isArray((data as any).accounts)) {
    return (data as { accounts: Account[] }).accounts;
  }
  return [];
}

export type { Account } from "./types";

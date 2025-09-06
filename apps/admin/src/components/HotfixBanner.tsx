import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router-dom";

import { api } from "../api/client";
import type { Account } from "../api/types";
import { useAccount } from "../account/AccountContext";

export default function HotfixBanner() {
  const { accountId } = useAccount();
  const location = useLocation();
  const isEditor = location.pathname.includes("editor");
  const { data } = useQuery<Account>({
    queryKey: ["account-info", accountId],
    queryFn: async () => {
      const res = await api.get<Account>(`/admin/accounts/${accountId}`);
      return res.data;
    },
    enabled: !!accountId && isEditor,
  });

  if (data?.type === "global" && isEditor) {
    return (
      <div className="mb-4 p-2 bg-yellow-200 text-yellow-900 text-sm rounded">
        Hotfix mode
      </div>
    );
  }
  return null;
}

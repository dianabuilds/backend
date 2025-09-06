import { useQuery } from "@tanstack/react-query";
import PageLayout from "./_shared/PageLayout";
import { api } from "../api/client";

interface UsageRow {
  account_id: string;
  tokens: number;
  limit: number;
  progress: number;
}

export default function AIUsage() {
  const { data } = useQuery({
    queryKey: ["ai-usage"],
    queryFn: async () => {
      const res = await api.get<UsageRow[]>("/admin/ai/usage/accounts");
      return res.data ?? [];
    },
  });
  return (
    <PageLayout title="AI Usage">
      <div className="space-y-4">
        {data?.map((row) => (
          <div key={row.account_id} className="space-y-1">
            <div className="flex justify-between text-sm">
              <span>{row.account_id}</span>
              <span>
                {row.tokens}/{row.limit || 0}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded h-3" role="progressbar" aria-valuenow={row.progress * 100}>
              <div
                className="bg-blue-500 h-3 rounded"
                style={{ width: `${Math.min(row.progress * 100, 100)}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </PageLayout>
  );
}

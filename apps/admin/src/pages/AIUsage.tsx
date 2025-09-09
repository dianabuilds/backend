import { useQuery } from '@tanstack/react-query';

import { api } from '../api/client';
import PageLayout from './_shared/PageLayout';

interface SystemUsage {
  tokens: number;
  cost: number;
}

export default function AIUsage() {
  const { data } = useQuery({
    queryKey: ['ai-usage-system'],
    queryFn: async () => {
      const res = await api.get<SystemUsage>('/admin/ai/usage/system');
      return res.data ?? { tokens: 0, cost: 0 };
    },
  });
  return (
    <PageLayout title="AI Usage">
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span>Total tokens</span>
          <span>{data?.tokens ?? 0}</span>
        </div>
        <div className="flex justify-between">
          <span>Estimated cost</span>
          <span>
            ${'{'}(data?.cost ?? 0).toFixed(4){'}'}
          </span>
        </div>
      </div>
    </PageLayout>
  );
}

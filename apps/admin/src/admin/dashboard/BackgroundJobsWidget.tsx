import { useQuery } from '@tanstack/react-query';

import { api } from '../../api/client';
import { Card, CardContent } from '../../components/ui/card';

interface JobItem {
  id: string;
  name: string;
  status: string;
}

export default function BackgroundJobsWidget({
  query = '',
  refreshInterval = 60000,
}: {
  query?: string;
  refreshInterval?: number;
}) {
  const { data = [] } = useQuery<JobItem[]>({
    queryKey: ['widget', query],
    queryFn: async (): Promise<JobItem[]> => {
      const res = await api.get<JobItem[]>(query);
      return (res.data as JobItem[] | undefined) ?? [];
    },
    refetchInterval: refreshInterval,
  });
  return (
    <Card>
      <CardContent className="p-4 sm:p-6 space-y-2">
        <h2 className="font-semibold">Background jobs</h2>
        <ul className="text-sm space-y-1">
          {data.map((j) => (
            <li key={j.id}>
              {j.name} - {j.status}
            </li>
          ))}
        </ul>
        <button className="mt-2 rounded bg-gray-200 px-3 py-1 text-sm disabled:opacity-50" disabled>
          View all jobs
        </button>
      </CardContent>
    </Card>
  );
}

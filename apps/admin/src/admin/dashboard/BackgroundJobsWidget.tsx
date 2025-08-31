import { useQuery } from '@tanstack/react-query';

import { api } from '../../api/client';

interface JobItem {
  id: string;
  name: string;
  status: string;
}

export default function BackgroundJobsWidget({
  query,
  refreshInterval,
}: {
  query: string;
  refreshInterval: number;
}) {
  const { data = [] } = useQuery<JobItem[]>({
    queryKey: ['widget', query],
    queryFn: async () => (await api.get(query)).data,
    refetchInterval: refreshInterval,
  });
  return (
    <section>
      <h2 className="mb-2 text-xl font-bold">Background jobs</h2>
      <ul className="text-sm space-y-1">
        {data.map((j) => (
          <li key={j.id}>
            {j.name} - {j.status}
          </li>
        ))}
      </ul>
    </section>
  );
}

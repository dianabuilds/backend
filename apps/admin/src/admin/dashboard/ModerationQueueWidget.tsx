import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { api } from '../../api/client';

interface QueueItem {
  id: string;
  type: string;
  reason: string;
  status: string;
}

export default function ModerationQueueWidget({
  query,
  refreshInterval,
}: {
  query: string;
  refreshInterval: number;
}) {
  const { data = [] } = useQuery<QueueItem[]>({
    queryKey: ['widget', query],
    queryFn: async () => (await api.get(query)).data,
    refetchInterval: refreshInterval,
  });
  return (
    <section>
      <h2 className="mb-2 text-xl font-bold">Moderation queue</h2>
      <ul className="text-sm space-y-1">
        {data.map((item) => (
          <li key={item.id}>
            <Link
              to={`/moderation?status=${item.status}`}
              className="hover:underline"
            >
              [{item.type}] {item.reason} - {item.status}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}

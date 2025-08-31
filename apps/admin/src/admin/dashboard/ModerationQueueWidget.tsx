import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { Card, CardContent } from '../../components/ui/card';
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
    <Card>
      <CardContent className="p-4 space-y-2">
        <h2 className="font-semibold">Moderation queue</h2>
        {data.length === 0 ? (
          <p className="text-sm text-gray-500">No items</p>
        ) : (
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
        )}
        <Link
          to="/moderation"
          className="mt-2 inline-block rounded bg-blue-500 px-3 py-1 text-sm text-white disabled:opacity-50"
        >
          Open moderation
        </Link>
      </CardContent>
    </Card>
  );
}

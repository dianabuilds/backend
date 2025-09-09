import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { api } from '../../api/client';
import { Card, CardContent } from '../../components/ui/card';

interface DraftIssue {
  id: string;
  slug?: string;
  title?: string;
  issues: string[];
}

export default function DraftIssuesWidget({
  query,
  refreshInterval,
}: {
  query: string;
  refreshInterval: number;
}) {
  const { data = [] } = useQuery<DraftIssue[]>({
    queryKey: ['widget', query],
    queryFn: async () => (await api.get(query)).data,
    refetchInterval: refreshInterval,
  });
  return (
    <Card>
      <CardContent className="p-4 sm:p-6 space-y-2">
        <h2 className="font-semibold">Drafts with issues</h2>
        <ul className="mb-2 list-disc pl-5 text-sm">
          {data.map((d) => (
            <li key={d.id}>{d.title || d.slug}</li>
          ))}
        </ul>
        <Link
          to="/nodes?status=draft"
          className="mt-2 inline-block rounded bg-gray-200 px-3 py-1 text-sm"
        >
          See all drafts
        </Link>
      </CardContent>
    </Card>
  );
}

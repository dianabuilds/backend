import { useQuery } from '@tanstack/react-query';

import { api } from '../../api/client';

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
    <section>
      <h2 className="mb-2 text-xl font-bold">Drafts with issues</h2>
      <ul className="mb-2 list-disc pl-5 text-sm">
        {data.map((d) => (
          <li key={d.id}>{d.title || d.slug}</li>
        ))}
      </ul>
    </section>
  );
}

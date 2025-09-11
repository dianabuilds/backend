import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { useAccount } from '../account/AccountContext';
import { nodesApi } from '../features/content/api/nodes.api';
import { queryKeys } from '../shared/api/queryKeys';

interface NodeItem {
  id: number;
  status: string;
}

export default function ContentAll() {
  const { accountId } = useAccount();
  const [status, setStatus] = useState('');
  const [tag, setTag] = useState('');

  const { data } = useQuery<NodeItem[]>({
    queryKey: queryKeys.nodes(accountId || '', {
      status: status || undefined,
      tags: tag || undefined,
    }),
    queryFn: async () => {
      const rows = await nodesApi.list(accountId || '', {
        status: status || undefined,
        tags: tag || undefined,
      });
      type RawNode = Partial<NodeItem> & { id?: number; nodeId?: number; status?: string };
      const arr = Array.isArray(rows) ? (rows as unknown as RawNode[]) : [];
      return arr.map((n) => ({
        id: Number(n.nodeId ?? n.id ?? 0),
        status: String(n.status ?? ''),
      }));
    },
    enabled: true,
  });

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">All Content</h1>
      <div className="flex gap-2 mb-4">
        <input
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          placeholder="status"
          className="px-2 py-1 border rounded text-sm"
        />
        <input
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          placeholder="tag"
          className="px-2 py-1 border rounded text-sm"
        />
      </div>
      <ul className="space-y-1">
        {data?.map((item) => (
          <li key={String(item.id)} className="text-sm">
            {item.status} {item.id}
          </li>
        ))}
      </ul>
    </div>
  );
}

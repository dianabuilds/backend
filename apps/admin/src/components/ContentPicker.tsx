import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { useAccount } from '../account/AccountContext';
import { type AdminNodeItem, listNodes } from '../api/nodes';

interface ContentPickerProps {
  onSelect: (item: AdminNodeItem) => void;
  onClose?: () => void;
}

export default function ContentPicker({ onSelect, onClose }: ContentPickerProps) {
  const { accountId } = useAccount();
  const [search, setSearch] = useState('');
  const [tag, setTag] = useState('');

  const { data: items = [] } = useQuery({
    queryKey: ['content-picker', accountId, search, tag],
    queryFn: async () =>
      accountId
        ? listNodes(accountId, {
            q: search || undefined,
            tags: tag || undefined,
          })
        : [],
  });

  return (
    <div className="p-4">
      <div className="mb-2 flex gap-2">
        <input
          className="border rounded px-2 py-1 flex-1"
          placeholder="Search by name"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <input
          className="border rounded px-2 py-1 flex-1"
          placeholder="Tag"
          value={tag}
          onChange={(e) => setTag(e.target.value)}
        />
        {onClose && (
          <button className="px-2 py-1 border rounded" onClick={onClose}>
            Close
          </button>
        )}
      </div>
      <ul className="max-h-64 overflow-auto border rounded">
        {items.map((n) => (
          <li
            key={n.id}
            className="px-2 py-1 text-sm hover:bg-gray-100 cursor-pointer"
            onClick={() => onSelect(n)}
          >
            {n.title || n.slug}
          </li>
        ))}
        {items.length === 0 && <li className="p-2 text-sm text-gray-500">No results</li>}
      </ul>
    </div>
  );
}

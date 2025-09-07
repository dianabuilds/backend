import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { nodesApi } from "../features/content/api/nodes.api";
import { queryKeys } from "../shared/api/queryKeys";
import { useAccount } from "../account/AccountContext";

interface NodeItem {
  id: string;
  status: string;
}

export default function ContentAll() {
  const { accountId } = useAccount();
  const [status, setStatus] = useState("");
  const [tag, setTag] = useState("");

  const { data } = useQuery({
    queryKey: queryKeys.nodes(accountId || "", {
      status: status || undefined,
      tags: tag || undefined,
    }),
    queryFn: async () => {
      return (await nodesApi.list(accountId || '', {
        status: status || undefined,
        tags: tag || undefined,
      })) as NodeItem[];
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
          <li key={item.id} className="text-sm">
            {item.status} – {item.id}
          </li>
        ))}
      </ul>
    </div>
  );
}

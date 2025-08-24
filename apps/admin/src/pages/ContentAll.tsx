import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { listNodes } from "../api/client";

interface NodeItem {
  id: string;
  type: string;
  status: string;
}

export default function ContentAll() {
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");
  const [tag, setTag] = useState("");

  const { data } = useQuery({
    queryKey: ["nodes", "all", type, status, tag],
    queryFn: async () => {
      const items = await listNodes({
        content_type: type || undefined,
        status: status || undefined,
        tag: tag || undefined,
      });
      return items as NodeItem[];
    },
  });

  return (
    <div>
      <h1 className="text-xl font-semibold mb-4">All Content</h1>
      <div className="flex gap-2 mb-4">
        <input
          value={type}
          onChange={(e) => setType(e.target.value)}
          placeholder="type"
          className="px-2 py-1 border rounded text-sm"
        />
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
            {item.type} – {item.status} – {item.id}
          </li>
        ))}
      </ul>
    </div>
  );
}

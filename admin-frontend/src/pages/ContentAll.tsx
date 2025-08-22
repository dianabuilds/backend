import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

interface ContentItem {
  id: string;
  type: string;
  status: string;
}

export default function ContentAll() {
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");
  const [tag, setTag] = useState("");

  const { data } = useQuery({
    queryKey: ["content", "all", type, status, tag],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (type) params.set("content_type", type);
      if (status) params.set("status", status);
      if (tag) params.set("tag", tag);
      const res = await api.get<{ items: ContentItem[] }>(
        `/admin/content/all?${params.toString()}`,
      );
      return res.data?.items || [];
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

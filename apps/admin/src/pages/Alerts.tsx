import { useQuery } from "@tanstack/react-query";

import { getAlerts, type AlertItem } from "../api/alerts";

export default function Alerts() {
  const { data, isLoading, error } = useQuery<AlertItem[]>({
    queryKey: ["alerts"],
    queryFn: getAlerts,
    refetchInterval: 15000,
  });

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Alerts</h1>
      {isLoading && <div className="text-sm text-gray-500">Loading...</div>}
      {error && (
        <div className="text-sm text-red-600">Failed to load alerts</div>
      )}
      <ul className="space-y-3">
        {data?.map((a) => (
          <li key={a.id} className="border-b pb-2">
            {a.startsAt && (
              <div className="text-xs text-gray-500">
                {new Date(a.startsAt).toLocaleString()}
              </div>
            )}
            <div>{a.description}</div>
            {a.url && (
              <a
                href={a.url}
                target="_blank"
                rel="noreferrer"
                className="text-blue-600 hover:underline text-sm"
              >
                View
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

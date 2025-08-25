import { useEffect, useState } from "react";

import { api } from "../api/client";

export default function Health() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get<Record<string, unknown>>("/health");
        setData(res.data || null);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Health</h1>
      <p className="text-sm text-gray-600 mb-6">
        View application health statuses.
      </p>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {data && (
        <div className="grid gap-2 max-w-md">
          {Object.entries(data).map(([key, value]) => (
            <div
              key={key}
              className="border rounded p-2 flex justify-between text-sm"
            >
              <span>{key}</span>
              <span
                className={
                  value === "ok" ? "text-green-600" : "text-red-600"
                }
              >
                {String(value)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

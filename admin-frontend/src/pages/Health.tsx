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
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {data && <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded text-xs overflow-auto">{JSON.stringify(data, null, 2)}</pre>}
    </div>
  );
}

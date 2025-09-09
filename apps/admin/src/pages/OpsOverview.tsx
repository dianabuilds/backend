import { useEffect, useState } from 'react';

import { api } from '../api/client';

export default function OpsOverview() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get('/admin/ops/overview')
      .then((res) => setData(res.data as Record<string, unknown>))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  if (error) {
    return <p className="text-red-600">{error}</p>;
  }
  if (!data) {
    return <p>Loading...</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Ops Overview</h1>
      <pre className="bg-gray-100 p-4 rounded text-sm">{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

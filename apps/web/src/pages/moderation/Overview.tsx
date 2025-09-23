import React from 'react';
import { Card, Spinner } from '@ui';
import { apiGet } from '../../shared/api/client';

type Overview = {
  complaints_new?: Record<string, any>;
  tickets?: Record<string, any>;
  content_queues?: Record<string, number>;
  last_sanctions?: Array<{ id: string; type: string; status: string; reason?: string | null; issued_at?: string | null; }>
  charts?: Record<string, any>;
  cards?: Array<Record<string, any>>;
};

export default function ModerationOverview() {
  const [data, setData] = React.useState<Overview | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const r = await apiGet<Overview>('/api/moderation/overview');
      setData(r || {});
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => { load(); }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Moderation Overview</h1>
        <div className="flex items-center gap-2">
          {loading && <Spinner size="sm" />}
          <button className="btn h-9 bg-gray-100 px-3 hover:bg-gray-200 dark:bg-dark-600" onClick={load}>Refresh</button>
        </div>
      </div>

      {error && <Card skin="shadow" className="p-4 text-red-600">{error}</Card>}

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-6">
        {Object.entries(data?.content_queues || {}).map(([k, v]) => (
          <Card key={k} skin="shadow" className="p-3">
            <div className="text-xs text-gray-500">{k}</div>
            <div className="text-lg font-semibold">{String(v)}</div>
          </Card>
        ))}
        {Object.keys(data?.content_queues || {}).length === 0 && (
          <Card skin="shadow" className="p-3"><div className="text-xs text-gray-500">Content</div><div className="text-lg font-semibold">0</div></Card>
        )}
      </div>

      {/* Sections */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card skin="shadow" className="p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-600">New Complaints</h3>
          <pre className="text-xs text-gray-700 dark:text-dark-100 overflow-auto">{JSON.stringify(data?.complaints_new || {}, null, 2)}</pre>
        </Card>
        <Card skin="shadow" className="p-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-600">Tickets</h3>
          <pre className="text-xs text-gray-700 dark:text-dark-100 overflow-auto">{JSON.stringify(data?.tickets || {}, null, 2)}</pre>
        </Card>
      </div>
    </div>
  );
}

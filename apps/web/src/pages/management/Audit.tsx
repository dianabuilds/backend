import React from 'react';
import { Card, Spinner } from '@ui';
import { apiGet } from '../../shared/api/client';

type AuditItem = {
  id?: string | number;
  created_at?: string | null;
  ts?: number | null;
  actor_id?: string | null;
  action?: string | null;
  resource_type?: string | null;
  resource_id?: string | null;
  reason?: string | null;
};

export default function ManagementAudit() {
  const [items, setItems] = React.useState<AuditItem[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Filters
  const [actions, setActions] = React.useState<string>(''); // comma-separated
  const [actorId, setActorId] = React.useState<string>('');
  const [actorQuery, setActorQuery] = React.useState<string>('');
  const [userOpts, setUserOpts] = React.useState<{ id: string; username: string }[]>([]);
  const [showUserOpts, setShowUserOpts] = React.useState<boolean>(false);
  const [fromTs, setFromTs] = React.useState<string>('');
  const [toTs, setToTs] = React.useState<string>('');

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params: string[] = ['limit=200'];
      const act = (actions || '').split(',').map((s) => s.trim()).filter(Boolean);
      if (act.length === 1) params.push(`action=${encodeURIComponent(act[0])}`);
      if (act.length > 1) params.push(`action=${encodeURIComponent(act.join(','))}`);
      if (actorId) params.push(`actor_id=${encodeURIComponent(actorId)}`);
      if (fromTs) params.push(`from=${encodeURIComponent(fromTs)}`);
      if (toTs) params.push(`to=${encodeURIComponent(toTs)}`);
      const url = `/v1/audit?${params.join('&')}`;
      const r = await apiGet<{ items: AuditItem[] }>(url);
      setItems(r?.items || []);
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    const t = setTimeout(load, 200);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [actions, actorId, fromTs, toTs]);

  function fmtTime(row: AuditItem): string {
    const raw = row.created_at || '';
    if (raw) return String(raw).slice(0, 19).replace('T', ' ');
    if (row.ts) {
      try {
        const d = new Date(row.ts);
        return d.toISOString().slice(0, 19).replace('T', ' ');
      } catch {}
    }
    return '';
  }

  return (
    <div className="p-6 space-y-6">
      <Card skin="shadow" className="relative p-4">
        {error && (
          <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
        )}
        <div className="table-toolbar mb-2 flex items-center justify-between">
          <h2 className="dark:text-dark-100 truncate text-base font-medium tracking-wide text-gray-800">Audit log</h2>
          <div className="flex items-center gap-2">
            {/* Actions filter */}
            <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 dark:border-dark-500 dark:bg-dark-700">
              <span className="text-xs text-gray-500">Action(s)</span>
              <input
                className="h-9 w-64 bg-transparent text-sm outline-none placeholder:text-gray-400"
                placeholder="e.g. create, update"
                value={actions}
                onChange={(e) => setActions(e.target.value)}
              />
            </div>
            {/* Actor filter with search */}
            <div className="relative flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 py-1 text-sm dark:border-dark-500 dark:bg-dark-700">
              <span className="text-xs text-gray-500">Actor</span>
              <input
                className="h-9 w-64 bg-transparent text-sm outline-none placeholder:text-gray-400"
                placeholder="Search username..."
                value={actorQuery}
                onChange={async (e) => {
                  const v = e.target.value;
                  setActorQuery(v);
                  setShowUserOpts(true);
                  try {
                    const opts = await apiGet(`/v1/users/search?q=${encodeURIComponent(v)}&limit=10`);
                    if (Array.isArray(opts)) setUserOpts(opts);
                  } catch {}
                }}
                onFocus={async () => {
                  setShowUserOpts(true);
                  try {
                    const opts = await apiGet(`/v1/users/search?q=${encodeURIComponent(actorQuery)}&limit=10`);
                    if (Array.isArray(opts)) setUserOpts(opts);
                  } catch {}
                }}
              />
              {actorId && (
                <button className="rounded bg-gray-200 px-2 text-xs hover:bg-gray-300 dark:bg-dark-600" onClick={() => { setActorId(''); setActorQuery(''); }}>
                  Clear
                </button>
              )}
              {showUserOpts && userOpts.length > 0 && (
                <div className="absolute left-0 top-10 z-10 w-64 rounded border border-gray-300 bg-white shadow dark:border-dark-500 dark:bg-dark-700">
                  {userOpts.map((u) => (
                    <button
                      key={u.id}
                      className="block w-full truncate px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                      onClick={() => {
                        setActorId(u.id);
                        setActorQuery(u.username || u.id);
                        setShowUserOpts(false);
                      }}
                    >
                      {u.username || u.id}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {/* Date range */}
            <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 py-1 text-sm dark:border-dark-500 dark:bg-dark-700">
              <span className="text-xs text-gray-500">From</span>
              <input type="datetime-local" className="form-input h-9 w-56" value={fromTs} onChange={(e) => setFromTs(e.target.value)} />
            </div>
            <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 py-1 text-sm dark:border-dark-500 dark:bg-dark-700">
              <span className="text-xs text-gray-500">To</span>
              <input type="datetime-local" className="form-input h-9 w-56" value={toTs} onChange={(e) => setToTs(e.target.value)} />
            </div>
            {loading && <Spinner size="sm" />}
            <button
              className="btn-base btn h-9 bg-gray-100 px-3 text-sm hover:bg-gray-200 dark:bg-dark-600"
              onClick={load}
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="relative overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-500">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-dark-700/40">
              <tr>
                <th className="py-2 px-3">Time</th>
                <th className="py-2 px-3">Actor</th>
                <th className="py-2 px-3">Action</th>
                <th className="py-2 px-3">Resource</th>
                <th className="py-2 px-3">Reason</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td className="py-3 px-3" colSpan={5}>Loading...</td></tr>
              )}
              {!loading && items.length === 0 && (
                <tr><td className="py-8 px-3 text-center text-sm text-gray-500" colSpan={5}>No events</td></tr>
              )}
              {!loading && items.map((e, i) => (
                <tr key={i} className="border-b border-gray-200">
                  <td className="py-2 px-3 text-gray-500">{fmtTime(e)}</td>
                  <td className="py-2 px-3">{e.actor_id || '-'}</td>
                  <td className="py-2 px-3">{e.action || '-'}</td>
                  <td className="py-2 px-3">{e.resource_type || ''}{e.resource_id ? `:${e.resource_id}` : ''}</td>
                  <td className="py-2 px-3 text-gray-700">{e.reason || (e as any)?.extra?.reason || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

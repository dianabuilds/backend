import React from 'react';
import { Card, Spinner, Drawer, Select, Textarea, Button, TablePagination } from '@ui';
import { apiGet, apiPost } from '../../shared/api/client';

type Appeal = {
  id: string;
  target_type: string;
  target_id: string;
  user_id: string;
  status: string;
  created_at?: string | null;
  decided_at?: string | null;
  decided_by?: string | null;
  decision_reason?: string | null;
};

export default function ModerationAppeals() {
  const [items, setItems] = React.useState<Appeal[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState('');

  const [decideId, setDecideId] = React.useState<string | null>(null);
  const [result, setResult] = React.useState('approved');
  const [reason, setReason] = React.useState('');
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [hasNext, setHasNext] = React.useState(false);
  const [totalItems, setTotalItems] = React.useState<number | undefined>(undefined);

  const resetPagination = React.useCallback(() => {
    setPage(1);
    setHasNext(false);
    setTotalItems(undefined);
  }, []);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const offset = Math.max(0, (page - 1) * pageSize);
      const params = [`limit=${pageSize}`, `offset=${offset}`];
      if (status) params.push(`status=${encodeURIComponent(status)}`);
      const r = await apiGet<{ items?: Appeal[]; total?: number }>(`/api/moderation/appeals?${params.join('&')}`);
      const fetched = Array.isArray(r?.items) ? r.items : [];
      setItems(fetched);
      const total = typeof r?.total === 'number' ? Number(r.total) : undefined;
      setTotalItems(total);
      if (total != null) {
        setHasNext(page * pageSize < total);
      } else {
        setHasNext(fetched.length === pageSize);
      }
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
      setHasNext(false);
      setTotalItems(undefined);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, status]);

  React.useEffect(() => {
    const t = setTimeout(() => { void load(); }, 200);
    return () => clearTimeout(t);
  }, [load]);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Appeals</h1>
        <div className="flex items-center gap-2">
          {loading && <Spinner size="sm" />}
          <button className="btn h-9 bg-gray-100 px-3 hover:bg-gray-200 dark:bg-dark-600" onClick={load}>Refresh</button>
        </div>
      </div>
      <Card skin="shadow" className="p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
          <input className="form-input h-9 w-40" placeholder="Status (new/pending/...)" value={status} onChange={(e) => { setStatus(e.target.value); resetPagination(); }} />
        </div>
        {error && <div className="mb-2 text-sm text-red-600">{error}</div>}
        <div className="relative overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-500">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-dark-700/40">
              <tr>
                <th className="py-2 px-3">ID</th>
                <th className="py-2 px-3">User</th>
                <th className="py-2 px-3">Target</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3">Created</th>
                <th className="py-2 px-3">Decided</th>
                <th className="py-2 px-3">By</th>
                <th className="py-2 px-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((a) => (
                <tr key={a.id} className="border-b border-gray-200">
                  <td className="py-2 px-3 text-gray-500">{a.id}</td>
                  <td className="py-2 px-3">{a.user_id}</td>
                  <td className="py-2 px-3">{a.target_type}:{a.target_id}</td>
                  <td className="py-2 px-3">{a.status}</td>
                  <td className="py-2 px-3">{a.created_at || ''}</td>
                  <td className="py-2 px-3">{a.decided_at || ''}</td>
                  <td className="py-2 px-3">{a.decided_by || ''}</td>
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <button className="btn h-8 rounded bg-gray-100 px-2 text-xs hover:bg-gray-200 dark:bg-dark-600" onClick={() => { setDecideId(a.id); setResult('approved'); setReason(''); }}>Decide</button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td className="py-4 px-3 text-center text-gray-500" colSpan={7}>No appeals</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <TablePagination
          page={page}
          pageSize={pageSize}
          currentCount={items.length}
          hasNext={hasNext}
          totalItems={totalItems}
          onPageChange={(value) => setPage(value)}
          onPageSizeChange={(value) => { setPageSize(value); resetPagination(); }}
        />
      </Card>
      <Drawer
        open={!!decideId}
        onClose={() => setDecideId(null)}
        title={`Decide appeal: ${decideId || ''}`}
        footer={<Button onClick={async () => {
          if (!decideId) return;
          try { await apiPost(`/api/moderation/appeals/${encodeURIComponent(decideId)}/decision`, { result, reason }); setDecideId(null); await load(); }
          catch (e: any) { setError(String(e?.message || e || 'error')); }
        }}>Apply</Button>}
        widthClass="w-[520px]"
      >
        <div className="p-4 space-y-3">
          <div>
            <div className="mb-1 text-xs text-gray-500">Result</div>
            <Select value={result} onChange={(e: any) => setResult(e.target.value)}>
              <option value="approved">approved</option>
              <option value="rejected">rejected</option>
            </Select>
          </div>
          <div>
            <div className="mb-1 text-xs text-gray-500">Reason</div>
            <Textarea value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason (optional)" />
          </div>
        </div>
      </Drawer>
    </div>
  );
}

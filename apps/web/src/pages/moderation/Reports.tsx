import React from 'react';
import { Card, Spinner, Drawer, Select, Textarea, Button, TablePagination } from '@ui';
import { apiGet, apiPost } from '../../shared/api/client';

type Report = {
  id: string;
  object_type: string;
  object_id: string;
  reporter_id: string;
  category: string;
  status: string;
  created_at?: string | null;
  resolved_at?: string | null;
  decision?: string | null;
};

export default function ModerationReports() {
  const [items, setItems] = React.useState<Report[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState('');
  const [category, setCategory] = React.useState('');

  const [resolveId, setResolveId] = React.useState<string | null>(null);
  const [result, setResult] = React.useState('valid');
  const [decision, setDecision] = React.useState('');
  const [notes, setNotes] = React.useState('');
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [hasNext, setHasNext] = React.useState(false);
  const [totalItems, setTotalItems] = React.useState<number | undefined>(undefined);

  const resetPagination = React.useCallback(() => {
    setPage(1);
    setHasNext(false);
    setTotalItems(undefined);
  }, []);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const offset = Math.max(0, (page - 1) * pageSize);
      const params = [`limit=${pageSize}`, `offset=${offset}`];
      if (status) params.push(`status=${encodeURIComponent(status)}`);
      if (category) params.push(`category=${encodeURIComponent(category)}`);
      const r = await apiGet<{ items?: Report[]; total?: number }>(`/api/moderation/reports?${params.join('&')}`);
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
  }

  React.useEffect(() => {
    const t = setTimeout(() => { void load(); }, 200);
    return () => clearTimeout(t);
  }, [status, category, page, pageSize]);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Reports</h1>
        <div className="flex items-center gap-2">
          {loading && <Spinner size="sm" />}
          <button className="btn h-9 bg-gray-100 px-3 hover:bg-gray-200 dark:bg-dark-600" onClick={load}>Refresh</button>
        </div>
      </div>
      <Card skin="shadow" className="p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
          <input className="form-input h-9 w-40" placeholder="Status (new/valid/...)" value={status} onChange={(e) => { setStatus(e.target.value); resetPagination(); }} />
          <input className="form-input h-9 w-40" placeholder="Category" value={category} onChange={(e) => { setCategory(e.target.value); resetPagination(); }} />
        </div>
        {error && <div className="mb-2 text-sm text-red-600">{error}</div>}
        <div className="relative overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-500">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-dark-700/40">
              <tr>
                <th className="py-2 px-3">ID</th>
                <th className="py-2 px-3">Object</th>
                <th className="py-2 px-3">Reporter</th>
                <th className="py-2 px-3">Category</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3">Created</th>
                <th className="py-2 px-3">Decision</th>
                <th className="py-2 px-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.id} className="border-b border-gray-200">
                  <td className="py-2 px-3 text-gray-500">{r.id}</td>
                  <td className="py-2 px-3">{r.object_type}:{r.object_id}</td>
                  <td className="py-2 px-3">{r.reporter_id}</td>
                  <td className="py-2 px-3">{r.category}</td>
                  <td className="py-2 px-3">{r.status}</td>
                  <td className="py-2 px-3">{r.created_at || ''}</td>
                  <td className="py-2 px-3">{r.decision || ''}</td>
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <button className="btn h-8 rounded bg-gray-100 px-2 text-xs hover:bg-gray-200 dark:bg-dark-600" onClick={() => { setResolveId(r.id); setResult('valid'); setDecision(''); setNotes(''); }}>Resolve</button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td className="py-4 px-3 text-center text-gray-500" colSpan={7}>No reports</td></tr>
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
        open={!!resolveId}
        onClose={() => setResolveId(null)}
        title={`Resolve report: ${resolveId || ''}`}
        footer={<Button onClick={async () => {
          if (!resolveId) return;
          try { await apiPost(`/api/moderation/reports/${encodeURIComponent(resolveId)}/resolve`, { result, decision, notes }); setResolveId(null); await load(); }
          catch (e: any) { setError(String(e?.message || e || 'error')); }
        }}>Apply</Button>}
        widthClass="w-[520px]"
      >
        <div className="p-4 space-y-3">
          <div>
            <div className="mb-1 text-xs text-gray-500">Result</div>
            <Select value={result} onChange={(e: any) => setResult(e.target.value)}>
              <option value="valid">valid</option>
              <option value="invalid">invalid</option>
              <option value="resolved">resolved</option>
              <option value="escalated">escalated</option>
            </Select>
          </div>
          <div>
            <div className="mb-1 text-xs text-gray-500">Decision</div>
            <InputLike value={decision} onChange={(e: any) => setDecision(e.target.value)} placeholder="Decision (optional)" />
          </div>
          <div>
            <div className="mb-1 text-xs text-gray-500">Notes</div>
            <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Notes (optional)" />
          </div>
        </div>
      </Drawer>
    </div>
  );
}

// Simple input using textarea UI (vendor kit lacks direct Input export in some bundles)
function InputLike(props: any) {
  return <Textarea rows={1} {...props} />;
}

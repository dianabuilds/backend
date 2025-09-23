import React from 'react';
import { Card, Spinner, Drawer, Textarea, Button, TablePagination } from '@ui';
import { apiGet, apiPost, apiPatch } from '../../shared/api/client';

type Ticket = {
  id: string;
  title: string;
  priority: string;
  author_id: string;
  assignee_id?: string | null;
  status: string;
  unread_count?: number;
  updated_at?: string | null;
};

export default function ModerationTickets() {
  const [items, setItems] = React.useState<Ticket[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState('');
  const [priority, setPriority] = React.useState('');

  const [commentTicket, setCommentTicket] = React.useState<Ticket | null>(null);
  const [commentText, setCommentText] = React.useState('');
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
      if (priority) params.push(`priority=${encodeURIComponent(priority)}`);
      const r = await apiGet<{ items?: Ticket[]; total?: number }>(`/api/moderation/tickets?${params.join('&')}`);
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
  }, [status, priority, page, pageSize]);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Tickets</h1>
        <div className="flex items-center gap-2">
          {loading && <Spinner size="sm" />}
          <button className="btn h-9 bg-gray-100 px-3 hover:bg-gray-200 dark:bg-dark-600" onClick={load}>Refresh</button>
        </div>
      </div>
      <Card skin="shadow" className="p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
          <input className="form-input h-9 w-40" placeholder="Status (new/progress/...)" value={status} onChange={(e) => { setStatus(e.target.value); resetPagination(); }} />
          <input className="form-input h-9 w-40" placeholder="Priority (low/normal/...)" value={priority} onChange={(e) => { setPriority(e.target.value); resetPagination(); }} />
        </div>
        {error && <div className="mb-2 text-sm text-red-600">{error}</div>}
        <div className="relative overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-500">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-dark-700/40">
              <tr>
                <th className="py-2 px-3">ID</th>
                <th className="py-2 px-3">Title</th>
                <th className="py-2 px-3">Author</th>
                <th className="py-2 px-3">Assignee</th>
                <th className="py-2 px-3">Status</th>
                <th className="py-2 px-3">Priority</th>
                <th className="py-2 px-3">Unread</th>
                <th className="py-2 px-3">Updated</th>
                <th className="py-2 px-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((t) => (
                <tr key={t.id} className="border-b border-gray-200">
                  <td className="py-2 px-3 text-gray-500">{t.id}</td>
                  <td className="py-2 px-3">{t.title}</td>
                  <td className="py-2 px-3">{t.author_id}</td>
                  <td className="py-2 px-3">{t.assignee_id || ''}</td>
                  <td className="py-2 px-3">{t.status}</td>
                  <td className="py-2 px-3">{t.priority}</td>
                  <td className="py-2 px-3">{t.unread_count ?? 0}</td>
                  <td className="py-2 px-3">{t.updated_at || ''}</td>
                  <td className="py-2 px-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <button className="btn h-8 rounded bg-gray-100 px-2 text-xs hover:bg-gray-200 dark:bg-dark-600" onClick={() => { setCommentTicket(t); setCommentText(''); }}>Comment</button>
                      <button
                        className="btn h-8 rounded bg-gray-100 px-2 text-xs hover:bg-gray-200 dark:bg-dark-600"
                        onClick={async () => { try { await apiPatch(`/api/moderation/tickets/${encodeURIComponent(t.id)}`, { status: 'closed' }); await load(); } catch (e: any) { setError(String(e?.message || e || 'error')); } }}
                      >Close</button>
                      <button
                        className="btn h-8 rounded bg-gray-100 px-2 text-xs hover:bg-gray-200 dark:bg-dark-600"
                        onClick={async () => { try { await apiPost(`/api/moderation/tickets/${encodeURIComponent(t.id)}/escalate`, {}); await load(); } catch (e: any) { setError(String(e?.message || e || 'error')); } }}
                      >Escalate</button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td className="py-4 px-3 text-center text-gray-500" colSpan={8}>No tickets</td></tr>
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
        open={!!commentTicket}
        onClose={() => setCommentTicket(null)}
        title={`Comment ticket: ${commentTicket?.id || ''}`}
        footer={<Button onClick={async () => {
          if (!commentTicket) return;
          const text = (commentText || '').trim();
          if (!text) return;
          try { await apiPost(`/api/moderation/tickets/${encodeURIComponent(commentTicket.id)}/messages`, { text, author_id: 'admin' }); setCommentTicket(null); await load(); }
          catch (e: any) { setError(String(e?.message || e || 'error')); }
        }}>Send</Button>}
        widthClass="w-[520px]"
      >
        <div className="p-4 space-y-3">
          <div className="mb-1 text-xs text-gray-500">Message</div>
          <Textarea value={commentText} onChange={(e) => setCommentText(e.target.value)} placeholder="Your message" />
        </div>
      </Drawer>
    </div>
  );
}


import React from 'react';
import { Card, Spinner, TablePagination } from '@ui';
import { apiGet, apiPost, apiPatch, apiDelete } from '../../shared/api/client';

type Rule = {
  id: string;
  category: string;
  enabled: boolean;
  updated_by?: string | null;
  updated_at?: string | null;
  description?: string | null;
};

export default function ModerationAIRules() {
  const [items, setItems] = React.useState<Rule[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [newCategory, setNewCategory] = React.useState('');
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
      const r = await apiGet<{ items?: Rule[]; total?: number }>(`/api/moderation/ai-rules?limit=${pageSize}&offset=${offset}`);
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

  async function create() {
    if (!newCategory.trim()) return;
    try {
      await apiPost('/api/moderation/ai-rules', { category: newCategory.trim(), enabled: true });
      setNewCategory('');
      if (page !== 1) {
        resetPagination();
      } else {
        await load();
      }
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
    }
  }

  async function toggle(rule: Rule) {
    try {
      await apiPatch(`/api/moderation/ai-rules/${encodeURIComponent(rule.id)}`, { enabled: !rule.enabled });
      await load();
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
    }
  }

  async function remove(rule: Rule) {
    try {
      await apiDelete(`/api/moderation/ai-rules/${encodeURIComponent(rule.id)}`);
      await load();
    } catch (e: any) {
      setError(String(e?.message || e || 'error'));
    }
  }

  React.useEffect(() => {
    void load();
  }, [page, pageSize]);

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">AI Rules</h1>
        <div className="flex items-center gap-2">
          {loading && <Spinner size="sm" />}
          <button className="btn h-9 bg-gray-100 px-3 hover:bg-gray-200 dark:bg-dark-600" onClick={load}>Refresh</button>
        </div>
      </div>
      {error && <Card skin="shadow" className="p-3 text-red-600">{error}</Card>}
      <Card skin="shadow" className="p-4">
        <div className="mb-4 flex items-center gap-2">
          <input className="form-input h-9 w-64" placeholder="New rule category (e.g. toxicity)" value={newCategory} onChange={(e) => setNewCategory(e.target.value)} />
          <button className="btn h-9 bg-primary-600 px-3 text-white hover:bg-primary-700" onClick={create}>Create</button>
        </div>
        <div className="relative overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-500">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-dark-700/40">
              <tr>
                <th className="py-2 px-3">ID</th>
                <th className="py-2 px-3">Category</th>
                <th className="py-2 px-3">Enabled</th>
                <th className="py-2 px-3">Updated</th>
                <th className="py-2 px-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((r) => (
                <tr key={r.id} className="border-b border-gray-200">
                  <td className="py-2 px-3 text-gray-500">{r.id}</td>
                  <td className="py-2 px-3">{r.category}</td>
                  <td className="py-2 px-3">{r.enabled ? 'Yes' : 'No'}</td>
                  <td className="py-2 px-3">{r.updated_at || ''}</td>
                  <td className="py-2 px-3">
                    <div className="flex items-center gap-2">
                      <button className="btn h-8 rounded bg-gray-100 px-2 text-sm hover:bg-gray-200 dark:bg-dark-600" onClick={() => toggle(r)}>
                        {r.enabled ? 'Disable' : 'Enable'}
                      </button>
                      <button className="btn h-8 rounded bg-red-100 px-2 text-sm text-red-700 hover:bg-red-200 dark:bg-dark-700" onClick={() => remove(r)}>
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td className="py-4 px-3 text-center text-gray-500" colSpan={5}>No rules</td></tr>
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
    </div>
  );
}


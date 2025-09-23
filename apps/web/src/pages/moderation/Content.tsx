import { ContentLayout } from '../content/ContentLayout';
import React from 'react';
import { Card, Spinner, Drawer, Select, Textarea, Button, Badge, TablePagination } from '@ui';
import { apiGet, apiPost } from '../../shared/api/client';

const moderationFilters = [
  { key: 'pending', label: 'Pending' },
  { key: 'resolved', label: 'Resolved' },
  { key: 'hidden', label: 'Hidden' },
  { key: 'restricted', label: 'Restricted' },
  { key: 'escalated', label: 'Escalated' },
];

const decisionOptions = [
  { value: 'keep', label: 'Keep visible' },
  { value: 'hide', label: 'Hide from feed' },
  { value: 'delete', label: 'Delete permanently' },
  { value: 'restrict', label: 'Restrict visibility' },
  { value: 'escalate', label: 'Escalate for review' },
  { value: 'review', label: 'Mark for manual review' },
];

type HistoryEntry = {
  action?: string;
  status?: string;
  reason?: string | null;
  actor?: string | null;
  decided_at?: string | null;
};

type ModerationItem = {
  id: string;
  type: string;
  author_id: string;
  created_at?: string | null;
  status?: string;
  preview?: string | null;
  meta?: Record<string, any>;
  moderation_history?: HistoryEntry[];
};

function formatTimestamp(value?: string | null): string {
  if (!value) return '-';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString();
}

function relativeTime(value?: string | null): string {
  if (!value) return '-';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return value;
  const diffMs = Date.now() - dt.getTime();
  const diffMin = Math.round(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  return `${diffDay}d ago`;
}

function StatusBadge({ value }: { value?: string }) {
  if (!value) return <span className="text-xs text-gray-500">-</span>;
  const normalized = value.toLowerCase();
  const theme =
    normalized === 'resolved'
      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
      : normalized === 'pending'
      ? 'bg-amber-50 text-amber-700 border border-amber-200'
      : normalized === 'hidden'
      ? 'bg-rose-50 text-rose-700 border border-rose-200'
      : normalized === 'restricted'
      ? 'bg-sky-50 text-sky-700 border border-sky-200'
      : 'bg-slate-100 text-slate-700 border border-slate-200';
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${theme}`}
    >
      {normalized}
    </span>
  );
}

export default function ModerationContent() {
  const [items, setItems] = React.useState<ModerationItem[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [reviewStatus, setReviewStatus] = React.useState<string>('pending');
  const [nodeStatus, setNodeStatus] = React.useState<string>('');
  const [label, setLabel] = React.useState<string>('');
  const [stats, setStats] = React.useState<Record<string, number>>({});
  const [selected, setSelected] = React.useState<ModerationItem | null>(null);
  const [decision, setDecision] = React.useState<string>('keep');
  const [decisionReason, setDecisionReason] = React.useState<string>('');
  const [applying, setApplying] = React.useState(false);
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
      const params: string[] = [`limit=${pageSize}`, `offset=${offset}`];
      if (reviewStatus) params.push(`moderation_status=${encodeURIComponent(reviewStatus)}`);
      if (nodeStatus) params.push(`status=${encodeURIComponent(nodeStatus)}`);
      if (label) params.push(`ai_label=${encodeURIComponent(label)}`);
      const response = await apiGet<{ items?: ModerationItem[]; next_cursor?: string; total?: number }>(
        `/api/moderation/content?${params.join('&')}`
      );
      const fetched = Array.isArray(response?.items) ? response.items : [];
      setItems(fetched);
      const total = typeof (response as any)?.total === 'number' ? Number((response as any).total) : undefined;
      setTotalItems(total);
      if (total != null) {
        setHasNext(page * pageSize < total);
      } else {
        setHasNext(fetched.length === pageSize);
      }
    } catch (err: any) {
      setError(String(err?.message || err || 'Failed to load moderation queue'));
      setItems([]);
      setHasNext(false);
      setTotalItems(undefined);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, reviewStatus, nodeStatus, label]);

  const loadStats = React.useCallback(async () => {
    try {
      const overview = await apiGet<any>('/api/moderation/overview');
      setStats((overview?.content_queues ?? {}) as Record<string, number>);
    } catch (err) {
      console.warn('Failed to fetch moderation overview', err);
    }
  }, []);

  React.useEffect(() => {
    void load();
  }, [load]);

  React.useEffect(() => {
    void loadStats();
  }, [loadStats]);

  const headerStats = React.useMemo(
    () =>
      Object.entries(stats)
        .slice(0, 3)
        .map(([key, value]) => ({ label: key.replaceAll('_', ' '), value: Number(value).toLocaleString() })),
    [stats],
  );

  const openDrawer = (item: ModerationItem) => {
    setSelected(item);
    setDecision('keep');
    setDecisionReason('');
  };

  const applyDecision = async () => {
    if (!selected) return;
    setApplying(true);
    try {
      await apiPost(`/api/moderation/content/${selected.id}/decision`, {
        action: decision,
        reason: decisionReason || undefined,
      });
      setSelected(null);
      await load();
      await loadStats();
    } catch (err: any) {
      setError(String(err?.message || err || 'Failed to apply decision'));
    } finally {
      setApplying(false);
    }
  };

  return (
    <ContentLayout
      title="Moderation - Content"
      description="Audit escalations, apply decisions, and keep the narrative graph healthy."
      stats={headerStats}
      actions={
        <div className="flex gap-2">
          <Button variant="outlined" onClick={loadStats}>
            Refresh metrics
          </Button>
          <Button onClick={load}>
            Refresh queue
          </Button>
        </div>
      }
      tabs={undefined}
    >
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-3">
          {moderationFilters.map((filter) => {
            const active = reviewStatus === filter.key;
            return (
              <button
                key={filter.key}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
                  active
                    ? 'bg-primary-600 text-white shadow-sm'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-dark-700 dark:text-dark-100 dark:hover:bg-dark-650'
                }`}
                onClick={() => { setReviewStatus(filter.key); resetPagination(); }}
              >
                {filter.label}
                <span className="ml-2 rounded-full bg-white/80 px-2 py-0.5 text-xs font-semibold text-gray-700 dark:bg-dark-800/80 dark:text-dark-50">
                  {stats[filter.key] ?? 0}
                </span>
              </button>
            );
          })}
          <button
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition ${
              reviewStatus === ''
                ? 'bg-primary-600 text-white shadow-sm'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-dark-700 dark:text-dark-100 dark:hover:bg-dark-650'
            }`}
            onClick={() => { setReviewStatus(''); resetPagination(); }}
          >
            All
          </button>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <input
            className="form-input h-9"
            placeholder="Filter by node status (draft/published)"
            value={nodeStatus}
            onChange={(e) => { setNodeStatus(e.target.value); resetPagination(); }}
          />
          <input
            className="form-input h-9"
            placeholder="Filter by AI label"
            value={label}
            onChange={(e) => { setLabel(e.target.value); resetPagination(); }}
          />
        </div>

        {error && (
          <div className="mt-3 rounded border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>
        )}

        <div className="mt-4 overflow-x-auto rounded-xl border border-gray-200 dark:border-dark-600">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-dark-800 dark:text-dark-200">
              <tr>
                <th className="px-4 py-3">ID</th>
                <th className="px-4 py-3">Author</th>
                <th className="px-4 py-3">Review status</th>
                <th className="px-4 py-3">Node status</th>
                <th className="px-4 py-3">Last decision</th>
                <th className="px-4 py-3">Updated</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-dark-700">
              {items.map((item) => {
                const lastDecision =
                  (item.meta?.last_decision as HistoryEntry | undefined) || item.moderation_history?.[0];
                return (
                  <tr
                    key={item.id}
                    className="bg-white/70 text-sm transition hover:bg-white dark:bg-dark-800/80 dark:hover:bg-dark-750"
                  >
                    <td className="px-4 py-3 font-mono text-xs text-gray-500 dark:text-dark-200">{item.id}</td>
                    <td className="px-4 py-3 text-gray-700 dark:text-dark-100">{item.author_id || '-'}</td>
                    <td className="px-4 py-3">
                      <StatusBadge value={item.status} />
                    </td>
                    <td className="px-4 py-3">
                      {item.meta?.node_status ? (
                        <Badge color="neutral" className="capitalize">
                          {String(item.meta.node_status)}
                        </Badge>
                      ) : (
                        <span className="text-xs text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-dark-200">
                      {lastDecision ? (
                        <div className="flex flex-col gap-1">
                          <span className="font-medium capitalize">{lastDecision.action ?? lastDecision.status}</span>
                          <span className="text-xs text-gray-400">
                            {`${lastDecision.actor || 'system'} - ${relativeTime(lastDecision.decided_at)}`}
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">No decisions</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 dark:text-dark-200">
                      {relativeTime(item.meta?.moderation_status_updated_at || item.created_at)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button size="sm" variant="outlined" onClick={() => openDrawer(item)}>
                        Decide
                      </Button>
                    </td>
                  </tr>
                );
              })}
              {!loading && items.length === 0 && (
                <tr>
                  <td className="px-4 py-6 text-center text-sm text-gray-500" colSpan={7}>
                    No content in this queue
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          {loading && (
            <div className="flex items-center justify-center py-6 text-sm text-gray-500">
              <Spinner size="sm" />
              <span className="ml-2">Loading content...</span>
            </div>
          )}
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
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `Decision for ${selected.id}` : 'Decision'}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outlined" onClick={() => setSelected(null)}>
              Cancel
            </Button>
            <Button onClick={applyDecision} disabled={applying}>
              {applying ? 'Applying...' : 'Apply decision'}
            </Button>
          </div>
        }
        widthClass="w-full max-w-xl"
      >
        {selected && (
          <div className="space-y-5">
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-700 dark:border-dark-600 dark:bg-dark-800/70 dark:text-dark-100">
              <div className="font-semibold text-gray-900 dark:text-white">Preview</div>
              <div className="mt-1 whitespace-pre-wrap text-sm">{selected.preview || '-'}</div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Action</label>
              <Select value={decision} onChange={(e: any) => setDecision(e.target.value)}>
                {decisionOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Reason</label>
              <Textarea value={decisionReason} onChange={(e) => setDecisionReason(e.target.value)} placeholder="Provide optional context" />
            </div>

            <div>
              <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">History</div>
              <div className="space-y-2">
                {(selected.moderation_history ?? []).map((entry, index) => (
                  <div
                    key={`${entry.decided_at ?? index}-${index}`}
                    className="rounded-lg border border-gray-200 p-3 text-xs text-gray-600 dark:border-dark-600 dark:text-dark-200"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold capitalize text-gray-800 dark:text-white">{entry.action || entry.status || 'decision'}</span>
                      <span>{formatTimestamp(entry.decided_at)}</span>
                    </div>
                    <div className="mt-1 text-gray-500 dark:text-dark-300">by {entry.actor || 'system'}</div>
                    {entry.reason ? <div className="mt-1 text-gray-500 dark:text-dark-300">{entry.reason}</div> : null}
                  </div>
                ))}
                {(selected.moderation_history ?? []).length === 0 && (
                  <div className="rounded-lg border border-dashed border-gray-200 p-3 text-xs text-gray-400 dark:border-dark-600 dark:text-dark-300">
                    No previous decisions recorded
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </ContentLayout>
  );
}

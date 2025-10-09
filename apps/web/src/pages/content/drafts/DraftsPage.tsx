import React from 'react';

import { ContentLayout } from '../ContentLayout';
import { Badge, Button, Card } from '@ui';
import { Table as DraftsTable } from '@ui/table';
import { fetchNodesList } from '@shared/api/nodes';
import type { NodeItem } from '@shared/types/nodes';
import { extractErrorMessage } from '@shared/utils/errors';
import { formatRelativeTime } from '@shared/utils/format';

type DraftRow = {
  id: string;
  title: string;
  slug?: string | null;
  author?: string | null;
  status?: string | null;
  updatedAt?: string | null;
};

const FALLBACK_DRAFTS: DraftRow[] = [
  { id: 'demo-1', title: 'Atmospheric ruins', slug: 'ruins-demo', author: 'System', status: 'draft', updatedAt: new Date(Date.now() - 18 * 36e5).toISOString() },
  { id: 'demo-2', title: 'Underground passage', slug: 'passage-demo', author: 'System', status: 'draft', updatedAt: new Date(Date.now() - 42 * 36e5).toISOString() },
];

function mapNodeToDraftRow(node: NodeItem): DraftRow {
  return {
    id: node.id,
    title: node.title ?? 'Untitled node',
    slug: node.slug ?? null,
    author: node.author_name ?? null,
    status: node.status ?? null,
    updatedAt: node.updated_at ?? null,
  };
}

function formatStatus(status?: string | null): { label: string; color: 'warning' | 'neutral' | 'success' } {
  const normalized = (status ?? '').toLowerCase();
  if (normalized === 'published') return { label: 'Published', color: 'success' };
  if (normalized === 'archived') return { label: 'Archived', color: 'neutral' };
  return { label: 'Draft', color: 'warning' };
}

export default function DraftsPage(): React.ReactElement {
  const [rows, setRows] = React.useState<DraftRow[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const controllerRef = React.useRef<AbortController | null>(null);

  const loadDrafts = React.useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setLoading(true);
    try {
      const { items } = await fetchNodesList({ status: 'draft', limit: 50, signal: controller.signal });
      const mapped = items.map(mapNodeToDraftRow);
      setRows(mapped.length ? mapped : FALLBACK_DRAFTS);
      setError(null);
    } catch (err) {
      if (controller.signal.aborted) return;
      setError(extractErrorMessage(err, 'Failed to load drafts'));
      setRows((previous) => (previous.length ? previous : FALLBACK_DRAFTS));
    } finally {
      if (controllerRef.current === controller) {
        controllerRef.current = null;
      }
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void loadDrafts();
    return () => {
      controllerRef.current?.abort();
    };
  }, [loadDrafts]);

  const handleRefresh = React.useCallback(() => {
    void loadDrafts();
  }, [loadDrafts]);

  return (
    <ContentLayout
      context="ops"
      title="Draft nodes"
      description="Monitor nodes that are still in progress before publication."
    >
      <Card className="space-y-4 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900 dark:text-dark-50">Recent drafts</h2>
            <p className="text-sm text-gray-500 dark:text-dark-200">Auto-sync via /v1/admin/nodes/list?status=draft</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500 dark:text-dark-300">{rows.length} entries</span>
            <Button size="sm" variant="outlined" onClick={handleRefresh} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </Button>
          </div>
        </div>

        {error && (
          <div className="rounded-xl border border-yellow-200 bg-yellow-50 px-4 py-3 text-sm text-yellow-800 dark:border-yellow-700/70 dark:bg-yellow-900/30 dark:text-yellow-100">
            {error}
          </div>
        )}

        <DraftsTable preset="surface" zebra hover headerSticky actions={null}>
          <DraftsTable.Actions />
          <DraftsTable.THead>
            <DraftsTable.TR>
              <DraftsTable.TH className="w-28">Node</DraftsTable.TH>
              <DraftsTable.TH>Title</DraftsTable.TH>
              <DraftsTable.TH className="w-40">Author</DraftsTable.TH>
              <DraftsTable.TH className="w-32">Status</DraftsTable.TH>
              <DraftsTable.TH className="w-40">Updated</DraftsTable.TH>
            </DraftsTable.TR>
          </DraftsTable.THead>
          <DraftsTable.TBody>
            {loading ? (
              <DraftsTable.Loading rows={3} colSpan={5} />
            ) : rows.length === 0 ? (
              <DraftsTable.Empty colSpan={5} title="No drafts" description="Draft nodes will appear after the next sync run." />
            ) : (
              rows.map((row) => {
                const status = formatStatus(row.status);
                return (
                  <DraftsTable.TR key={row.id}>
                    <DraftsTable.TD className="font-mono text-xs text-gray-500 dark:text-dark-300">{row.id}</DraftsTable.TD>
                    <DraftsTable.TD className="font-medium text-gray-900 dark:text-dark-100">{row.title}</DraftsTable.TD>
                    <DraftsTable.TD>{row.author ?? 'N/A'}</DraftsTable.TD>
                    <DraftsTable.TD>
                      <Badge color={status.color}>{status.label}</Badge>
                    </DraftsTable.TD>
                    <DraftsTable.TD>{formatRelativeTime(row.updatedAt, { fallback: 'N/A' })}</DraftsTable.TD>
                  </DraftsTable.TR>
                );
              })
            )}
          </DraftsTable.TBody>
        </DraftsTable>
      </Card>
    </ContentLayout>
  );
}

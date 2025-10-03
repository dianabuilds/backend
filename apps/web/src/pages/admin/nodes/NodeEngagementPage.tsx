import React from 'react';
import { useParams } from 'react-router-dom';
import { Card, PageHeader, Spinner } from '@ui';
import { fetchAdminNodeEngagement } from './api';
import { AnalyticsPanel } from './components/AnalyticsPanel';
import { BansPanel } from './components/BansPanel';
import { CommentsPanel } from './components/CommentsPanel';
import { ModeratorPanel } from './components/ModeratorPanel';
import { SummaryOverview } from './components/SummaryOverview';
import type { AdminNodeEngagementSummary } from './types';
function formatNumber(value: number | null | undefined): string {
  if (typeof value !== 'number') return 'N/A';
  return value.toLocaleString();
}
function extractLikeCount(summary: AdminNodeEngagementSummary | null): number {
  if (!summary?.reactions || typeof summary.reactions !== 'object') return 0;
  const reactions = summary.reactions as Record<string, number>;
  const like = reactions.like ?? reactions['like'];
  return typeof like === 'number' ? like : 0;
}
export default function NodeEngagementPage(): JSX.Element {
  const params = useParams();
  const nodeId = params.nodeId ?? params.id ?? null;
  const [summary, setSummary] = React.useState<AdminNodeEngagementSummary | null>(null);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [refreshing, setRefreshing] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);
  const loadSummary = React.useCallback(
    async ({ silent = false }: { silent?: boolean } = {}) => {
      if (!nodeId) {
        setSummary(null);
        setError('Node id is missing in the route.');
        setLoading(false);
        setRefreshing(false);
        return;
      }
      if (silent) setRefreshing(true);
      else setLoading(true);
      setError(null);
      try {
        const data = await fetchAdminNodeEngagement(nodeId);
        setSummary(data);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load node data';
        setError(message);
        setSummary(null);
      } finally {
        if (silent) setRefreshing(false);
        else setLoading(false);
      }
    },
    [nodeId],
  );
  React.useEffect(() => {
    loadSummary();
  }, [loadSummary]);
  const handleRefreshSummary = React.useCallback(() => loadSummary({ silent: true }), [loadSummary]);
  const stats = React.useMemo(() => {
    if (!summary) return undefined;
    const likes = extractLikeCount(summary);
    const commentsTotal = summary.comments?.total ?? summary.comments?.by_status?.published ?? 0;
    return [
      { label: 'Views', value: formatNumber(summary.views_count ?? 0) },
      { label: 'Likes', value: formatNumber(likes) },
      { label: 'Comments', value: formatNumber(commentsTotal) },
    ];
  }, [summary]);
  const headerTitle = summary?.title || (summary ? `Node #${summary.id}` : 'Node engagement');
  const headerDescription = summary
    ? 'Review engagement signals, comment health, and moderation actions in one place.'
    : 'Loading node engagement summary...';
  return (
    <div className="space-y-8">
      <PageHeader
        title={headerTitle}
        description={headerDescription}
        breadcrumbs={[
          { label: 'Nodes', to: '/nodes/library' },
          { label: headerTitle },
        ]}
        stats={stats}
      />
      {loading ? (
        <div className="flex flex-col items-center gap-3 py-24 text-sm text-neutral-500 dark:text-neutral-300">
          <Spinner />
          <span>Loading node engagement...</span>
        </div>
      ) : error ? (
        <Card className="border border-rose-200 bg-rose-50 p-6 text-sm text-rose-600 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100">
          {error}
        </Card>
      ) : summary ? (
        <div className="grid gap-6 lg:grid-cols-12">
          <div className="space-y-6 lg:col-span-8">
            <SummaryOverview summary={summary} onRefresh={handleRefreshSummary} refreshing={refreshing} />
            <CommentsPanel nodeId={nodeId!} commentSummary={summary.comments} onChange={handleRefreshSummary} />
            <BansPanel nodeId={nodeId!} commentSummary={summary.comments} onChange={handleRefreshSummary} />
            <AnalyticsPanel nodeId={nodeId!} />
          </div>
          <div className="space-y-6 lg:col-span-4">
            <ModeratorPanel nodeId={nodeId!} summary={summary} refreshing={refreshing} onRefresh={handleRefreshSummary} />
          </div>
        </div>
      ) : (
        <Card className="p-6 text-sm text-neutral-600 dark:text-neutral-300">
          Node information is unavailable. Try refreshing the page later.
        </Card>
      )}
    </div>
  );
}

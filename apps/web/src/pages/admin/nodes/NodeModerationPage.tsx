import React from 'react';

import { useNavigate, useParams } from 'react-router-dom';

import { Button, Card, PageHero, Skeleton } from '@ui';

import { fetchAdminNodeEngagement } from './api';

import { BansPanel } from './components/BansPanel';

import { CommentsPanel } from './components/CommentsPanel';

import { ModeratorPanel } from './components/ModeratorPanel';

import { SummaryOverview } from './components/SummaryOverview';

import type { AdminNodeEngagementSummary } from './types';
import type { PageHeroMetric } from '@ui/patterns/PageHero';

function formatNumber(value: number | null | undefined): string {
  if (typeof value !== 'number') return 'N/A';
  return value.toLocaleString();
}

function NodeModerationSkeleton(): JSX.Element {
  return (
    <div className="grid gap-6 lg:grid-cols-12 lg:items-start">
      <div className="space-y-6 lg:col-span-8">
        <Card className="space-y-6 p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="space-y-2">
              <Skeleton className="h-6 w-48" rounded />
              <Skeleton className="h-4 w-72" rounded />
            </div>
            <Skeleton className="h-9 w-32" rounded />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Skeleton className="h-24" rounded />
            <Skeleton className="h-24" rounded />
            <Skeleton className="h-24" rounded />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Skeleton className="h-4 w-40" rounded />
            <Skeleton className="h-4 w-48" rounded />
            <Skeleton className="h-4 w-44" rounded />
            <Skeleton className="h-4 w-36" rounded />
          </div>
        </Card>

        <Card className="space-y-5 p-6">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <Skeleton className="h-5 w-40" rounded />
            <Skeleton className="h-8 w-28" rounded />
          </div>
          <Skeleton className="h-32" rounded />
        </Card>

        <Card className="space-y-5 p-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <Skeleton className="h-5 w-36" rounded />
            <Skeleton className="h-8 w-24" rounded />
          </div>
          <Skeleton className="h-32" rounded />
        </Card>
      </div>

      <div className="space-y-6 lg:col-span-4">
        <Card className="space-y-4 p-6">
          <Skeleton className="h-5 w-48" rounded />
          <Skeleton className="h-10" rounded />
          <div className="space-y-3">
            <Skeleton className="h-5 w-full" rounded />
            <Skeleton className="h-5 w-full" rounded />
            <Skeleton className="h-5 w-3/4" rounded />
          </div>
        </Card>
      </div>
    </div>
  );
}

export default function NodeModerationPage(): JSX.Element {
  const params = useParams();
  const navigate = useNavigate();
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

  const commentSummary = summary?.comments ?? null;
  const heroMetrics = React.useMemo<PageHeroMetric[]>(() => {
    const pending = commentSummary?.by_status?.pending ?? null;
    const hidden = commentSummary?.by_status?.hidden ?? null;
    const bans = commentSummary?.bans_count ?? null;
    return [
      { id: 'pending', label: 'Pending', value: formatNumber(pending) },
      { id: 'hidden', label: 'Hidden', value: formatNumber(hidden) },
      { id: 'bans', label: 'Bans', value: formatNumber(bans) },
    ];
  }, [commentSummary]);

  const headerTitle = summary?.title || (summary ? `Node #${summary.id}` : 'Node moderation');
  const moderationStateHint = React.useMemo(() => {
    if (!commentSummary) return 'Comments are open.';
    if (commentSummary.disabled) return 'Comments are disabled for visitors.';
    if (commentSummary.locked) return 'Comments are locked for review.';
    return 'Comments are open for posting.';
  }, [commentSummary]);

  const headerDescription = summary
    ? `Moderate comments, manage bans, and control discussion health for this node. ${moderationStateHint}`
    : 'Loading node moderation data…';

  const showSkeleton = loading && !summary;

  const handleOpenAnalytics = React.useCallback(() => {
    if (!nodeId) return;
    navigate(`/admin/nodes/${encodeURIComponent(nodeId)}`);
  }, [navigate, nodeId]);

  const heroActions = React.useMemo(() => {
    if (!nodeId) return null;
    return (
      <Button onClick={handleOpenAnalytics} variant="outlined" data-testid="moderation-open-analytics">
        Open analytics overview
      </Button>
    );
  }, [handleOpenAnalytics, nodeId]);

  return (
    <div className="space-y-8">
      <PageHero
        title={headerTitle}
        description={headerDescription}
        eyebrow="Node moderation"
        breadcrumbs={[
          { label: 'Nodes', to: '/nodes/library' },
          nodeId ? { label: 'Engagement', to: `/admin/nodes/${encodeURIComponent(nodeId)}` } : undefined,
          { label: 'Moderation' },
        ].filter(Boolean) as Array<{ label: string; to?: string }>}
        metrics={heroMetrics}
        actions={heroActions}
        variant="compact"
        tone="light"
      />

      {error ? (
        <Card className="border border-rose-200 bg-rose-50 p-6 text-sm text-rose-600 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100">
          {error}
        </Card>
      ) : showSkeleton ? (
        <NodeModerationSkeleton />
      ) : summary ? (
        <div className="grid gap-6 lg:grid-cols-12 lg:items-start">
          <div className="space-y-6 lg:col-span-8">
            <CommentsPanel nodeId={nodeId!} commentSummary={summary.comments} onChange={handleRefreshSummary} />
            <BansPanel nodeId={nodeId!} commentSummary={summary.comments} onChange={handleRefreshSummary} />
          </div>

          <div className="space-y-6 lg:col-span-4 lg:sticky lg:top-24">
            <SummaryOverview
              summary={summary}
              onRefresh={handleRefreshSummary}
              refreshing={refreshing}
              nodeId={nodeId}
              currentView="moderation"
              showMetrics={false}
              className="bg-gradient-to-br from-rose-50/70 via-white to-white dark:from-dark-700/40 dark:via-dark-800 dark:to-dark-900"
            />
            <ModeratorPanel
              nodeId={nodeId!}
              summary={summary}
              refreshing={refreshing}
              onRefresh={handleRefreshSummary}
            />

            <Card className="rounded-3xl border border-violet-100/70 bg-gradient-to-br from-violet-50/70 via-white to-white p-6 dark:border-dark-600 dark:from-dark-700/40 dark:via-dark-800 dark:to-dark-900">
              <div className="space-y-5 text-sm text-neutral-600 dark:text-neutral-300">
                <div className="space-y-1">
                  <h3 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">Need engagement context?</h3>
                  <p className="text-sm text-neutral-600 dark:text-neutral-300">Jump to the analytics dashboard to inspect traffic and reaction trends.</p>
                </div>
                <Button
                  onClick={handleOpenAnalytics}
                  variant="ghost"
                  color="neutral"
                  className="px-5"
                >
                  Open analytics overview
                </Button>
              </div>
            </Card>
          </div>
        </div>
      ) : (
        <Card className="p-6 text-sm text-neutral-600 dark:text-neutral-300">
          Moderation data is unavailable. Try refreshing the page later.
        </Card>
      )}
    </div>
  );
}

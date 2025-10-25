import React from 'react';

import { useNavigate, useParams } from 'react-router-dom';

import { Button, Card, PageHero, Skeleton } from '@ui';
import { Link } from 'react-router-dom';

import { fetchAdminNodeEngagement } from './api';

import { AnalyticsPanel } from './components/AnalyticsPanel';

import { SummaryOverview } from './components/SummaryOverview';

import type { AdminNodeEngagementSummary } from './types';
import type { PageHeroMetric } from '@ui/patterns/PageHero';

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

function NodeEngagementSkeleton(): JSX.Element {
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

        <Card className="space-y-6 p-6">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <Skeleton className="h-5 w-48" rounded />
            <Skeleton className="h-9 w-28" rounded />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <Skeleton className="h-20" rounded />
            <Skeleton className="h-20" rounded />
            <Skeleton className="h-20" rounded />
          </div>
          <Skeleton className="h-72" rounded />
        </Card>
      </div>

      <div className="space-y-6 lg:col-span-4">
        <Card className="space-y-4 p-6">
          <Skeleton className="h-5 w-48" rounded />
          <Skeleton className="h-4 w-56" rounded />
          <Skeleton className="h-10 w-36" rounded />
        </Card>
      </div>
    </div>
  );
}

export default function NodeEngagementPage(): JSX.Element {
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

  const heroMetrics = React.useMemo<PageHeroMetric[]>(() => {
    if (!summary) {
      return [
        { id: 'views', label: 'Views', value: '—' },
        { id: 'likes', label: 'Likes', value: '—' },
        { id: 'comments', label: 'Comments', value: '—' },
      ];
    }
    return [
      { id: 'views', label: 'Views', value: formatNumber(summary.views_count ?? 0) },
      { id: 'likes', label: 'Likes', value: formatNumber(extractLikeCount(summary)) },
      { id: 'comments', label: 'Comments', value: formatNumber(summary.comments?.total ?? 0) },
    ];
  }, [summary]);

  const headerTitle = summary?.title || (summary ? `Node #${summary.id}` : 'Node engagement');
  const headerDescription = summary
    ? 'Review engagement signals, growth trends, and key KPI for this node.'
    : 'Loading node engagement summary…';

  const showSkeleton = loading && !summary;

  const quickLinks = React.useMemo(() => {
    const links = summary?.links ?? {};
    if (!nodeId) {
      return {
        comments: links.comments ?? undefined,
        moderation: links.moderation ?? undefined,
        bans: links.bans ?? undefined,
      };
    }
    const encoded = encodeURIComponent(nodeId);
    const defaults = {
      comments: `/admin/nodes/${encoded}/moderation#comments`,
      moderation: `/admin/nodes/${encoded}/moderation`,
      bans: `/admin/nodes/${encoded}/moderation#bans`,
    };
    return {
      comments: links.comments ?? defaults.comments,
      moderation: links.moderation ?? defaults.moderation,
      bans: links.bans ?? defaults.bans,
    };
  }, [nodeId, summary?.links]);

  const quickLinkItems = React.useMemo(() => [
    quickLinks.comments ? { key: 'comments', label: 'Open comments workspace', href: quickLinks.comments } : null,
    quickLinks.bans ? { key: 'bans', label: 'Manage comment bans', href: quickLinks.bans } : null,
  ].filter(Boolean) as Array<{ key: string; label: string; href: string }>, [quickLinks.bans, quickLinks.comments]);

  const handleOpenModeration = React.useCallback(() => {
    if (!nodeId) return;
    navigate(`/admin/nodes/${encodeURIComponent(nodeId)}/moderation`);
  }, [navigate, nodeId]);


  const heroActions = React.useMemo(() => {
    if (!nodeId) return null;
    return (
      <Button onClick={handleOpenModeration} variant="outlined" data-testid="engagement-open-moderation">
        Open moderation workspace
      </Button>
    );
  }, [handleOpenModeration, nodeId]);

  return (
    <div className="space-y-8">
      <PageHero
        title={headerTitle}
        description={headerDescription}
        eyebrow="Node analytics"
        breadcrumbs={[
          { label: 'Nodes', to: '/nodes/library' },
          { label: headerTitle },
        ]}
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
        <NodeEngagementSkeleton />
      ) : summary ? (
        <div className="grid gap-6 lg:grid-cols-12 lg:items-start">
          <div className="space-y-6 lg:col-span-8">
            <AnalyticsPanel nodeId={nodeId!} />
          </div>

          <div className="space-y-6 lg:col-span-4">
            <SummaryOverview
              summary={summary}
              onRefresh={handleRefreshSummary}
              refreshing={refreshing}
              nodeId={nodeId}
              currentView="analytics"
              showMetrics={false}
              className="bg-gradient-to-br from-white via-white to-transparent dark:from-dark-800/90 dark:via-dark-900/70 dark:to-dark-900/90"
            />
            <Card className="rounded-3xl border border-neutral-200/70 bg-gradient-to-br from-primary-50/60 via-white to-white p-6 dark:border-dark-600 dark:from-dark-700/40 dark:via-dark-800 dark:to-dark-900">
              <div className="space-y-5 text-sm text-neutral-600 dark:text-neutral-300">
                <div className="space-y-1">
                  <h3 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">Need moderation actions?</h3>
                  <p className="text-sm text-neutral-600 dark:text-neutral-300">Switch to the moderation workspace to review comments and bans.</p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    onClick={handleOpenModeration}
                    variant="ghost"
                    color="neutral"
                    className="px-5"
                  >
                    Open moderation workspace
                  </Button>
                </div>
                {quickLinkItems.length ? (
                  <nav className="mt-2 grid gap-1 text-sm text-primary-600 dark:text-primary-300">
                    {quickLinkItems.map((item) => {
                      const external = item.href.startsWith('http');
                      return external ? (
                        <a key={item.key} href={item.href} target="_blank" rel="noreferrer" className="hover:underline">
                          {item.label}
                        </a>
                      ) : (
                        <Link key={item.key} to={item.href} className="hover:underline">
                          {item.label}
                        </Link>
                      );
                    })}
                  </nav>
                ) : null}
              </div>
            </Card>
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

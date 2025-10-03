import React from 'react';
import { Link } from 'react-router-dom';
import { Badge, Button, Card, MetricCard } from '@ui';

import type { AdminNodeEngagementSummary } from '../types';

const STATUS_BADGE_THEME: Record<string, { color: 'neutral' | 'info' | 'success' | 'warning' | 'error'; label: string }> = {
  published: { color: 'success', label: 'Published' },
  pending: { color: 'info', label: 'Pending' },
  hidden: { color: 'warning', label: 'Hidden' },
  deleted: { color: 'error', label: 'Deleted' },
  blocked: { color: 'error', label: 'Blocked' },
};

const COMMENT_STATUS_TONE: Record<string, { color: 'neutral' | 'info' | 'success' | 'warning' | 'error'; label: string }> = {
  pending: { color: 'warning', label: 'Pending' },
  published: { color: 'success', label: 'Published' },
  hidden: { color: 'neutral', label: 'Hidden' },
  deleted: { color: 'error', label: 'Deleted' },
  blocked: { color: 'error', label: 'Blocked' },
};

type SummaryOverviewProps = {
  summary: AdminNodeEngagementSummary | null;
  refreshing?: boolean;
  onRefresh?: () => void;
};

function formatNumber(value: number | null | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return 'N/A';
  return value.toLocaleString();
}

function extractLikeCount(summary: AdminNodeEngagementSummary | null): number {
  if (!summary?.reactions || typeof summary.reactions !== 'object') return 0;
  const reactions = summary.reactions as Record<string, number>;
  const like = reactions.like ?? reactions['like'];
  return typeof like === 'number' ? like : 0;
}

export function SummaryOverview({ summary, refreshing, onRefresh }: SummaryOverviewProps) {
  const metrics = React.useMemo(() => {
    if (!summary) return [];
    const likes = extractLikeCount(summary);
    const commentsTotal = summary.comments?.total ?? summary.comments?.by_status?.published ?? 0;
    return [
      { label: 'Views', value: formatNumber(summary.views_count ?? 0), tone: 'primary' as const },
      { label: 'Likes', value: formatNumber(likes), tone: 'success' as const },
      { label: 'Comments', value: formatNumber(commentsTotal), tone: 'secondary' as const },
    ];
  }, [summary]);

  const commentStatusBadges = React.useMemo(() => {
    const entries = Object.entries(summary?.comments?.by_status ?? {});
    if (!entries.length) return null;
    return (
      <div className="flex flex-wrap gap-2">
        {entries.map(([status, count]) => {
          const tone = COMMENT_STATUS_TONE[status] ?? { color: 'neutral', label: status };
          return (
            <Badge key={status} color={tone.color} variant="soft">
              {tone.label}: {formatNumber(typeof count === 'number' ? count : 0)}
            </Badge>
          );
        })}
      </div>
    );
  }, [summary?.comments?.by_status]);

  const statusBadge = React.useMemo(() => {
    if (!summary?.status) return null;
    const tone = STATUS_BADGE_THEME[summary.status] ?? { color: 'neutral', label: summary.status };
    return (
      <Badge color={tone.color} variant="soft">
        {tone.label}
      </Badge>
    );
  }, [summary?.status]);

  const links = summary?.links ?? {};

  return (
    <Card className="space-y-6 p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">Node snapshot</h2>
          <p className="mt-1 text-sm text-neutral-600 dark:text-neutral-300">
            Engagement health and moderation context updated in near real-time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {statusBadge}
          <Button size="sm" variant="outlined" color="neutral" onClick={onRefresh} disabled={refreshing} data-testid="summary-refresh" data-analytics="admin.node.summary.refresh">
            {refreshing ? 'Refreshing...' : 'Refresh stats'}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2 text-sm text-neutral-600 dark:text-neutral-300">
          <div className="flex items-center gap-2">
            <span className="font-medium text-neutral-800 dark:text-neutral-200">Node ID:</span>
            <span>{summary?.id ?? 'N/A'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-medium text-neutral-800 dark:text-neutral-200">Slug:</span>
            <span>{summary?.slug ?? 'N/A'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-medium text-neutral-800 dark:text-neutral-200">Author:</span>
            <span>{summary?.author_id ?? 'N/A'}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-medium text-neutral-800 dark:text-neutral-200">Updated:</span>
            <span>{summary?.updated_at ?? 'N/A'}</span>
          </div>
          {commentStatusBadges}
        </div>
        <div className="space-y-2">
          {links.moderation && (
            <Link className="text-sm text-primary-600 hover:underline dark:text-primary-300" to={links.moderation}>
              Open moderation history
            </Link>
          )}
          {links.comments && (
            <Link className="text-sm text-primary-600 hover:underline dark:text-primary-300" to={links.comments}>
              Open comments view
            </Link>
          )}
          {links.analytics && (
            <Link className="text-sm text-primary-600 hover:underline dark:text-primary-300" to={links.analytics}>
              Open analytics dashboard
            </Link>
          )}
          {links.bans && (
            <Link className="text-sm text-primary-600 hover:underline dark:text-primary-300" to={links.bans}>
              Open ban management
            </Link>
          )}
        </div>
      </div>
    </Card>
  );
}


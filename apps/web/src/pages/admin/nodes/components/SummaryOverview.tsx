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
  nodeId?: string | null;
  currentView?: 'analytics' | 'moderation';
  showMetrics?: boolean;
  className?: string;
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

type TimelineItem = {
  id: string;
  title: string;
  at?: string | null;
  by?: string | null;
  tone?: 'default' | 'warning' | 'info';
  description?: string;
};

function buildTimeline(summary: AdminNodeEngagementSummary | null): TimelineItem[] {
  if (!summary) return [];

  const items: TimelineItem[] = [];
  const comments = summary.comments;

  if (comments?.locked_at) {
    items.push({
      id: 'locked',
      title: comments.locked ? 'Comments locked' : 'Comments lock updated',
      by: comments.locked_by || undefined,
      at: comments.locked_at,
      tone: comments.locked ? 'warning' : 'info',
      description: comments.locked ? 'New messages blocked until moderation finishes.' : 'Lock toggled from moderator panel.',
    });
  }

  if (comments?.disabled) {
    items.push({
      id: 'disabled',
      title: 'Comments disabled',
      description: 'Reply form hidden for visitors.',
      tone: 'warning',
      at: summary.updated_at,
    });
  }

  if (comments?.last_comment_created_at) {
    items.push({
      id: 'last-comment',
      title: 'Last comment received',
      at: comments.last_comment_created_at,
      description: comments.last_comment_updated_at ? `Updated at ${comments.last_comment_updated_at}` : undefined,
    });
  }

  if (summary.updated_at) {
    items.push({
      id: 'updated',
      title: 'Node updated',
      at: summary.updated_at,
    });
  }

  if (summary.created_at) {
    items.push({
      id: 'created',
      title: 'Node created',
      at: summary.created_at,
    });
  }

  return items;
}

function buildFrontLinks(nodeId?: string | null) {
  if (!nodeId) return null;
  const encoded = encodeURIComponent(nodeId);
  return {
    analytics: `/admin/nodes/${encoded}`,
    moderation: `/admin/nodes/${encoded}/moderation`,
    comments: `/admin/nodes/${encoded}/moderation#comments`,
    bans: `/admin/nodes/${encoded}/moderation#bans`,
  } as const;
}

export function SummaryOverview({ summary, refreshing, onRefresh, nodeId, currentView = 'analytics', showMetrics = true, className = '' }: SummaryOverviewProps) {
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

  const timelineItems = React.useMemo(() => buildTimeline(summary), [summary]);
  const frontLinks = React.useMemo(() => buildFrontLinks(nodeId ?? undefined), [nodeId]);
  const links = summary?.links ?? {};

  const moderationLink = frontLinks?.moderation ?? links.moderation ?? undefined;
  const commentsLink = frontLinks?.comments ?? links.comments ?? undefined;

  const activityLink = currentView === 'moderation' ? commentsLink ?? moderationLink : moderationLink;

  const cardClasses = `space-y-8 p-6 rounded-3xl border border-neutral-200/70 bg-white/90 shadow-sm dark:border-dark-600 dark:bg-dark-800/90 ${className}`.trim();

  return (
    <Card className={cardClasses}>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-1">
          <h2 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">Node snapshot</h2>
          <p className="text-sm text-neutral-600 dark:text-neutral-300">
            Engagement health and moderation context updated in near real-time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {statusBadge}
          <Button
            size="sm"
            variant="outlined"
            color="neutral"
            onClick={onRefresh}
            disabled={refreshing}
            data-testid="summary-refresh"
            data-analytics="admin.node.summary.refresh"
          >
            {refreshing ? 'Refreshing...' : 'Refresh stats'}
          </Button>
        </div>
      </div>

      {showMetrics && metrics.length ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {metrics.map((metric) => (
            <MetricCard key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} />
          ))}
        </div>
      ) : null}

      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-3 text-sm text-neutral-600 dark:text-neutral-300">
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

        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm font-medium text-neutral-800 dark:text-neutral-200">
            <span>Recent activity</span>
            {activityLink ? (
              <Link
                to={activityLink}
                className="text-xs font-medium text-primary-600 hover:underline dark:text-primary-300"
                target={activityLink.startsWith('http') ? '_blank' : undefined}
                rel={activityLink.startsWith('http') ? 'noreferrer' : undefined}
              >
                View all
              </Link>
            ) : null}
          </div>
          {timelineItems.length ? (
            <ul className="relative space-y-4 border-l border-neutral-200 pl-4 dark:border-dark-500">
              {timelineItems.map((item) => (
                <li key={item.id} className="relative text-sm text-neutral-600 dark:text-neutral-300">
                  <span
                    className={`absolute -left-[9px] top-1.5 h-2.5 w-2.5 rounded-full ${
                      item.tone === 'warning'
                        ? 'bg-amber-500'
                        : item.tone === 'info'
                        ? 'bg-primary-500'
                        : 'bg-neutral-300 dark:bg-dark-400'
                    }`}
                  />
                  <div className="font-medium text-neutral-800 dark:text-neutral-100">{item.title}</div>
                  {item.by ? (
                    <div className="text-xs text-neutral-500 dark:text-neutral-400">by {item.by}</div>
                  ) : null}
                  {item.description ? (
                    <div className="text-xs text-neutral-500 dark:text-neutral-400">{item.description}</div>
                  ) : null}
                  {item.at ? (
                    <div className="text-xs text-neutral-500 dark:text-neutral-400">{item.at}</div>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : (
            <div className="rounded-md border border-dashed border-neutral-300 p-4 text-xs text-neutral-500 dark:border-dark-600 dark:text-dark-200">
              No recent moderation events recorded.
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}

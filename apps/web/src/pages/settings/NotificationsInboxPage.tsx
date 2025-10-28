import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge, Button, Card } from '@ui';
import { SettingsLayout } from '@shared/settings/SettingsLayout';
import { WalletConnectionCard } from '@shared/settings/WalletConnectionCard';
import { formatDateTime } from '@shared/utils/format';
import {
  NotificationInbox,
  type NotificationInboxOverview,
} from '@features/notifications/inbox';

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return '--';
  const formatted = formatDateTime(value);
  return formatted || '--';
}

export default function NotificationsInboxPage(): React.ReactElement {
  const navigate = useNavigate();
  const [overview, setOverview] = React.useState<NotificationInboxOverview | null>(null);

  const statusBadge = React.useMemo(() => {
    if (!overview) {
      return (
        <Badge color="neutral" variant="soft">
          Loading
        </Badge>
      );
    }
    if (overview.hasError) {
      return (
        <Badge color="warning" variant="soft">
          Attention
        </Badge>
      );
    }
    if (overview.loading) {
      return (
        <Badge color="primary" variant="soft">
          Syncing
        </Badge>
      );
    }
    return (
      <Badge color="success" variant="soft">
        Up to date
      </Badge>
    );
  }, [overview]);

  return (
    <SettingsLayout
      title="Notifications inbox"
      description="Review personal alerts, mark them as read, and keep track of retention without leaving settings."
      side={<WalletConnectionCard />}
    >
      <div className="space-y-6">
        <Card className="space-y-4 rounded-3xl border border-white/60 bg-white/70 p-4 shadow-sm dark:border-dark-600/60 dark:bg-dark-700/70">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1">
              <h2 className="text-sm font-semibold text-gray-700 dark:text-dark-100">Inbox overview</h2>
              <p className="text-xs text-gray-500 dark:text-dark-300">
                Snapshot of unread volume, retention window, and the most recent notification.
              </p>
            </div>
            {statusBadge}
          </div>
          <dl className="grid gap-3 text-sm text-gray-600 dark:text-dark-200 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-1 rounded-2xl border border-gray-200/60 bg-white/80 p-3 text-sm shadow-sm dark:border-dark-600/50 dark:bg-dark-700/70">
              <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-400">Unread</dt>
              <dd className="text-lg font-semibold text-gray-900 dark:text-dark-50">
                {overview ? overview.unread : '--'}
              </dd>
            </div>
            <div className="space-y-1 rounded-2xl border border-gray-200/60 bg-white/80 p-3 text-sm shadow-sm dark:border-dark-600/50 dark:bg-dark-700/70">
              <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-400">Loaded</dt>
              <dd className="text-lg font-semibold text-gray-900 dark:text-dark-50">
                {overview ? overview.total : '--'}
              </dd>
            </div>
            <div className="space-y-1 rounded-2xl border border-gray-200/60 bg-white/80 p-3 text-sm shadow-sm dark:border-dark-600/50 dark:bg-dark-700/70">
              <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-400">Retention</dt>
              <dd className="text-lg font-semibold text-gray-900 dark:text-dark-50">
                {overview ? `${overview.retentionDays} days` : '--'}
                <span className="ml-1 text-xs text-gray-500 dark:text-dark-300">
                  {overview ? `(${overview.retentionMax} records)` : ''}
                </span>
              </dd>
            </div>
            <div className="space-y-1 rounded-2xl border border-gray-200/60 bg-white/80 p-3 text-sm shadow-sm dark:border-dark-600/50 dark:bg-dark-700/70">
              <dt className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-400">Latest entry</dt>
              <dd className="text-lg font-semibold text-gray-900 dark:text-dark-50">
                {formatTimestamp(overview?.lastReceivedAt)}
              </dd>
            </div>
          </dl>
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <Button
              type="button"
              size="sm"
              variant="ghost"
              color="neutral"
              onClick={() => navigate('/settings/notifications')}
            >
              Manage preferences
            </Button>
            <Button
              type="button"
              size="sm"
              color="primary"
              onClick={() => navigate('/notifications')}
            >
              Notifications hub
            </Button>
          </div>
        </Card>
        <NotificationInbox onOverviewChange={setOverview} />
      </div>
    </SettingsLayout>
  );
}

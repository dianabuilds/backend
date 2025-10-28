import React from 'react';
import { Badge, Button, Card, Spinner, Switch } from '@ui';
import { formatDateTime } from '@shared/utils/format';
import type { NotificationHistoryItem } from '@shared/types/notifications';
import { useNotificationsHistory } from '../../common/hooks';

function useRetentionConfig(): { days: number; maxPerUser: number } {
  const daysRaw = (import.meta as any).env?.VITE_NOTIFICATIONS_RETENTION_DAYS;
  const maxRaw = (import.meta as any).env?.VITE_NOTIFICATIONS_MAX_PER_USER;
  const days = Number.parseInt(daysRaw ?? '', 10);
  const maxPerUser = Number.parseInt(maxRaw ?? '', 10);
  return {
    days: Number.isFinite(days) && days > 0 ? days : 90,
    maxPerUser: Number.isFinite(maxPerUser) && maxPerUser > 0 ? maxPerUser : 200,
  };
}

export type NotificationInboxOverview = {
  unread: number;
  total: number;
  hasError: boolean;
  loading: boolean;
  lastReceivedAt: string | null;
  retentionDays: number;
  retentionMax: number;
};

const NotificationCard = React.memo(
  ({
    item,
    marking,
    onMarkRead,
  }: {
    item: NotificationHistoryItem;
    marking: Record<string, boolean>;
    onMarkRead: (id: string) => void;
  }) => {
    const createdAt = formatDateTime(item.created_at) || '-';
    const message = React.useMemo(() => item.message?.trim() ?? '', [item.message]);
    const unread = !item.read_at;
    const handleMark = React.useCallback(() => onMarkRead(item.id), [item.id, onMarkRead]);

    return (
      <div className="rounded-2xl border border-gray-200/70 bg-white/90 p-4 shadow-sm transition hover:border-primary-200 hover:shadow-md dark:border-dark-600/50 dark:bg-dark-700/70">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-semibold text-gray-900 dark:text-dark-50">
                {item.title || 'Notification'}
              </span>
              <Badge color={unread ? 'info' : 'neutral'} variant="soft">
                {unread ? 'Pending' : 'Read'}
              </Badge>
              <Badge variant="soft" color="neutral">
                {item.type || 'system'}
              </Badge>
            </div>
            {message ? (
              <p className="max-w-[48rem] whitespace-pre-wrap break-words text-sm text-gray-600 dark:text-dark-200">
                {message}
              </p>
            ) : null}
            <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-dark-300">
              <span>{createdAt}</span>
              <span aria-hidden="true">/</span>
              {unread ? (
                <Button
                  variant="ghost"
                  color="neutral"
                  size="xs"
                  onClick={handleMark}
                  disabled={marking[item.id]}
                >
                  {marking[item.id] ? '...' : 'Mark read'}
                </Button>
              ) : (
                <span className="text-gray-400 dark:text-dark-300">Marked as read</span>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  },
);

NotificationCard.displayName = 'NotificationCard';

type NotificationInboxProps = {
  onOverviewChange?: (overview: NotificationInboxOverview) => void;
};

export function NotificationInbox({ onOverviewChange }: NotificationInboxProps = {}): React.ReactElement {
  const { days, maxPerUser } = useRetentionConfig();
  const [showUnreadOnly, setShowUnreadOnly] = React.useState(false);
  const { items, loading, loadingMore, error, hasMore, refresh, loadMore, markAsRead } = useNotificationsHistory({
    pageSize: 25,
  });
  const [marking, setMarking] = React.useState<Record<string, boolean>>({});

  React.useEffect(() => {
    const handler = () => {
      void refresh();
    };
    window.addEventListener('notifications:refresh', handler);
    return () => {
      window.removeEventListener('notifications:refresh', handler);
    };
  }, [refresh]);

  const unreadCount = React.useMemo(() => items.filter((item) => !item.read_at).length, [items]);
  const filteredItems = React.useMemo(
    () => (showUnreadOnly ? items.filter((item) => !item.read_at) : items),
    [items, showUnreadOnly],
  );
  const lastReceivedAt = React.useMemo(() => {
    const latest = items[0];
    return latest?.created_at ?? latest?.updated_at ?? null;
  }, [items]);

  const handleToggleUnread = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setShowUnreadOnly(event.currentTarget.checked);
  }, []);

  const handleMarkRead = React.useCallback(
    async (notificationId: string) => {
      const id = notificationId.trim();
      if (!id) return;
      setMarking((prev) => ({ ...prev, [id]: true }));
      try {
        await markAsRead(id);
      } finally {
        setMarking((prev) => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
      }
    },
    [markAsRead],
  );

  React.useEffect(() => {
    if (!onOverviewChange) return;
    onOverviewChange({
      unread: unreadCount,
      total: items.length,
      hasError: Boolean(error),
      loading,
      lastReceivedAt,
      retentionDays: days,
      retentionMax: maxPerUser,
    });
  }, [onOverviewChange, unreadCount, items.length, error, loading, lastReceivedAt, days, maxPerUser]);

  return (
    <Card className="space-y-5 rounded-3xl border border-gray-100 bg-white p-5 shadow-sm dark:border-dark-600/60 dark:bg-dark-750/80 sm:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="text-[11px] font-semibold uppercase tracking-widest text-primary-600">Inbox</div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-dark-50">Personal notifications</h2>
          <p className="text-sm text-gray-600 dark:text-dark-200">
            Inbox keeps notifications for the last {days} days and stores up to {maxPerUser} recent entries.
          </p>
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
            <Badge color="info" variant="soft">
              {unreadCount}
            </Badge>
            <span>unread</span>
          </div>
        </div>
        <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
          <label className="flex items-center gap-3 text-sm text-gray-700 dark:text-dark-100">
            <Switch checked={showUnreadOnly} onChange={handleToggleUnread} />
            Unread only
          </label>
          <Button
            variant="outlined"
            color="neutral"
            onClick={() => void refresh()}
            disabled={loading || loadingMore}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
      ) : null}

      {loading && !items.length ? (
        <div className="flex min-h-[220px] items-center justify-center">
          <div className="flex items-center gap-2 text-sm text-indigo-600 dark:text-dark-200">
            <Spinner size="sm" />
            <span>Loading notifications...</span>
          </div>
        </div>
      ) : null}

      <div className="grid gap-3">
        {filteredItems.map((item) => (
          <NotificationCard key={item.id} item={item} marking={marking} onMarkRead={handleMarkRead} />
        ))}
      </div>

      {!loading && filteredItems.length === 0 && !error ? (
        <div className="rounded-2xl border border-dashed border-gray-200 p-6 text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
          {showUnreadOnly ? 'No unread notifications.' : 'Inbox is empty for now.'}
        </div>
      ) : null}

      {hasMore ? (
        <div className="flex justify-center">
          <Button
            variant="ghost"
            color="neutral"
            onClick={() => void loadMore()}
            disabled={loadingMore}
          >
            {loadingMore ? 'Loading...' : 'Load more'}
          </Button>
        </div>
      ) : null}
    </Card>
  );
}

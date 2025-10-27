import React from 'react';
import { Badge, Button, Spinner, Switch, Table } from '@ui';
import { NotificationSurface, notificationTableHeadCellClass, notificationTableRowClass } from '../../common/NotificationSurface';
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

function formatPriority(priority?: string | null): React.ReactNode {
  const value = String(priority ?? 'normal').toLowerCase();
  if (value === 'urgent' || value === 'high') {
    return (
      <Badge color="warning" variant="soft">
        {value}
      </Badge>
    );
  }
  if (value === 'low') {
    return (
      <Badge color="neutral" variant="soft">
        {value}
      </Badge>
    );
  }
  return (
    <Badge color="info" variant="soft">
      normal
    </Badge>
  );
}

function InboxTable({
  items,
  onMarkRead,
  marking,
}: {
  items: NotificationHistoryItem[];
  onMarkRead: (id: string) => void;
  marking: Record<string, boolean>;
}) {
  if (!items.length) return null;
  return (
    <div className="hide-scrollbar overflow-x-auto">
      <Table.Table className="min-w-[900px] text-left rtl:text-right">
        <Table.THead>
          <Table.TR>
            <Table.TH className={`${notificationTableHeadCellClass} w-[42%]`}>Notification</Table.TH>
            <Table.TH className={`${notificationTableHeadCellClass} w-[12%]`}>Type</Table.TH>
            <Table.TH className={`${notificationTableHeadCellClass} w-[12%]`}>Priority</Table.TH>
            <Table.TH className={`${notificationTableHeadCellClass} w-[18%]`}>Created</Table.TH>
            <Table.TH className={`${notificationTableHeadCellClass} w-[16%]`}>Status</Table.TH>
          </Table.TR>
        </Table.THead>
        <Table.TBody>
          {items.map((item) => (
            <Table.TR key={item.id} className={notificationTableRowClass}>
              <Table.TD className="px-6 py-4 align-top">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900 dark:text-dark-50">{item.title || 'Notification'}</span>
                    {!item.read_at && <span className="inline-flex h-2 w-2 rounded-full bg-primary-500" />}
                  </div>
                  {item.message ? <p className="text-sm text-gray-600 dark:text-dark-200">{item.message}</p> : null}
                </div>
              </Table.TD>
              <Table.TD className="px-6 py-4 align-top">
                <Badge variant="soft" color="neutral">
                  {item.type || 'system'}
                </Badge>
              </Table.TD>
              <Table.TD className="px-6 py-4 align-top">{formatPriority(item.priority)}</Table.TD>
              <Table.TD className="px-6 py-4 align-top text-sm text-gray-600">
                {formatDateTime(item.created_at) || '-'}
              </Table.TD>
              <Table.TD className="px-6 py-4 align-top">
                <div className="flex items-center gap-3">
                  <Badge color={item.read_at ? 'neutral' : 'info'} variant="soft">
                    {item.read_at ? 'Read' : 'Pending'}
                  </Badge>
                  <Button
                    variant="ghost"
                    color="neutral"
                    size="xs"
                    onClick={() => onMarkRead(item.id)}
                    disabled={!!item.read_at || marking[item.id]}
                  >
                    {marking[item.id] ? '...' : item.read_at ? 'Done' : 'Mark read'}
                  </Button>
                </div>
              </Table.TD>
            </Table.TR>
          ))}
        </Table.TBody>
      </Table.Table>
    </div>
  );
}

export function NotificationInbox(): React.ReactElement {
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

  return (
    <NotificationSurface className="space-y-6 p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-1">
          <div className="text-xs font-semibold uppercase tracking-widest text-primary-600">Inbox</div>
          <h2 className="text-2xl font-semibold text-gray-900">Personal notifications</h2>
          <p className="text-sm text-gray-600 dark:text-dark-200">
            Инбокс хранит уведомления за последние {days} дней и показывает до {maxPerUser} последних записей.
          </p>
          <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
            <Badge color="info" variant="soft">
              {unreadCount}
            </Badge>
            непрочитанных
          </div>
        </div>
        <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
          <label className="flex items-center gap-3 text-sm text-gray-700 dark:text-dark-100">
            <Switch checked={showUnreadOnly} onChange={handleToggleUnread} />
            Только непрочитанные
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
            <span>Загружаем уведомления...</span>
          </div>
        </div>
      ) : null}

      <InboxTable items={filteredItems} onMarkRead={handleMarkRead} marking={marking} />

      {!loading && filteredItems.length === 0 && !error ? (
        <div className="rounded-2xl border border-dashed border-gray-200 p-6 text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
          {showUnreadOnly ? 'Непрочитанных уведомлений нет.' : 'Инбокс пока пуст.'}
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
    </NotificationSurface>
  );
}

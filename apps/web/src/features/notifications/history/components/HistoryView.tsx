import React from 'react';
import { Badge, Button, Spinner, Table } from '@ui';
import { NotificationSurface, notificationTableHeadCellClass, notificationTableRowClass } from '../../common/NotificationSurface';
import { formatDateTime } from '@shared/utils/format';
import type { NotificationHistoryItem } from '@shared/types/notifications';
import { useNotificationsHistory } from '../hooks';

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

function HistoryTable({ items }: { items: NotificationHistoryItem[] }) {
  if (!items.length) return null;
  return (
    <div className="hide-scrollbar overflow-x-auto">
      <Table.Table className="min-w-[900px] text-left rtl:text-right">
        <Table.THead>
          <Table.TR>
            <Table.TH className={`${notificationTableHeadCellClass} w-[40%]`}>Notification</Table.TH>
            <Table.TH className={`${notificationTableHeadCellClass} w-[12%]`}>Type</Table.TH>
            <Table.TH className={`${notificationTableHeadCellClass} w-[12%]`}>Priority</Table.TH>
            <Table.TH className={`${notificationTableHeadCellClass} w-[18%]`}>Created</Table.TH>
            <Table.TH className={`${notificationTableHeadCellClass} w-[18%]`}>Status</Table.TH>
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
                <Badge color={item.read_at ? 'neutral' : 'info'} variant="soft">
                  {item.read_at ? 'Read' : 'Pending'}
                </Badge>
              </Table.TD>
            </Table.TR>
          ))}
        </Table.TBody>
      </Table.Table>
    </div>
  );
}

export function NotificationHistory(): React.ReactElement {
  const { items, loading, loadingMore, error, hasMore, refresh, loadMore } = useNotificationsHistory();

  return (
    <NotificationSurface className="space-y-6 p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <div className="text-xs font-semibold uppercase tracking-widest text-primary-600">Notifications</div>
          <h2 className="text-2xl font-semibold text-gray-900">Activity log</h2>
          <p className="text-sm text-gray-600">
            Review the most recent notifications delivered to your account across every channel.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outlined" color="neutral" onClick={() => void refresh()} disabled={loading || loadingMore}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
      ) : null}

      {loading && !items.length ? (
        <div className="flex min-h-[160px] items-center justify-center">
          <div className="flex items-center gap-2 text-sm text-indigo-600">
            <Spinner size="sm" />
            <span>Loading history...</span>
          </div>
        </div>
      ) : null}

      <HistoryTable items={items} />

      {!loading && items.length === 0 && !error ? (
        <div className="rounded-2xl border border-dashed border-gray-200 p-6 text-sm text-gray-500">
          No notifications were delivered yet.
        </div>
      ) : null}

      {hasMore ? (
        <div className="flex justify-center">
          <Button variant="ghost" color="neutral" onClick={() => void loadMore()} disabled={loadingMore}>
            {loadingMore ? 'Loading...' : 'Load more'}
          </Button>
        </div>
      ) : null}
    </NotificationSurface>
  );
}
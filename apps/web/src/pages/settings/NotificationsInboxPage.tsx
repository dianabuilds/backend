import React from 'react';
import { SettingsLayout } from '../../shared/settings/SettingsLayout';
import { NotificationSurface, notificationTableHeadCellClass, notificationTableRowClass } from '../notifications/NotificationSurface';
import { Button, Pagination, Select, Spinner, Table } from '@ui';
import { apiGet, apiPost } from '../../shared/api/client';

type NotificationItem = {
  id: string;
  title: string;
  message: string;
  type: string;
  placement: string;
  priority: string;
  created_at: string;
  updated_at?: string | null;
  read_at?: string | null;
  cta_label?: string | null;
  cta_url?: string | null;
  meta?: Record<string, unknown> | null;
};

type NotificationsResponse = {
  items?: NotificationItem[];
  unread?: number;
};

const PAGE_SIZES = [10, 20, 30, 50];

function formatTimestamp(value?: string | null): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export default function NotificationsInboxPage(): React.ReactElement {
  const [items, setItems] = React.useState<NotificationItem[]>([]);
  const [unreadTotal, setUnreadTotal] = React.useState(0);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(10);
  const [hasNext, setHasNext] = React.useState(false);
  const [marking, setMarking] = React.useState<Record<string, boolean>>({});

  const fetchInbox = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    const offset = (page - 1) * pageSize;
    try {
      const response = await apiGet<NotificationsResponse>(`/v1/notifications?limit=${pageSize}&offset=${offset}`);
      const rows = Array.isArray(response?.items) ? response.items : [];
      const unread = typeof response?.unread === 'number' ? response.unread : rows.filter((item) => !item.read_at).length;
      setItems(rows);
      setUnreadTotal(unread);
      setHasNext(rows.length === pageSize);
    } catch (err: any) {
      setError(err?.message || 'Failed to load notifications. Please try again.');
      setItems([]);
      setUnreadTotal(0);
      setHasNext(false);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  React.useEffect(() => {
    void fetchInbox();
  }, [fetchInbox]);

  const pageUnread = React.useMemo(() => items.filter((item) => !item.read_at).length, [items]);

  const markAsRead = React.useCallback(
    async (notificationId: string) => {
      setMarking((prev) => ({ ...prev, [notificationId]: true }));
      try {
        const response = await apiPost<{ notification?: NotificationItem }>(`/v1/notifications/read/${notificationId}`,
          {},
        );
        const updated = response?.notification;
        const fallbackReadAt = new Date().toISOString();
        let wasUnread = false;
        setItems((prev) =>
          prev.map((item) => {
            if (item.id !== notificationId) {
              return item;
            }
            if (!item.read_at) {
              wasUnread = true;
            }
            return {
              ...item,
              ...(updated ?? {}),
              read_at: updated?.read_at ?? updated?.updated_at ?? item.read_at ?? fallbackReadAt,
            };
          }),
        );
        if (wasUnread) {
          setUnreadTotal((value) => (value > 0 ? value - 1 : 0));
        }
        window.dispatchEvent(new CustomEvent('notifications:refresh'));
      } catch (err: any) {
        setError(err?.message || 'Unable to mark the notification as read.');
      } finally {
        setMarking((prev) => {
          const next = { ...prev };
          delete next[notificationId];
          return next;
        });
      }
    },
    [],
  );

  const handleRefresh = React.useCallback(async () => {
    await fetchInbox();
    window.dispatchEvent(new CustomEvent('notifications:refresh'));
  }, [fetchInbox]);


  return (
    <SettingsLayout
      title="Notification inbox"
      description="Review the most recent in-product alerts delivered to your account."
      error={error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
      ) : null}
    >
      <NotificationSurface className="space-y-6 p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <div className="text-xs font-semibold uppercase tracking-widest text-primary-600">Notifications</div>
            <h2 className="text-2xl font-semibold text-gray-900">Inbox</h2>
            <p className="text-sm text-gray-600">
              Showing {items.length} item(s) on this page. Unread on page: {pageUnread}. Total unread: {unreadTotal}.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant="outlined" color="neutral" onClick={handleRefresh} disabled={loading}>
              Refresh
            </Button>
          </div>
        </div>
        <div className="grid gap-3 rounded-2xl border border-white/60 bg-white/80 p-4 shadow-sm sm:grid-cols-2 lg:grid-cols-4">
          <div className="flex flex-col">
            <span className="text-xs uppercase tracking-wide text-gray-500">Total items</span>
            <span className="mt-1 text-lg font-semibold text-gray-900">{items.length}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs uppercase tracking-wide text-gray-500">Total unread</span>
            <span className="mt-1 text-lg font-semibold text-gray-900">{unreadTotal}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs uppercase tracking-wide text-gray-500">Unread on page</span>
            <span className="mt-1 text-lg font-semibold text-gray-900">{pageUnread}</span>
          </div>
          <div className="flex flex-col">
            <span className="text-xs uppercase tracking-wide text-gray-500">Page size</span>
            <span className="mt-1 text-lg font-semibold text-gray-900">{pageSize}</span>
          </div>
        </div>

        <div className="hide-scrollbar overflow-x-auto">
          <Table.Table className="min-w-[720px] text-left rtl:text-right">
            <Table.THead>
              <Table.TR>
                <Table.TH className={`${notificationTableHeadCellClass} w-[60%]`}>Notification</Table.TH>
                <Table.TH className={`${notificationTableHeadCellClass} w-[25%]`}>Created</Table.TH>
                <Table.TH className={`${notificationTableHeadCellClass} w-[15%] text-right`}>Actions</Table.TH>
              </Table.TR>
            </Table.THead>
            <Table.TBody>
              {loading && (
                <Table.TR className={notificationTableRowClass}>
                  <Table.TD colSpan={3} className="px-6 py-10 text-center">
                    <div className="flex items-center justify-center gap-2 text-sm text-indigo-600">
                      <Spinner size="sm" />
                      <span>Loading notifications...</span>
                    </div>
                  </Table.TD>
                </Table.TR>
              )}
              {!loading &&
                items.map((item) => (
                  <Table.TR
                    key={item.id}
                    className={`${notificationTableRowClass} ${!item.read_at ? 'bg-indigo-50/60 dark:bg-dark-700/70' : ''}`}
                  >
                    <Table.TD className="px-6 py-4 align-top">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 dark:text-dark-50">{item.title || 'Notification'}</span>
                          {!item.read_at && <span className="inline-flex h-2 w-2 rounded-full bg-primary-500" />}
                        </div>
                        <div className="text-sm text-gray-600 break-words whitespace-pre-wrap dark:text-dark-200">{item.message}</div>
                        {(() => {
                          const topicValue = item.meta?.topic;
                          return topicValue !== undefined && topicValue !== null ? (
                            <div className="text-xs text-gray-400">Topic: {String(topicValue)}</div>
                          ) : null;
                        })()}
                        {item.cta_url && (
                          <a
                            href={item.cta_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-medium text-primary-600 hover:underline"
                          >
                            {item.cta_label || 'Open link'}
                          </a>
                        )}
                      </div>
                    </Table.TD>
                    <Table.TD className="px-6 py-4 align-top">
                      <div className="text-sm text-gray-700 dark:text-dark-100">{formatTimestamp(item.created_at)}</div>
                      {item.read_at && (
                        <div className="text-xs text-gray-400">Read: {formatTimestamp(item.read_at)}</div>
                      )}
                    </Table.TD>
                    <Table.TD className="px-6 py-4 align-top text-right">
                      <Button
                        size="sm"
                        variant="outlined"
                        onClick={() => markAsRead(item.id)}
                        disabled={!!item.read_at || marking[item.id]}
                      >
                        {marking[item.id] ? '...' : item.read_at ? 'Read' : 'Mark as read'}
                      </Button>
                    </Table.TD>
                  </Table.TR>
                ))}
              {!loading && items.length === 0 && (
                <Table.TR className={notificationTableRowClass}>
                  <Table.TD colSpan={3} className="px-6 py-12 text-center text-sm text-gray-500">
                    No notifications to display yet.
                  </Table.TD>
                </Table.TR>
              )}
            </Table.TBody>
          </Table.Table>
        </div>

        <div className="flex flex-col gap-3 border-t border-white/50 pt-4 sm:flex-row sm:items-center sm:justify-between dark:border-dark-600/50">
          <div className="flex items-center gap-2 text-sm text-indigo-600">
            <span>Rows per page</span>
            <Select
              value={String(pageSize)}
              onChange={(event) => {
                setPageSize(Number(event.target.value));
                setPage(1);
              }}
              className="h-9 w-24 text-xs"
            >
              {PAGE_SIZES.map((size) => (
                <option key={size} value={size}>
                  {size}
                </option>
              ))}
            </Select>
          </div>
          <Pagination page={page} hasNext={hasNext} onChange={setPage} />
        </div>
      </NotificationSurface>
    </SettingsLayout>
  );
}










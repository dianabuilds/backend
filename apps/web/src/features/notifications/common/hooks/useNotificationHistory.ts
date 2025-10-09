import React from 'react';
import {
  fetchNotificationsHistory,
  markNotificationAsRead,
  type FetchNotificationsHistoryOptions,
} from '@shared/api/notifications';
import type { NotificationHistoryItem } from '@shared/types/notifications';

export type UseNotificationsHistoryOptions = {
  pageSize?: number;
  autoFetch?: boolean;
};

export type UseNotificationsHistoryResult = {
  items: NotificationHistoryItem[];
  loading: boolean;
  loadingMore: boolean;
  error: string | null;
  hasMore: boolean;
  refresh: () => Promise<void>;
  loadMore: () => Promise<void>;
  markAsRead: (notificationId: string) => Promise<void>;
};

const DEFAULT_FETCH_ERROR = 'Failed to load notification history.';
const DEFAULT_MARK_ERROR = 'Failed to mark the notification as read.';

export function useNotificationsHistory(
  options: UseNotificationsHistoryOptions = {},
): UseNotificationsHistoryResult {
  const pageSize = options.pageSize ?? 30;
  const autoFetch = options.autoFetch ?? true;

  const [items, setItems] = React.useState<NotificationHistoryItem[]>([]);
  const [loading, setLoading] = React.useState<boolean>(autoFetch);
  const [loadingMore, setLoadingMore] = React.useState(false);
  const [hasMore, setHasMore] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const offsetRef = React.useRef(0);
  const abortRef = React.useRef<AbortController | null>(null);
  const mountedRef = React.useRef(true);
  const pageSizeRef = React.useRef(pageSize);

  React.useEffect(() => {
    pageSizeRef.current = pageSize;
  }, [pageSize]);

  React.useEffect(() => () => {
    mountedRef.current = false;
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  const runFetch = React.useCallback(
    async (mode: 'refresh' | 'append') => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      if (mode === 'refresh') {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }
      setError(null);

      const params: FetchNotificationsHistoryOptions = {
        limit: pageSizeRef.current,
        offset: mode === 'refresh' ? 0 : offsetRef.current,
        signal: controller.signal,
      };

      try {
        const page = await fetchNotificationsHistory(params);
        if (!mountedRef.current || controller.signal.aborted) {
          return;
        }
        setItems((prev) => (mode === 'append' ? [...prev, ...page.items] : page.items));
        offsetRef.current = page.nextOffset;
        setHasMore(page.hasMore);
      } catch (err: unknown) {
        if (!mountedRef.current || controller.signal.aborted) {
          return;
        }
        if (mode === 'refresh') {
          setItems([]);
          offsetRef.current = 0;
          setHasMore(false);
        }
        const message =
          (err as Error)?.message?.trim() || DEFAULT_FETCH_ERROR;
        setError(message);
      } finally {
        const aborted = controller.signal.aborted;
        abortRef.current = null;
        if (mountedRef.current && !aborted) {
          if (mode === 'refresh') {
            setLoading(false);
          } else {
            setLoadingMore(false);
          }
        }
      }
    },
    [],
  );

  const refresh = React.useCallback(async () => {
    await runFetch('refresh');
  }, [runFetch]);

  const loadMore = React.useCallback(async () => {
    if (loadingMore || !hasMore) {
      return;
    }
    await runFetch('append');
  }, [hasMore, loadingMore, runFetch]);

  React.useEffect(() => {
    if (!autoFetch) return;
    void refresh();
  }, [autoFetch, refresh]);

  const markAsRead = React.useCallback(async (notificationId: string) => {
    const id = notificationId.trim();
    if (!id) {
      setError(DEFAULT_MARK_ERROR);
      return;
    }
    try {
      const updated = await markNotificationAsRead(id);
      if (!mountedRef.current) {
        return;
      }
      const fallbackReadAt = new Date().toISOString();
      setItems((prev) =>
        prev.map((item) => {
          if (item.id !== id) {
            return item;
          }
          const nextReadAt =
            updated?.read_at ?? updated?.created_at ?? item.read_at ?? fallbackReadAt;
          return {
            ...item,
            ...(updated ?? {}),
            read_at: nextReadAt,
          };
        }),
      );
    } catch (err: unknown) {
      if (!mountedRef.current) {
        return;
      }
      const message = (err as Error)?.message?.trim() || DEFAULT_MARK_ERROR;
      setError(message);
    }
  }, []);

  return {
    items,
    loading,
    loadingMore,
    error,
    hasMore,
    refresh,
    loadMore,
    markAsRead,
  };
}

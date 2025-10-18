import React from 'react';

import { fetchNotificationBroadcasts } from '@shared/api/notifications';
import type {
  NotificationBroadcast,
  NotificationBroadcastListResponse,
  NotificationBroadcastStatus,
} from '@shared/types/notifications';
import { usePaginatedQuery } from '@shared/hooks/usePaginatedQuery';
import { extractErrorMessage } from '@shared/utils/errors';

const EMPTY_STATUS_COUNTS: Record<NotificationBroadcastStatus, number> = {
  draft: 0,
  scheduled: 0,
  sending: 0,
  sent: 0,
  failed: 0,
  cancelled: 0,
};

type BroadcastQueryResult = {
  response: NotificationBroadcastListResponse | null;
  items: NotificationBroadcast[];
};

export type UseNotificationBroadcastsOptions = {
  status?: NotificationBroadcastStatus | 'all';
  search?: string;
  pageSize?: number;
  debounceMs?: number;
  mapError?: (error: unknown) => string;
};

export type UseNotificationBroadcastsResult = {
  broadcasts: NotificationBroadcast[];
  page: number;
  setPage: (page: number) => void;
  pageSize: number;
  setPageSize: (pageSize: number) => void;
  hasNext: boolean;
  loading: boolean;
  error: string | null;
  setError: React.Dispatch<React.SetStateAction<string | null>>;
  refresh: () => Promise<void>;
  statusCounts: Record<NotificationBroadcastStatus, number>;
  total: number;
  recipients: number;
};

export function useNotificationBroadcasts({
  status = 'all',
  search = '',
  pageSize = 20,
  debounceMs = 300,
  mapError,
}: UseNotificationBroadcastsOptions = {}): UseNotificationBroadcastsResult {
  const normalizedStatus = status;
  const normalizedSearch = search.trim();

  const [statusCounts, setStatusCounts] = React.useState<Record<NotificationBroadcastStatus, number>>({
    ...EMPTY_STATUS_COUNTS,
  });
  const [total, setTotal] = React.useState(0);
  const [recipients, setRecipients] = React.useState(0);

  const {
    items: broadcasts,
    page,
    setPage,
    pageSize: currentPageSize,
    setPageSize,
    hasNext,
    loading,
    error,
    setError,
    refresh,
  } = usePaginatedQuery<NotificationBroadcast, BroadcastQueryResult>({
    initialPageSize: pageSize,
    debounceMs,
    dependencies: [normalizedStatus, normalizedSearch],
    fetcher: async ({ page: currentPage, pageSize: currentSize, signal }) => {
      const offset = Math.max(0, (currentPage - 1) * currentSize);
      const statuses = normalizedStatus === 'all' ? undefined : [normalizedStatus];
      const response = await fetchNotificationBroadcasts({
        limit: currentSize,
        offset,
        statuses,
        search: normalizedSearch || undefined,
        signal,
      });
      const items = Array.isArray(response?.items) ? response.items : [];
      return { response: response ?? null, items };
    },
    mapResponse: (result, { page: currentPage, pageSize: currentSize }) => {
      const response = result.response;
      const items = Array.isArray(result.items) ? result.items : [];
      const offset = typeof response?.offset === 'number' ? response.offset : (currentPage - 1) * currentSize;
      const totalItems = typeof response?.total === 'number' ? response.total : offset + items.length;
      setTotal(totalItems);

      const counts = response?.status_counts ?? {};
      setStatusCounts({
        draft: counts.draft ?? 0,
        scheduled: counts.scheduled ?? 0,
        sending: counts.sending ?? 0,
        sent: counts.sent ?? 0,
        failed: counts.failed ?? 0,
        cancelled: counts.cancelled ?? 0,
      });

      const aggregatedRecipients =
        typeof response?.recipients === 'number'
          ? response.recipients
          : items.reduce((sum, item) => sum + (Number.isFinite(item.total) ? Number(item.total) : 0), 0);
      setRecipients(aggregatedRecipients);

      const hasNextFlag =
        typeof response?.has_next === 'boolean'
          ? response.has_next
          : offset + items.length < totalItems;

      return {
        items,
        hasNext: hasNextFlag,
        total: totalItems,
      };
    },
    onError: (err) => (mapError ? mapError(err) : extractErrorMessage(err)),
  });

  React.useEffect(() => {
    setPage(1);
  }, [normalizedStatus, normalizedSearch, setPage]);

  React.useEffect(() => {
    setStatusCounts({ ...EMPTY_STATUS_COUNTS });
    setTotal(0);
    setRecipients(0);
  }, [normalizedStatus, normalizedSearch]);

  React.useEffect(() => {
    if (error) {
      setStatusCounts({ ...EMPTY_STATUS_COUNTS });
      setTotal(0);
      setRecipients(0);
    }
  }, [error]);

  return {
    broadcasts,
    page,
    setPage,
    pageSize: currentPageSize,
    setPageSize,
    hasNext,
    loading,
    error,
    setError,
    refresh,
    statusCounts,
    total,
    recipients,
  };
}

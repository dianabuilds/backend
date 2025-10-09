import React from "react";

import { fetchNotificationsChannelsOverview } from "@shared/api";
import type { NotificationsChannelsOverview } from "@shared/types/notifications";
import { useNotificationsQuery } from "./useNotificationsQuery";

export type NotificationsChannelsFetchMode = 'initial' | 'refresh';

export type UseNotificationsChannelsOverviewResult = {
  overview: NotificationsChannelsOverview | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  reload: (mode?: NotificationsChannelsFetchMode) => Promise<void>;
};

const DEFAULT_ERROR_MESSAGE = 'Failed to load notification channels.';

export function useNotificationsChannelsOverview(
  autoFetch: boolean = true,
): UseNotificationsChannelsOverviewResult {
  const { data, loading, refreshing, error, reload } = useNotificationsQuery<NotificationsChannelsOverview>({
    fetcher: (signal) => fetchNotificationsChannelsOverview({ signal }),
    auto: autoFetch,
    mapError: (err) =>
      typeof (err as any)?.message === 'string' && (err as any).message.trim()
        ? (err as any).message.trim()
        : DEFAULT_ERROR_MESSAGE,
  });

  const reloadWithMode = React.useCallback(
    async (mode: NotificationsChannelsFetchMode = 'initial') => {
      await reload(mode);
    },
    [reload],
  );

  return {
    overview: data,
    loading,
    refreshing,
    error,
    reload: reloadWithMode,
  };
}

import * as React from 'react';

import {
  deleteFeatureFlag,
  fetchFeatureFlags,
  saveFeatureFlag,
  searchFeatureFlagUsers,
} from '@shared/api/management/flags';
import { extractErrorMessage } from '@shared/utils/errors';
import type {
  FeatureFlag,
  FeatureFlagTester,
  FeatureFlagUpsertPayload,
} from '@shared/types/management';

export type UseManagementFlagsOptions = {
  auto?: boolean;
};

export type UseManagementFlagsResult = {
  loading: boolean;
  error: string | null;
  items: FeatureFlag[];
  refresh: () => Promise<void>;
  clearError: () => void;
  saveFlag: (payload: FeatureFlagUpsertPayload) => Promise<void>;
  deleteFlag: (slug: string) => Promise<void>;
  searchTesters: (query: string, opts?: { limit?: number; signal?: AbortSignal }) => Promise<FeatureFlagTester[]>;
};

export function useManagementFlags(
  { auto = true }: UseManagementFlagsOptions = {},
): UseManagementFlagsResult {
  const [loading, setLoading] = React.useState<boolean>(auto);
  const [error, setError] = React.useState<string | null>(null);
  const [items, setItems] = React.useState<FeatureFlag[]>([]);

  const refresh = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const flags = await fetchFeatureFlags();
      setItems(Array.isArray(flags) ? flags : []);
    } catch (err) {
      setItems([]);
      setError(extractErrorMessage(err, 'Не удалось загрузить feature flags.'));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (!auto) return;
    void refresh();
  }, [auto, refresh]);

  const saveFlag = React.useCallback(
    async (payload: FeatureFlagUpsertPayload) => {
      try {
        await saveFeatureFlag(payload);
        await refresh();
      } catch (err) {
        setError(extractErrorMessage(err, 'Не удалось сохранить фичефлаг.'));
        throw err;
      }
    },
    [refresh],
  );

  const deleteFlagHandler = React.useCallback(
    async (slug: string) => {
      try {
        await deleteFeatureFlag(slug);
        await refresh();
      } catch (err) {
        setError(extractErrorMessage(err, 'Не удалось удалить фичефлаг.'));
        throw err;
      }
    },
    [refresh],
  );

  const searchTesters = React.useCallback(
    async (query: string, opts?: { limit?: number; signal?: AbortSignal }) => {
      try {
        return await searchFeatureFlagUsers(query, opts);
      } catch (err) {
        if ((err as Error)?.name === 'AbortError') {
          return [];
        }
        setError(extractErrorMessage(err, 'Не удалось выполнить поиск пользователей.'));
        return [];
      }
    },
    [],
  );

  const clearError = React.useCallback(() => setError(null), []);

  return {
    loading,
    error,
    items,
    refresh,
    clearError,
    saveFlag,
    deleteFlag: deleteFlagHandler,
    searchTesters,
  };
}
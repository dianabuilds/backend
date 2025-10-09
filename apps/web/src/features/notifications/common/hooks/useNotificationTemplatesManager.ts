
import React from 'react';

import {
  deleteNotificationTemplate,
  fetchNotificationTemplates,
  saveNotificationTemplate,
} from '@shared/api/notifications';
import type {
  NotificationTemplate,
  NotificationTemplatePayload,
} from '@shared/types/notifications';
import { useNotificationsQuery } from './useNotificationsQuery';

export type UseNotificationTemplatesManagerOptions = {
  auto?: boolean;
};

export type UseNotificationTemplatesManagerResult = {
  templates: NotificationTemplate[];
  loading: boolean;
  saving: boolean;
  deletingId: string | null;
  error: string | null;
  refresh: (mode?: 'initial' | 'refresh') => Promise<void>;
  saveTemplate: (payload: NotificationTemplatePayload) => Promise<void>;
  deleteTemplate: (id: string) => Promise<void>;
  clearError: () => void;
};

export function useNotificationTemplatesManager({
  auto = true,
}: UseNotificationTemplatesManagerOptions = {}): UseNotificationTemplatesManagerResult {
  const {
    data,
    loading,
    refreshing,
    error: queryError,
    reload,
    setError: setQueryError,
  } = useNotificationsQuery<NotificationTemplate[]>({
    fetcher: (signal) => fetchNotificationTemplates({ signal }),
    auto,
  });

  const [saving, setSaving] = React.useState(false);
  const [deletingId, setDeletingId] = React.useState<string | null>(null);
  const [mutationError, setMutationError] = React.useState<string | null>(null);

  const clearError = React.useCallback(() => {
    setMutationError(null);
    setQueryError(null);
  }, [setQueryError]);

  const refresh = React.useCallback(
    async (mode: 'initial' | 'refresh' = 'initial') => {
      await reload(mode);
    },
    [reload],
  );

  const saveTemplate = React.useCallback(
    async (payload: NotificationTemplatePayload) => {
      clearError();
      setSaving(true);
      try {
        await saveNotificationTemplate(payload);
        await refresh('refresh');
      } catch (err: any) {
        const message = typeof err?.message === 'string' ? err.message : 'Failed to save template.';
        setMutationError(message);
        throw err;
      } finally {
        setSaving(false);
      }
    },
    [clearError, refresh],
  );

  const deleteTemplate = React.useCallback(
    async (id: string) => {
      const trimmed = id.trim();
      if (!trimmed) {
        setMutationError('Template id is missing.');
        return;
      }
      clearError();
      setDeletingId(trimmed);
      try {
        await deleteNotificationTemplate(trimmed);
        await refresh('refresh');
      } catch (err: any) {
        const message = typeof err?.message === 'string' ? err.message : 'Failed to delete template.';
        setMutationError(message);
        throw err;
      } finally {
        setDeletingId(null);
      }
    },
    [clearError, refresh],
  );

  return {
    templates: data ?? [],
    loading: loading || refreshing,
    saving,
    deletingId,
    error: mutationError ?? queryError,
    refresh: refresh,
    saveTemplate,
    deleteTemplate,
    clearError,
  };
}

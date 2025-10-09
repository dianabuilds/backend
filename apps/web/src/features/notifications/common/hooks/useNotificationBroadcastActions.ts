
import React from 'react';

import {
  cancelNotificationBroadcast,
  createNotificationBroadcast,
  sendNotificationBroadcastNow,
  updateNotificationBroadcast,
} from '@shared/api/notifications';
import { extractErrorMessage } from '@shared/utils/errors';

export type BroadcastBusyState = Record<string, 'send' | 'cancel'>;

export type NotificationBroadcastActionMessages = {
  create?: string;
  update?: string;
  sendNow?: string;
  cancel?: string;
};

export type UseNotificationBroadcastActionsOptions = {
  mapError?: (error: unknown, fallback: string) => string;
  messages?: NotificationBroadcastActionMessages;
};

export type UseNotificationBroadcastActionsResult = {
  saving: boolean;
  busy: BroadcastBusyState;
  error: string | null;
  createBroadcast: (
    payload: Parameters<typeof createNotificationBroadcast>[0],
    callbacks?: ActionCallbacks,
  ) => Promise<void>;
  updateBroadcast: (
    id: string,
    payload: Parameters<typeof updateNotificationBroadcast>[1],
    callbacks?: ActionCallbacks,
  ) => Promise<void>;
  sendNow: (id: string, callbacks?: ActionCallbacks) => Promise<void>;
  cancel: (id: string, callbacks?: ActionCallbacks) => Promise<void>;
  clearError: () => void;
};

type ActionCallbacks = {
  onSuccess?: () => void;
  onError?: (message: string) => void;
};

function resolveError(error: unknown, fallback: string, mapError?: (error: unknown, fallback: string) => string) {
  if (mapError) {
    return mapError(error, fallback);
  }
  return extractErrorMessage(error, fallback);
}

export function useNotificationBroadcastActions({
  mapError,
  messages,
}: UseNotificationBroadcastActionsOptions = {}): UseNotificationBroadcastActionsResult {
  const [saving, setSaving] = React.useState(false);
  const [busy, setBusy] = React.useState<BroadcastBusyState>({});
  const [error, setError] = React.useState<string | null>(null);

  const clearError = React.useCallback(() => {
    setError(null);
  }, []);

  const runWithErrorHandling = React.useCallback(
    async (
      action: () => Promise<void>,
      callbacks: ActionCallbacks | undefined,
      fallback: string,
    ) => {
      const onSuccess = callbacks?.onSuccess;
      const onErrorCallback = callbacks?.onError;
      try {
        await action();
        onSuccess?.();
      } catch (err) {
        const message = resolveError(err, fallback, mapError);
        if (!onErrorCallback) {
          setError(message);
        } else {
          onErrorCallback(message);
        }
        throw err;
      }
    },
    [mapError],
  );

  const createBroadcast = React.useCallback(
    async (
      payload: Parameters<typeof createNotificationBroadcast>[0],
      callbacks?: ActionCallbacks,
    ) => {
      setSaving(true);
      try {
        await runWithErrorHandling(
          () => createNotificationBroadcast(payload),
          callbacks,
          messages?.create ?? 'Failed to create broadcast.',
        );
      } finally {
        setSaving(false);
      }
    },
    [messages, runWithErrorHandling],
  );

  const updateBroadcast = React.useCallback(
    async (
      id: string,
      payload: Parameters<typeof updateNotificationBroadcast>[1],
      callbacks?: ActionCallbacks,
    ) => {
      setSaving(true);
      try {
        await runWithErrorHandling(
          () => updateNotificationBroadcast(id, payload),
          callbacks,
          messages?.update ?? 'Failed to update broadcast.',
        );
      } finally {
        setSaving(false);
      }
    },
    [messages, runWithErrorHandling],
  );

  const sendNow = React.useCallback(
    async (id: string, callbacks?: ActionCallbacks) => {
      setBusy((prev) => ({ ...prev, [id]: 'send' }));
      try {
        await runWithErrorHandling(
          () => sendNotificationBroadcastNow(id),
          callbacks,
          messages?.sendNow ?? 'Failed to queue immediate send.',
        );
      } finally {
        setBusy((prev) => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
      }
    },
    [messages, runWithErrorHandling],
  );

  const cancel = React.useCallback(
    async (id: string, callbacks?: ActionCallbacks) => {
      setBusy((prev) => ({ ...prev, [id]: 'cancel' }));
      try {
        await runWithErrorHandling(
          () => cancelNotificationBroadcast(id),
          callbacks,
          messages?.cancel ?? 'Failed to cancel broadcast.',
        );
      } finally {
        setBusy((prev) => {
          const next = { ...prev };
          delete next[id];
          return next;
        });
      }
    },
    [messages, runWithErrorHandling],
  );

  return {
    saving,
    busy,
    error,
    createBroadcast,
    updateBroadcast,
    sendNow,
    cancel,
    clearError,
  };
}

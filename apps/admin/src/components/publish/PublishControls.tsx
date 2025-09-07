import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { type HTMLAttributes, useMemo, useState } from 'react';

import { patchNode } from '../../api/nodes';
import {
  type AccessMode,
  cancelScheduledPublish,
  getPublishInfo,
  type PublishInfo,
  publishNow,
  schedulePublish,
} from '../../api/publish';
import { useToast } from '../ToastProvider';
import { Button, TextInput } from '../../shared/ui';

type Props = {
  accountId: string;
  nodeId: number;
  disabled?: boolean;
  onChanged?: () => void;
  className?: string;
};

function toLocalInputValue(iso?: string | null): string {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, '0');
  const yyyy = d.getFullYear();
  const mm = pad(d.getMonth() + 1);
  const dd = pad(d.getDate());
  const hh = pad(d.getHours());
  const mi = pad(d.getMinutes());
  return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
}

function toUTCISOFromLocal(localValue: string): string {
  // local datetime-local -> ISO UTC
  const local = new Date(localValue);
  return new Date(local.getTime() - local.getTimezoneOffset() * 60000).toISOString();
}

function Spinner(
  props: HTMLAttributes<HTMLSpanElement>,
) {
  return (
    <span
      {...props}
      className={`inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin ${
        props.className ?? ''
      }`}
    />
  );
}

export default function PublishControls({ accountId, nodeId, disabled, onChanged, className }: Props) {
  const { addToast } = useToast();
  const qc = useQueryClient();

  const { data, isLoading, refetch } = useQuery<PublishInfo>({
    queryKey: ['publish-info', accountId || 'default', nodeId],
    queryFn: () => getPublishInfo(accountId || '', nodeId),
    enabled: Number.isFinite(nodeId),
  });

  const [access, setAccess] = useState<AccessMode>('everyone');
  const [mode, setMode] = useState<'now' | 'schedule'>('now');
  const [when, setWhen] = useState<string>(() => {
    const d = new Date();
    d.setMinutes(d.getMinutes() + 30);
    return toLocalInputValue(d.toISOString());
  });

  const statusText = useMemo(() => {
    if (!data) return '';
    if (data.scheduled?.status === 'pending') {
      return `Запланировано на ${new Date(data.scheduled.run_at).toLocaleString()}`;
    }
    if (data.status === 'published') {
      const ts = data.published_at ? new Date(data.published_at).toLocaleString() : '';
      return `Опубликовано${ts ? ` • ${ts}` : ''}`;
    }
    return 'Черновик';
  }, [data]);

  const mPublish = useMutation({
    mutationFn: () => publishNow(accountId || '', nodeId, access),
    onSuccess: async () => {
      addToast({ title: 'Опубликовано', variant: 'success' });
      await qc.invalidateQueries({ queryKey: ['publish-info', accountId || 'default', nodeId] });
      onChanged?.();
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : String(e);
      addToast({ title: 'Ошибка публикации', description: msg, variant: 'error' });
    },
  });

  const mSchedule = useMutation({
    mutationFn: () => schedulePublish(accountId || '', nodeId, toUTCISOFromLocal(when), access),
    onSuccess: async () => {
      addToast({ title: 'Публикация запланирована', variant: 'success' });
      await qc.invalidateQueries({ queryKey: ['publish-info', accountId || 'default', nodeId] });
      onChanged?.();
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : String(e);
      addToast({ title: 'Не удалось запланировать', description: msg, variant: 'error' });
    },
  });

  const mCancel = useMutation({
    mutationFn: () => cancelScheduledPublish(accountId || '', nodeId),
    onSuccess: async () => {
      addToast({ title: 'Расписание отменено', variant: 'success' });
      await qc.invalidateQueries({ queryKey: ['publish-info', accountId || 'default', nodeId] });
      onChanged?.();
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : String(e);
      addToast({ title: 'Не удалось отменить', description: msg, variant: 'error' });
    },
  });

  const mUnpublish = useMutation({
    mutationFn: () => patchNode(accountId || '', nodeId, { isPublic: false }),
    onSuccess: async () => {
      addToast({ title: 'Снято с публикации', variant: 'success' });
      await qc.invalidateQueries({ queryKey: ['publish-info', accountId, nodeId] });
      onChanged?.();
    },
    onError: (e: unknown) => {
      const msg = e instanceof Error ? e.message : String(e);
      addToast({ title: 'Не удалось снять с публикации', description: msg, variant: 'error' });
    },
  });

  const scheduled = data?.scheduled?.status === 'pending';
  const isMutating =
    mPublish.isPending ||
    mSchedule.isPending ||
    mCancel.isPending ||
    mUnpublish.isPending;

  return (
    <div className={`space-y-4 ${className ?? ''}`.trim()}>
      <div className="flex items-center gap-2 text-sm text-gray-600">
        <span>Статус:</span>
        {isLoading || isMutating ? (
          <Spinner data-testid="status-spinner" className="text-gray-400" />
        ) : (
          <span className="font-medium">{statusText}</span>
        )}
        <button
          className="ml-auto text-xs underline text-blue-600"
          onClick={() => refetch()}
          disabled={isLoading || isMutating}
        >
          Обновить
        </button>
      </div>

      <div className="space-y-4 p-4 border rounded-md bg-gray-50">
        <div className="space-y-1">
          <label className="font-medium">Доступ</label>
          <select
            value={access}
            onChange={(e) => setAccess(e.target.value as AccessMode)}
            disabled={disabled}
            className="w-full border rounded px-2 py-1"
          >
            <option value="everyone">Всем</option>
            <option value="premium_only">Только премиум</option>
            <option value="early_access">Ранний доступ</option>
          </select>
        </div>

        <div className="space-y-1">
          <label className="font-medium">Режим</label>
          <div className="flex flex-col gap-1">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                checked={mode === 'now'}
                onChange={() => setMode('now')}
              />
              Опубликовать сейчас
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                checked={mode === 'schedule'}
                onChange={() => setMode('schedule')}
              />
              Запланировать
            </label>
            {mode === 'schedule' && (
              <TextInput
                type="datetime-local"
                value={when}
                onChange={(e) => setWhen(e.target.value)}
                className="w-full"
              />
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            className="bg-green-600 text-white disabled:opacity-50"
            onClick={() => (mode === 'now' ? mPublish.mutate() : mSchedule.mutate())}
            disabled={disabled || mPublish.isPending || mSchedule.isPending}
          >
            {mPublish.isPending || mSchedule.isPending ? (
              <Spinner data-testid="publish-spinner" className="text-white" />
            ) : mode === 'now' ? (
              'Опубликовать'
            ) : (
              'Запланировать'
            )}
          </Button>
          {scheduled && (
            <Button
              className="bg-gray-200 disabled:opacity-50"
              onClick={() => mCancel.mutate()}
              disabled={disabled || mCancel.isPending}
            >
              {mCancel.isPending ? (
                <Spinner
                  data-testid="cancel-spinner"
                  className="text-gray-600"
                />
              ) : (
                'Отменить расписание'
              )}
            </Button>
          )}
          {data?.status === 'published' && (
            <Button
              className="bg-red-600 text-white disabled:opacity-50"
              onClick={() => mUnpublish.mutate()}
              disabled={disabled || mUnpublish.isPending}
            >
              {mUnpublish.isPending ? (
                <Spinner
                  data-testid="unpublish-spinner"
                  className="text-white"
                />
              ) : (
                'Снять с публикации'
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

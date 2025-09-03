import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import {
  AccessMode,
  cancelScheduledPublish,
  getPublishInfo,
  publishNow,
  schedulePublish,
  type PublishInfo,
} from '../../api/publish';
import { patchNode } from '../../api/nodes';
import { useToast } from '../ToastProvider';

type Props = {
  workspaceId: string;
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

export default function PublishControls({ workspaceId, nodeId, disabled, onChanged, className }: Props) {
  const { addToast } = useToast();
  const qc = useQueryClient();

  const { data, isLoading, refetch } = useQuery<PublishInfo>({
    queryKey: ['publish-info', workspaceId, nodeId],
    queryFn: () => getPublishInfo(workspaceId, nodeId),
    enabled: !!workspaceId && Number.isFinite(nodeId),
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
    mutationFn: () => publishNow(workspaceId, nodeId, access),
    onSuccess: async () => {
      addToast({ title: 'Опубликовано', variant: 'success' });
      await qc.invalidateQueries({ queryKey: ['publish-info', workspaceId, nodeId] });
      onChanged?.();
    },
    onError: (e: any) => {
      addToast({ title: 'Ошибка публикации', description: String(e?.message || e), variant: 'error' });
    },
  });

  const mSchedule = useMutation({
    mutationFn: () => schedulePublish(workspaceId, nodeId, toUTCISOFromLocal(when), access),
    onSuccess: async () => {
      addToast({ title: 'Публикация запланирована', variant: 'success' });
      await qc.invalidateQueries({ queryKey: ['publish-info', workspaceId, nodeId] });
      onChanged?.();
    },
    onError: (e: any) => {
      addToast({ title: 'Не удалось запланировать', description: String(e?.message || e), variant: 'error' });
    },
  });

  const mCancel = useMutation({
    mutationFn: () => cancelScheduledPublish(workspaceId, nodeId),
    onSuccess: async () => {
      addToast({ title: 'Расписание отменено', variant: 'success' });
      await qc.invalidateQueries({ queryKey: ['publish-info', workspaceId, nodeId] });
      onChanged?.();
    },
    onError: (e: any) => {
      addToast({ title: 'Не удалось отменить', description: String(e?.message || e), variant: 'error' });
    },
  });

  const mUnpublish = useMutation({
    mutationFn: () => patchNode(workspaceId, nodeId, { isPublic: false }),
    onSuccess: async () => {
      addToast({ title: 'Снято с публикации', variant: 'success' });
      await qc.invalidateQueries({ queryKey: ['publish-info', workspaceId, nodeId] });
      onChanged?.();
    },
    onError: (e: any) => {
      addToast({ title: 'Не удалось снять с публикации', description: String(e?.message || e), variant: 'error' });
    },
  });

  const scheduled = data?.scheduled?.status === 'pending';

  return (
    <div className={className}>
      <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
        <span>Статус:</span>
        <span className="font-medium">{isLoading ? 'Загрузка…' : statusText}</span>
        <button
          className="ml-auto text-xs underline text-blue-600"
          onClick={() => refetch()}
          disabled={isLoading}
        >
          Обновить
        </button>
      </div>

      <div className="flex flex-col gap-3 p-3 border rounded-md">
        <div className="flex flex-wrap items-center gap-3">
          <label className="font-medium">Доступ:</label>
          <select
            value={access}
            onChange={(e) => setAccess(e.target.value as AccessMode)}
            disabled={disabled}
            className="border rounded px-2 py-1"
          >
            <option value="everyone">Всем</option>
            <option value="premium_only">Только премиум</option>
            <option value="early_access">Ранний доступ</option>
          </select>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <label className="font-medium">Режим:</label>
          <label className="flex items-center gap-1">
            <input
              type="radio"
              checked={mode === 'now'}
              onChange={() => setMode('now')}
            />
            Опубликовать сейчас
          </label>
          <label className="flex items-center gap-1">
            <input
              type="radio"
              checked={mode === 'schedule'}
              onChange={() => setMode('schedule')}
            />
            Запланировать
          </label>
          {mode === 'schedule' && (
            <input
              type="datetime-local"
              value={when}
              onChange={(e) => setWhen(e.target.value)}
              className="border rounded px-2 py-1"
            />
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            className="px-3 py-1 rounded bg-green-600 text-white disabled:opacity-50"
            onClick={() => (mode === 'now' ? mPublish.mutate() : mSchedule.mutate())}
            disabled={disabled || mPublish.isPending || mSchedule.isPending}
          >
            {mode === 'now' ? 'Опубликовать' : 'Запланировать'}
          </button>
          {scheduled && (
            <button
              className="px-3 py-1 rounded bg-gray-200 disabled:opacity-50"
              onClick={() => mCancel.mutate()}
              disabled={disabled || mCancel.isPending}
            >
              Отменить расписание
            </button>
          )}
          {data?.status === 'published' && (
            <button
              className="px-3 py-1 rounded bg-red-600 text-white disabled:opacity-50"
              onClick={() => mUnpublish.mutate()}
              disabled={disabled || mUnpublish.isPending}
            >
              Снять с публикации
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { Badge, Card } from '@ui';
import type { SiteBlock } from '@shared/types/management';
import { formatDateTime } from '@shared/utils/format';

const SYNC_STATE_META: Record<
  string,
  {
    label: string;
    color: 'success' | 'warning' | 'neutral';
  }
> = {
  synced: { label: 'Синхронизирован', color: 'success' },
  has_updates: { label: 'Доступны обновления', color: 'warning' },
  detached: { label: 'Ручной режим', color: 'neutral' },
};

type Props = {
  block: SiteBlock;
};

export function SiteBlockLibrarySourceCard({ block }: Props): React.ReactElement | null {
  const source = block.library_source;
  if (!source) {
    return null;
  }
  const syncMeta = SYNC_STATE_META[source.sync_state ?? 'synced'] ?? SYNC_STATE_META.synced;
  return (
    <Card className="flex h-full flex-col gap-3 border border-gray-200/80 bg-white/95 p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-400">Источник</div>
          <div className="text-base font-semibold text-gray-900">{source.key}</div>
        </div>
        <Badge color={syncMeta.color} variant="soft">
          {syncMeta.label}
        </Badge>
      </div>
      <dl className="space-y-2 text-sm text-gray-600">
        <div className="flex items-center justify-between gap-2">
          <dt className="text-gray-500">Секция</dt>
          <dd className="font-medium text-gray-800">{source.section || block.section}</dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="text-gray-500">Локаль</dt>
          <dd className="font-medium text-gray-800">{source.locale ?? block.default_locale ?? '—'}</dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="text-gray-500">Обновлён</dt>
          <dd className="font-medium text-gray-800">
            {source.updated_at ? formatDateTime(source.updated_at) : '—'}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-2">
          <dt className="text-gray-500">Автор</dt>
          <dd className="truncate font-medium text-gray-800">{source.updated_by ?? '—'}</dd>
        </div>
      </dl>
    </Card>
  );
}

export default SiteBlockLibrarySourceCard;

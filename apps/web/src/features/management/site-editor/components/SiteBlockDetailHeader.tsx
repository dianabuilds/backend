import React from 'react';
import { Badge, Button } from '@ui';
import { formatDateTime } from '@shared/utils/format';
import type { SiteBlock } from '@shared/types/management';
import { SCOPE_LABELS, STATUS_META, REVIEW_STATUS_META } from './SiteBlockLibraryPage.constants';

type HeaderProps = {
  block: SiteBlock;
  loading: boolean;
  onRefresh: () => void;
  onPublish: () => void;
  onSave: () => void;
  saving: boolean;
  publishing: boolean;
  publishDisabled: boolean;
  saveDisabled: boolean;
  onArchive?: () => void;
  archiveDisabled?: boolean;
  archiveLabel?: string;
  archiveColor?: 'primary' | 'neutral' | 'error';
};

function InfoPill({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}): React.ReactElement {
  return (
    <div className="min-w-[120px] space-y-1 rounded-xl border border-gray-200/80 bg-white/60 px-3 py-2 shadow-xs">
      <div className="text-2xs font-semibold uppercase tracking-wide text-gray-400">{label}</div>
      <div className="text-xs font-medium text-gray-800">{value}</div>
    </div>
  );
}

export function SiteBlockDetailHeader({
  block,
  loading,
  onRefresh,
  onPublish,
  onSave,
  saving,
  publishing,
  publishDisabled,
  saveDisabled,
  onArchive,
  archiveDisabled,
  archiveLabel,
  archiveColor = 'error',
}: HeaderProps): React.ReactElement {
  const statusMeta = STATUS_META[block.status] ?? STATUS_META.draft;
  const reviewMeta = REVIEW_STATUS_META[block.review_status ?? 'none'] ?? REVIEW_STATUS_META.none;

  return (
    <div className="flex flex-wrap items-start justify-between gap-4 rounded-2xl border border-gray-200/80 bg-white/95 px-4 py-3 shadow-sm">
      <div className="flex flex-1 flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Badge color={statusMeta.color} variant="soft">
            {statusMeta.label}
          </Badge>
          <Badge color={reviewMeta.color} variant="outline">
            {reviewMeta.label}
          </Badge>
          {block.requires_publisher ? (
            <Badge color="warning" variant="outline">
              Требует publisher
            </Badge>
          ) : null}
          <span className="text-xs text-gray-400">
            {SCOPE_LABELS[block.scope ?? 'unknown'] ?? block.scope ?? '—'}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-2xl font-semibold text-gray-900">{block.title || 'Без названия'}</h2>
          {block.key ? (
            <span className="rounded-md border border-gray-200 bg-gray-50 px-2 py-1 font-mono text-xs text-gray-500">
              {block.key}
            </span>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          <InfoPill label="Текущая версия" value={`v${block.draft_version ?? block.version ?? '—'}`} />
          <InfoPill label="Опубликовано" value={`v${block.published_version ?? '—'}`} />
          <InfoPill
            label="Обновил"
            value={
              block.updated_by ? (
                <span className="font-medium">{block.updated_by}</span>
              ) : (
                <span className="text-gray-400">—</span>
              )
            }
          />
          <InfoPill
            label="Изменён"
            value={block.updated_at ? formatDateTime(block.updated_at) : <span className="text-gray-400">—</span>}
          />
        </div>
      </div>
      <div className="flex flex-col items-end gap-2">
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            color="neutral"
            onClick={onRefresh}
            disabled={loading || saving || publishing}
          >
            Обновить
          </Button>
          {onArchive ? (
            <Button
              size="sm"
              variant="ghost"
              color={archiveColor}
              onClick={onArchive}
              disabled={archiveDisabled || saving || publishing}
            >
              {archiveLabel ?? 'В архив'}
            </Button>
          ) : null}
          <Button size="sm" variant="filled" color="neutral" onClick={onSave} disabled={saveDisabled || saving || publishing}>
            {saving ? 'Сохраняем…' : 'Сохранить'}
          </Button>
          <Button
            size="sm"
            variant="filled"
            color="primary"
            onClick={onPublish}
            disabled={publishDisabled || saving || publishing}
          >
            {publishing ? 'Публикуем…' : 'Опубликовать'}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default SiteBlockDetailHeader;

import React from 'react';
import clsx from 'clsx';
import { Badge } from '@ui';
import { formatDateTime } from '@shared/utils/format';
import type { SiteBlock } from '@shared/types/management';
import {
  REVIEW_STATUS_META,
  STATUS_META,
  STATUS_ORDER,
} from './SiteBlockLibraryPage.constants';
import { formatScope } from '../utils/blockHelpers';
import { collectLocales, pickOwner } from './SiteBlockLibrary.utils';

type Props = {
  block: SiteBlock;
  selected: boolean;
  onSelect: (block: SiteBlock) => void;
};

export function SiteBlockListItem({ block, selected, onSelect }: Props): React.ReactElement {
  const statusMeta = STATUS_META[block.status];
  const reviewMeta = REVIEW_STATUS_META[block.review_status];
  const owner = pickOwner(block);
  const updatedAt = formatDateTime(block.updated_at, { fallback: '—' });
  const scopeLabel = formatScope(block.scope);
  const locales = collectLocales(block).join(', ') || '—';

  return (
    <button
      type="button"
      onClick={() => onSelect(block)}
      className={clsx(
        'w-full rounded-2xl border px-3 py-3 text-left transition focus:outline-none focus:ring-2 focus:ring-primary-400',
        selected
          ? 'border-primary-400 bg-primary-50/80 dark:border-primary-400/60 dark:bg-primary-900/30'
          : 'border-gray-200 bg-white hover:border-primary-300 dark:border-dark-600 dark:bg-dark-800/70 hover:dark:border-primary-400',
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-400">
            {block.section || 'Без секции'}
          </div>
          <div className="text-sm font-semibold text-gray-900 dark:text-white">{block.title}</div>
          <div className="font-mono text-[11px] text-gray-500 dark:text-dark-200">{block.key}</div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge color={statusMeta.color} variant="soft">
            {statusMeta.label}
          </Badge>
          <Badge color="neutral" variant="outline">
            {scopeLabel}
          </Badge>
          {block.review_status !== 'none' ? (
            <Badge color={reviewMeta.color} variant="soft">
              {reviewMeta.label}
            </Badge>
          ) : null}
          {block.requires_publisher ? (
            <Badge color="warning" variant="outline">
              Publisher
            </Badge>
          ) : null}
          {block.is_template ? (
            <Badge color="neutral" variant="soft">
              Шаблон
            </Badge>
          ) : null}
        </div>
      </div>
      <div className="mt-2 grid gap-2 text-[11px] text-gray-500 dark:text-dark-200 sm:grid-cols-2">
        <div>Локали: {locales}</div>
        <div>Обновлён: {updatedAt}</div>
        <div>Ответственный: {owner ?? '—'}</div>
        <div>Использований: {typeof block.usage_count === 'number' ? block.usage_count : '—'}</div>
      </div>
    </button>
  );
}

export function sortBlocksForList(left: SiteBlock, right: SiteBlock): number {
  const statusDiff = STATUS_ORDER[left.status] - STATUS_ORDER[right.status];
  if (statusDiff !== 0) {
    return statusDiff;
  }
  const titleDiff = left.title.localeCompare(right.title, 'ru');
  if (titleDiff !== 0) {
    return titleDiff;
  }
  return (right.updated_at ?? '').localeCompare(left.updated_at ?? '');
}

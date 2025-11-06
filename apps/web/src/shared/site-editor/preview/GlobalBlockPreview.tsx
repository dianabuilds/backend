import React from 'react';
import type { SiteBlockPreviewItem } from '@shared/api/management/siteEditor/types';
import { formatDateTime, formatNumber } from '@shared/utils/format';

type PreviewMetaItemProps = {
  label: string;
  value: React.ReactNode;
};

function PreviewMetaItem({ label, value }: PreviewMetaItemProps): React.ReactElement {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-dark-300">{label}</span>
      <span className="text-xs font-medium text-gray-700 dark:text-dark-50">{value}</span>
    </div>
  );
}

export type GlobalBlockPreviewProps = {
  items?: SiteBlockPreviewItem[] | null;
  source?: string | null;
  fetchedAt?: string | null;
  emptyMessage?: string;
};

const DEFAULT_EMPTY_MESSAGE = 'Предпросмотр пуст. Проверьте источники данных или обновите конфигурацию.';

export function GlobalBlockPreview({
  items,
  source,
  fetchedAt,
  emptyMessage = DEFAULT_EMPTY_MESSAGE,
}: GlobalBlockPreviewProps): React.ReactElement {
  const hasItems = Boolean(items && items.length);
  const timestamp = fetchedAt ?? null;

  return (
    <div className="space-y-3">
      <div className="text-xs text-gray-500 dark:text-dark-200">
        Источник: {source || '—'} · Получено{' '}
        {formatDateTime(timestamp, {
          fallback: '—',
          withSeconds: true,
        })}
      </div>

      {hasItems ? (
        <ul className="space-y-2">
          {items!.map((item, index) => (
            <li
              key={`${item.id ?? index}-${item.href ?? index}`}
              className="rounded-xl border border-gray-200 p-3 text-xs text-gray-600 dark:border-dark-600 dark:text-dark-200"
            >
              <div className="text-sm font-semibold text-gray-900 dark:text-white">{item.title || 'Без названия'}</div>
              {item.subtitle ? (
                <div className="text-xs text-gray-500 dark:text-dark-300">{item.subtitle}</div>
              ) : null}
              {item.href ? (
                <div className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-dark-300">{item.href}</div>
              ) : null}
              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                <PreviewMetaItem label="Поставщик" value={item.provider || '—'} />
                <PreviewMetaItem
                  label="Счёт"
                  value={formatNumber(item.score ?? null, {
                    defaultValue: '—',
                    maximumFractionDigits: 2,
                  })}
                />
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <div className="rounded-xl border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-300">
          {emptyMessage}
        </div>
      )}
    </div>
  );
}

import React from 'react';
import { Badge, Card } from '@ui';
import type { SiteBlock } from '@shared/types/management';

const STATUS_META: Record<
  string,
  {
    label: string;
    color: 'success' | 'warning' | 'neutral';
  }
> = {
  ready: { label: 'Заполнено', color: 'success' },
  missing: { label: 'Не заполнено', color: 'warning' },
  not_required: { label: 'Не требуется', color: 'neutral' },
  unknown: { label: 'Не определено', color: 'neutral' },
};

type Props = {
  block: SiteBlock;
};

export function SiteBlockLocaleStatusCard({ block }: Props): React.ReactElement {
  const statuses =
    block.locale_statuses && block.locale_statuses.length
      ? block.locale_statuses
      : (block.available_locales ?? []).map((locale) => ({
          locale,
          required: locale === block.default_locale,
          status: 'unknown',
        }));

  return (
    <Card className="h-full space-y-3 border border-gray-200/80 bg-white/95 p-4 shadow-sm">
      <div>
        <div className="text-xs font-semibold uppercase tracking-wide text-gray-400">Локализация</div>
        <p className="text-sm text-gray-600">Отслеживаем готовность обязательных языков блока.</p>
      </div>
      <div className="space-y-2">
        {statuses.map((entry) => {
          const meta = STATUS_META[entry.status] ?? STATUS_META.unknown;
          return (
            <div key={`${entry.locale}-${entry.status}`} className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-gray-900">{entry.locale.toUpperCase()}</div>
                <div className="text-xs text-gray-500">
                  {entry.required ? 'Обязательная локаль' : 'Дополнительная локаль'}
                </div>
              </div>
              <Badge color={meta.color} variant="soft">
                {meta.label}
              </Badge>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

export default SiteBlockLocaleStatusCard;

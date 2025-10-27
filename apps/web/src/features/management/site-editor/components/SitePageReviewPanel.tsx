import React from 'react';
import { Badge, Button, Select } from '@ui';
import type { SitePageReviewStatus } from '@shared/types/management';

type SitePageReviewPanelProps = {
  status: SitePageReviewStatus;
  statusLabel: string;
  badgeColor: 'neutral' | 'warning' | 'success' | 'error';
  message: string;
  hint: string;
  options: Array<{ value: SitePageReviewStatus; label: string }>;
  disabled: boolean;
  showSelfPublishBadge: boolean;
  onChange: (status: SitePageReviewStatus) => void;
};

export function SitePageReviewPanel({
  status,
  statusLabel,
  badgeColor,
  message,
  hint,
  options,
  disabled,
  showSelfPublishBadge,
  onChange,
}: SitePageReviewPanelProps): React.ReactElement {
  const handleQuickSet = React.useCallback(() => {
    if (!disabled) {
      onChange('pending');
    }
  }, [disabled, onChange]);

  return (
    <details className="group rounded-2xl border border-gray-200/70 bg-white/95 text-gray-900 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/80 dark:text-dark-50 [&_summary::-webkit-details-marker]:hidden">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold">
        <span>Статус ревью</span>
        <div className="flex items-center gap-2 text-xs">
          <Badge color={badgeColor}>{statusLabel}</Badge>
          <span className="text-primary-500 group-open:hidden">Развернуть</span>
          <span className="hidden text-primary-500 group-open:block">Свернуть</span>
        </div>
      </summary>

      <div className="space-y-3 border-t border-gray-100 px-4 py-4 dark:border-dark-700/60">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            {showSelfPublishBadge ? (
              <Badge variant="outline" color="success">Самопубликация</Badge>
            ) : null}
            <p className="text-xs leading-5 text-gray-600 dark:text-dark-100">{message}</p>
          </div>
          {showSelfPublishBadge ? (
            <Button
              size="xs"
              variant="ghost"
              onClick={handleQuickSet}
              disabled={disabled}
              className="whitespace-nowrap"
            >
              Отправить на ревью
            </Button>
          ) : null}
        </div>

        <label className="space-y-1">
          <span className="text-xs font-medium text-gray-600 dark:text-dark-200">Выбрать статус</span>
          <Select
            value={status}
            onChange={(event) => onChange(event.target.value as SitePageReviewStatus)}
            disabled={disabled}
            className="w-full text-sm"
          >
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </label>
        <p className="text-[11px] text-gray-400 dark:text-dark-300">{hint}</p>
      </div>
    </details>
  );
}

export default SitePageReviewPanel;

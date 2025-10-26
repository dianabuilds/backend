import React from 'react';
import { Badge, Button, Card, Spinner } from '@ui';
import { formatDateTime } from '@shared/utils/format';
import type { SitePagePreviewResponse } from '@shared/types/management';

type SitePagePreviewPanelProps = {
  preview: SitePagePreviewResponse | null;
  previewLayout: string;
  previewLayouts: string[];
  onSelectLayout: (layout: string) => void;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
};

function getBlocksCount(preview: SitePagePreviewResponse | null, layout: string): number {
  const layoutData = preview?.layouts?.[layout];
  const blocks = (layoutData?.data as { blocks?: unknown[] } | undefined)?.blocks;
  return Array.isArray(blocks) ? blocks.length : 0;
}

export function SitePagePreviewPanel({
  preview,
  previewLayout,
  previewLayouts,
  onSelectLayout,
  loading,
  error,
  onRefresh,
}: SitePagePreviewPanelProps): React.ReactElement {
  const selectedLayout = preview ? preview.layouts[previewLayout] : null;
  const meta = selectedLayout?.meta as Record<string, unknown> | undefined;
  const layoutOptions = previewLayouts.length ? previewLayouts : ['desktop', 'mobile'];

  return (
    <Card padding="md" className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Предпросмотр</h3>
          <p className="text-xs text-gray-500 dark:text-dark-200">
            Генерация payload для предпросмотра с учётом текущего черновика.
          </p>
        </div>
        <Button size="xs" variant="ghost" onClick={onRefresh} disabled={loading}>
          Обновить
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {layoutOptions.map((layout) => {
          const isActive = layout === previewLayout;
          return (
            <Button
              key={layout}
              size="xs"
              variant={isActive ? 'filled' : 'outlined'}
              color={isActive ? 'primary' : 'neutral'}
              onClick={() => onSelectLayout(layout)}
            >
              {layout}
            </Button>
          );
        })}
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
          <Spinner size="sm" />
          Формируем предпросмотр…
        </div>
      ) : null}

      {error ? (
        <div className="rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-600/60 dark:bg-rose-950/40 dark:text-rose-200">
          {error}
        </div>
      ) : null}

      {preview ? (
        <div className="space-y-2 rounded-md border border-gray-200/70 bg-white/80 px-3 py-2 text-[11px] text-gray-600 dark:border-dark-600/60 dark:bg-dark-800/70 dark:text-dark-200">
          <div className="flex flex-wrap items-center gap-2">
            <Badge color="neutral">
              Черновик v{preview.draft_version}
            </Badge>
            <span>·</span>
            <span>Публикация {preview.published_version ?? '—'}</span>
            {preview.version_mismatch ? (
              <span className="text-rose-600 dark:text-rose-300">
                (открыт другой черновик, обновите данные)
              </span>
            ) : null}
          </div>
          {selectedLayout ? (
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-gray-700 dark:text-dark-100">
                  Макет {selectedLayout.layout}
                </span>
                {selectedLayout.generated_at ? (
                  <span>
                    {formatDateTime(selectedLayout.generated_at, { withSeconds: true, fallback: '—' })}
                  </span>
                ) : null}
              </div>
              <div className="text-xs text-gray-500 dark:text-dark-200">
                Блоков: {getBlocksCount(preview, previewLayout)}
              </div>
              {meta ? (
                <div className="text-xs text-gray-500 dark:text-dark-200">
                  Title: {(meta?.title as string | undefined) ?? '—'}
                </div>
              ) : null}
            </div>
          ) : (
            <div className="text-xs text-gray-500 dark:text-dark-200">
              Макет пока не сформирован. Нажмите &laquo;Обновить&raquo;.
            </div>
          )}
        </div>
      ) : (
        <div className="rounded-md border border-gray-200/70 bg-gray-50 px-3 py-2 text-xs text-gray-500 dark:border-dark-600/60 dark:bg-dark-800/60 dark:text-dark-200">
          Предпросмотр ещё не запрашивался.
        </div>
      )}
    </Card>
  );
}

export default SitePagePreviewPanel;

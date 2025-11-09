import React from 'react';
import { Link } from 'react-router-dom';
import { Badge, Button, Card } from '@ui';
import { ExternalLink } from '@icons';
import { formatDateTime } from '@shared/utils/format';
import { STATUS_META } from '../../site-editor/components/SiteBlockLibraryPage.constants';
import { useHomeEditorContext } from '../HomeEditorContext';
import type { HomeBlock } from '../types';
import { getBlockDefinition } from '../blockDefinitions';
import { BlockSettingsForm } from './BlockSettingsForm';

export function BlockInspector(): React.ReactElement {
  const { data, selectedBlockId, setData, validation } = useHomeEditorContext();
  const block = React.useMemo(
    () => data.blocks.find((item) => item.id === selectedBlockId) ?? null,
    [data.blocks, selectedBlockId],
  );
  const blockErrors = React.useMemo(
    () => (block ? validation.blocks[block.id] ?? [] : []),
    [block, validation.blocks],
  );

  const updateBlock = React.useCallback(
    (updater: (current: HomeBlock) => HomeBlock) => {
      if (!block) return;
      setData((prev) => ({
        ...prev,
        blocks: prev.blocks.map((item) => (item.id === block.id ? updater(item) : item)),
      }));
    },
    [block, setData],
  );

  if (!block) {
    return (
      <Card padding="sm" className="min-h-[160px]">
        <div className="flex flex-col items-center justify-center gap-2 text-center text-sm text-gray-500 dark:text-dark-200">
          <p>Выберите блок на канвасе, чтобы посмотреть его параметры.</p>
        </div>
      </Card>
    );
  }

  const definition = getBlockDefinition(block.type);
  const usesLibrary = block.source === 'site' && Boolean(block.siteBlockKey);
  const libraryStatusMeta =
    usesLibrary &&
    block.siteBlockStatus &&
    (block.siteBlockStatus === 'draft' || block.siteBlockStatus === 'published' || block.siteBlockStatus === 'archived')
      ? STATUS_META[block.siteBlockStatus]
      : null;
  const libraryLocale = block.siteBlockLocale ?? '—';
  const librarySection = block.siteBlockSection ?? block.type;
  const libraryLink = usesLibrary && block.siteBlockId ? `/management/site-editor/blocks/${block.siteBlockId}` : null;
  const libraryUpdatedAt = block.siteBlockUpdatedAt ? formatDateTime(block.siteBlockUpdatedAt, { fallback: '—' }) : '—';

  return (
    <Card
      padding="sm"
      className="space-y-4 border border-gray-200/70 bg-white/95 shadow-sm dark:border-dark-600/60 dark:bg-dark-800/80"
    >
      <div className="space-y-3">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-300">Блок на странице</p>
            <h3 className="text-base font-semibold text-gray-900 dark:text-dark-50">
              {block.title || definition?.label || block.type}
            </h3>
          </div>
          <Badge variant="outline" color="neutral">
            {definition?.label ?? block.type}
          </Badge>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 dark:text-dark-300">
          <span>
            ID · <span className="font-mono text-gray-800 dark:text-dark-100">{block.id}</span>
          </span>
          <span>
            Статус ·{' '}
            <span className="font-medium text-gray-900 dark:text-dark-50">
              {block.enabled ? 'активен' : 'отключён'}
            </span>
          </span>
          {usesLibrary && block.siteBlockStatus ? (
            <span className="inline-flex items-center gap-1">
              <span className="text-gray-400">Источник</span>
              <Badge color="primary" variant="soft">
                Библиотека
              </Badge>
              {libraryStatusMeta ? (
                <Badge color={libraryStatusMeta.color} variant="outline">
                  {libraryStatusMeta.label}
                </Badge>
              ) : null}
            </span>
          ) : null}
        </div>
        {usesLibrary ? (
          <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-primary-100/70 bg-primary-50/40 px-3 py-2 text-xs text-gray-700">
            <span className="font-mono text-sm text-gray-900">{block.siteBlockKey ?? '—'}</span>
            <span className="text-gray-500">
              {librarySection} · {libraryLocale.toUpperCase()}
            </span>
            <span className="text-gray-500">
              Обновлён {libraryUpdatedAt}
              {block.siteBlockUpdatedBy ? ` · ${block.siteBlockUpdatedBy}` : ''}
            </span>
            {block.siteBlockRequiresPublisher ? (
              <Badge color="warning" variant="outline">
                Требуется publisher
              </Badge>
            ) : null}
            {libraryLink ? (
              <Button
                as={Link}
                to={libraryLink}
                size="xs"
                variant="ghost"
                className="inline-flex items-center gap-1"
              >
                <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                Открыть блок
              </Button>
            ) : null}
          </div>
        ) : null}
        {blockErrors.length ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-500/30 dark:bg-amber-900/30 dark:text-amber-200">
            <div className="font-semibold">Ошибки настройки:</div>
            <ul className="mt-1 list-disc space-y-1 pl-4">
              {blockErrors.map((error, index) => (
                <li key={`${error.path}-${index}`}>{error.message}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>

      <div className="rounded-3xl border border-gray-100/70 bg-white/90 p-4 shadow-inner dark:border-dark-600/40 dark:bg-dark-900/60">
        <BlockSettingsForm block={block} onChange={updateBlock} errors={blockErrors} />
      </div>
    </Card>
  );
}

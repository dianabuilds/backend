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
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">
            {block.title || definition?.label || block.type}
          </h3>
          <Badge variant="outline" color="neutral">
            {definition?.label ?? block.type}
          </Badge>
        </div>
        <p className="text-xs text-gray-500 dark:text-dark-300">
          ID блока: <span className="font-mono text-gray-700 dark:text-dark-100">{block.id}</span>
        </p>
        <p className="text-xs text-gray-500 dark:text-dark-300">
          Состояние: {block.enabled ? 'активен и будет показан на главной' : 'отключен и скрыт из публикации'}.
        </p>
        {usesLibrary ? (
          <div className="space-y-3 rounded-2xl border border-primary-100 bg-primary-50/40 p-3 text-sm text-gray-700">
            <div className="flex flex-wrap items-center gap-2">
              <Badge color="primary" variant="soft">
                Библиотека
              </Badge>
              {libraryStatusMeta ? (
                <Badge color={libraryStatusMeta.color} variant="soft">
                  {libraryStatusMeta.label}
                </Badge>
              ) : null}
              {block.siteBlockRequiresPublisher ? (
                <Badge color="warning" variant="outline">
                  Требуется publisher
                </Badge>
              ) : null}
            </div>
            <dl className="grid gap-1 text-xs text-gray-600">
              <div className="flex items-center gap-1">
                <dt className="text-gray-500">Ключ:</dt>
                <dd className="font-mono text-gray-800">{block.siteBlockKey}</dd>
              </div>
              <div className="flex items-center gap-1">
                <dt className="text-gray-500">Секция:</dt>
                <dd className="font-medium text-gray-800">{librarySection}</dd>
              </div>
              <div className="flex items-center gap-1">
                <dt className="text-gray-500">Локаль:</dt>
                <dd className="font-medium text-gray-800 uppercase">{libraryLocale}</dd>
              </div>
              <div className="flex items-center gap-1">
                <dt className="text-gray-500">Обновлён:</dt>
                <dd className="font-medium text-gray-800">
                  {libraryUpdatedAt}
                  {block.siteBlockUpdatedBy ? ` · ${block.siteBlockUpdatedBy}` : ''}
                </dd>
              </div>
            </dl>
            {libraryLink ? (
              <Button
                as={Link}
                to={libraryLink}
                size="sm"
                variant="ghost"
                className="inline-flex items-center gap-1.5"
              >
                <ExternalLink className="h-4 w-4" aria-hidden="true" />
                <span>Открыть блок</span>
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

import React from 'react';
import { Badge, Card } from '@ui';
import { useHomeEditorContext } from '../HomeEditorContext';
import type { HomeBlock } from '../types';
import { getBlockDefinition } from '../blockDefinitions';
import { BlockSettingsForm } from './BlockSettingsForm';

export function BlockInspector(): React.ReactElement {
  const { data, selectedBlockId, setData, validation } = useHomeEditorContext();
  const block = React.useMemo(() => data.blocks.find((item) => item.id === selectedBlockId) ?? null, [data.blocks, selectedBlockId]);
  const blockErrors = React.useMemo(() => (block ? validation.blocks[block.id] ?? [] : []), [block, validation.blocks]);

  const updateBlock = React.useCallback((updater: (current: HomeBlock) => HomeBlock) => {
    if (!block) return;
    setData((prev) => ({
      ...prev,
      blocks: prev.blocks.map((item) => (item.id === block.id ? updater(item) : item)),
    }));
  }, [block, setData]);

  if (!block) {
    return (
      <Card padding="sm" className="h-full">
        <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-sm text-gray-500">
          <p>Выберите блок на канвасе, чтобы посмотреть его параметры.</p>
        </div>
      </Card>
    );
  }

  const definition = getBlockDefinition(block.type);

  return (
    <Card padding="sm" className="h-full space-y-4">
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-gray-900">{block.title || definition?.label || block.type}</h3>
          <Badge variant="outline" color="neutral">{definition?.label ?? block.type}</Badge>
        </div>
        <p className="text-xs text-gray-500">ID блока: <span className="font-mono">{block.id}</span></p>
        <p className="text-xs text-gray-500">
          Состояние: {block.enabled ? 'активен и будет показан на главной' : 'отключен и скрыт из публикации'}.
        </p>
        {blockErrors.length ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
            <div className="font-semibold">Ошибки настройки:</div>
            <ul className="mt-1 list-disc space-y-1 pl-4">
              {blockErrors.map((error, index) => (
                <li key={`${error.path}-${index}`}>{error.message}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>

      <BlockSettingsForm block={block} onChange={updateBlock} errors={blockErrors} />
    </Card>
  );
}
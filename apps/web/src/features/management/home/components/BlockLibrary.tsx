import React from 'react';
import { Card, Button } from '@ui';
import { Plus } from '@icons';
import { useHomeEditorContext } from '../HomeEditorContext';
import { createBlockInstance, listBlockDefinitions } from '../blockDefinitions';

const BLOCK_DEFINITIONS = listBlockDefinitions();

export function BlockLibraryPanel(): React.ReactElement {
  const { data, setBlocks, selectBlock, saving } = useHomeEditorContext();

  const handleAdd = React.useCallback(
    (type: (typeof BLOCK_DEFINITIONS)[number]['type']) => {
      const freshBlock = createBlockInstance(type, data.blocks);
      setBlocks([...data.blocks, freshBlock]);
      selectBlock(freshBlock.id);
    },
    [data.blocks, selectBlock, setBlocks],
  );

  return (
    <Card padding="sm" className="h-full space-y-4">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-gray-900">Библиотека блоков</h3>
        <p className="text-xs text-gray-500">Добавляйте заранее сконфигурированные блоки на канвас.</p>
      </div>
      <div className="flex flex-col gap-2">
        {BLOCK_DEFINITIONS.map((definition) => (
          <Button
            key={definition.type}
            variant="outlined"
            color="neutral"
            className="h-auto w-full items-start justify-start gap-3 whitespace-normal py-3 text-left"
            onClick={() => handleAdd(definition.type)}
            disabled={saving}
          >
            <span className="flex h-8 w-8 flex-none items-center justify-center rounded-md bg-gray-100 text-gray-600">
              <Plus className="h-4 w-4" />
            </span>
            <span className="flex min-w-0 flex-1 flex-col gap-1 text-left">
              <span className="text-sm font-semibold text-gray-900">{definition.label}</span>
              <span className="text-xs text-gray-500 leading-4">{definition.description}</span>
            </span>
          </Button>
        ))}
      </div>
    </Card>
  );
}

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
      <div>
        <h3 className="text-sm font-semibold text-gray-900">Библиотека блоков</h3>
        <p className="text-xs text-gray-500">Добавляйте заранее сконфигурированные блоки на канвас.</p>
      </div>
      <div className="grid gap-2">
        {BLOCK_DEFINITIONS.map((definition) => (
          <Button
            key={definition.type}
            variant="outlined"
            color="neutral"
            className="justify-start"
            onClick={() => handleAdd(definition.type)}
            disabled={saving}
          >
            <span className="inline-flex items-center gap-3">
              <span className="rounded-md bg-gray-100 p-1.5 text-gray-600">
                <Plus className="h-4 w-4" />
              </span>
              <span>
                <span className="block text-sm font-semibold text-gray-900">{definition.label}</span>
                <span className="block text-xs text-gray-500">{definition.description}</span>
              </span>
            </span>
          </Button>
        ))}
      </div>
    </Card>
  );
}
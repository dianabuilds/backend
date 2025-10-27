import React from 'react';
import { Link } from 'react-router-dom';
import { Card, Input, Button } from '@ui';
import { Plus, Search } from '@icons';
import { useHomeEditorContext } from '../HomeEditorContext';
import { createBlockInstance, listBlockDefinitions } from '../blockDefinitions';

const BLOCK_DEFINITIONS = listBlockDefinitions();

export function BlockLibraryPanel(): React.ReactElement {
  const { data, setBlocks, selectBlock, saving } = useHomeEditorContext();
  const [query, setQuery] = React.useState('');

  const filteredDefinitions = React.useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return BLOCK_DEFINITIONS;
    }
    return BLOCK_DEFINITIONS.filter((definition) => {
      const haystack = [
        definition.label,
        definition.description,
        definition.type,
      ].join(' ').toLowerCase();
      return haystack.includes(normalized);
    });
  }, [query]);

  const handleAdd = React.useCallback(
    (type: (typeof BLOCK_DEFINITIONS)[number]['type']) => {
      const freshBlock = createBlockInstance(type, data.blocks);
      setBlocks([...data.blocks, freshBlock]);
      selectBlock(freshBlock.id);
    },
    [data.blocks, selectBlock, setBlocks],
  );

  const handleSearchChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  }, []);

  return (
    <Card padding="sm" className="flex h-full flex-col gap-4 bg-white/95 shadow-sm">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-gray-900">Библиотека блоков</h3>
        <p className="text-xs text-gray-500">Добавляйте заранее сконфигурированные блоки на канвас.</p>
      </div>
      <Input
        value={query}
        onChange={handleSearchChange}
        placeholder="Поиск по названию или описанию"
        prefix={<Search className="h-4 w-4 text-gray-400" />}
      />
      <div className="text-xs text-gray-500">
        Найдено {filteredDefinitions.length} из {BLOCK_DEFINITIONS.length}
      </div>
      <div className="scrollbar-thin -mr-2 flex-1 space-y-2 overflow-y-auto pr-1">
        {filteredDefinitions.map((definition) => (
          <button
            key={definition.type}
            type="button"
            onClick={() => handleAdd(definition.type)}
            disabled={saving}
            className="group flex w-full items-start gap-3 rounded-xl border border-gray-200 bg-white px-3 py-2 text-left shadow-sm transition hover:border-primary-400 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className="flex h-8 w-8 flex-none items-center justify-center rounded-lg bg-primary-50 text-primary-600">
              <Plus className="h-4 w-4 transition group-hover:scale-110" />
            </span>
            <span className="flex min-w-0 flex-1 flex-col gap-1">
              <span className="truncate text-sm font-semibold text-gray-900">{definition.label}</span>
              <span className="text-xs leading-4 text-gray-500">{definition.description}</span>
              <span className="text-[11px] uppercase tracking-wide text-gray-400">
                Шаблон · <span className="font-mono lowercase text-gray-500">{definition.type}</span>
              </span>
            </span>
          </button>
        ))}
        {filteredDefinitions.length === 0 ? (
          <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 text-center text-sm text-gray-500">
            По запросу ничего не найдено.
          </div>
        ) : null}
      </div>
      <Button
        as={Link}
        to="/management/site-editor/library"
        variant="ghost"
        color="neutral"
        size="sm"
        className="w-full justify-center"
      >
        Открыть полную библиотеку
      </Button>
    </Card>
  );
}

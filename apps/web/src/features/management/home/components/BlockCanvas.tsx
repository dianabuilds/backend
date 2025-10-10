import React from 'react';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  type DragEndEvent,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  arrayMove,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Badge, Button, Card, Switch } from '@ui';
import { GripVertical, Trash2 } from '@icons';
import type { HomeBlock } from '../types';
import { useHomeEditorContext } from '../HomeEditorContext';
import { getBlockLabel } from '../blockDefinitions';

const DRAG_SENSOR_ACTIVATION = { distance: 5 } as const;

type SortableBlockCardProps = {
  block: HomeBlock;
  index: number;
  selected: boolean;
  hasErrors: boolean;
  onSelect: (blockId: string) => void;
  onToggle: (blockId: string, enabled: boolean) => void;
  onRemove: (blockId: string) => void;
};

function SortableBlockCard({ block, index, selected, hasErrors, onSelect, onToggle, onRemove }: SortableBlockCardProps): React.ReactElement {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: block.id });

  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const label = getBlockLabel(block.type);
  const isDisabled = !block.enabled;

  const cardClass = [
    'relative rounded-lg border bg-white p-3 shadow-sm transition-all',
    selected
      ? 'border-primary-500 shadow-primary-200/60 ring-1 ring-primary-500/30'
      : hasErrors
        ? 'border-amber-400 bg-amber-50/80'
        : 'border-gray-200',
    isDragging ? 'shadow-lg ring-2 ring-primary-400/40' : '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={cardClass}
      data-testid={`home-block-${block.id}`}
      onClick={() => onSelect(block.id)}
    >
      <div className={`flex items-start gap-3 ${isDisabled ? 'opacity-60' : ''}`}>
        <button
          type="button"
          aria-label="Переместить блок"
          className="mt-1 inline-flex h-6 w-6 shrink-0 cursor-grab items-center justify-center rounded border border-gray-200 bg-gray-50 text-gray-500 hover:text-gray-700"
          {...attributes}
          {...listeners}
          onClick={(event) => event.stopPropagation()}
        >
          <GripVertical className="h-4 w-4" />
        </button>

        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="truncate text-sm font-semibold text-gray-900">{block.title || label}</span>
            <Badge variant="outline" color="neutral">{label}</Badge>
            {hasErrors ? <Badge color="warning">Есть ошибки</Badge> : null}
            {isDisabled ? <Badge color="neutral">Отключён</Badge> : null}
          </div>
          <div className="text-xs text-gray-500">
            <span className="uppercase tracking-wide">#{index + 1}</span>
            <span className="mx-2">•</span>
            <span className="font-mono text-[11px]">{block.id}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div onClick={(event) => event.stopPropagation()}>
            <Switch
              aria-label="Включить или выключить блок"
              checked={block.enabled}
              onChange={(event) => onToggle(block.id, event.target.checked)}
            />
          </div>
          <Button aria-label="Удалить блок"
            type="button"
            size="icon"
            variant="ghost"
            color="neutral"
            onClick={(event) => {
              event.stopPropagation();
              onRemove(block.id);
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

export function BlockCanvas(): React.ReactElement {
  const { data, setBlocks, selectBlock, selectedBlockId, validation } = useHomeEditorContext();
  const blocks = data.blocks;

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: DRAG_SENSOR_ACTIVATION }));

  const handleDragEnd = React.useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) {
      return;
    }
    const oldIndex = blocks.findIndex((item) => item.id === active.id);
    const newIndex = blocks.findIndex((item) => item.id === over.id);
    if (oldIndex === -1 || newIndex === -1) {
      return;
    }
    const reordered = arrayMove(blocks, oldIndex, newIndex);
    setBlocks(reordered);
  }, [blocks, setBlocks]);

  const handleToggle = React.useCallback((blockId: string, enabled: boolean) => {
    const updated = blocks.map((block) => (block.id === blockId ? { ...block, enabled } : block));
    setBlocks(updated);
  }, [blocks, setBlocks]);

  const handleRemove = React.useCallback((blockId: string) => {
    const updated = blocks.filter((block) => block.id !== blockId);
    setBlocks(updated);
    if (selectedBlockId === blockId) {
      selectBlock(updated[0]?.id ?? null);
    }
  }, [blocks, selectBlock, selectedBlockId, setBlocks]);

  const handleSelect = React.useCallback((blockId: string) => {
    selectBlock(blockId);
  }, [selectBlock]);

  return (
    <Card padding="sm" className="min-h-[600px] space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Текущая раскладка</h3>
        <span className="text-xs text-gray-500">{blocks.length} блок(ов)</span>
      </div>

      {blocks.length === 0 ? (
        <div className="flex h-full min-h-[320px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-gray-200 bg-gray-50 p-6 text-center text-sm text-gray-500">
          <p>На канвасе пока нет блоков. Добавьте блок из библиотеки слева.</p>
        </div>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={blocks.map((block) => block.id)} strategy={verticalListSortingStrategy}>
            <div className="space-y-3">
              {blocks.map((block, index) => (
                <SortableBlockCard
                  key={block.id}
                  block={block}
                  index={index}
                  selected={selectedBlockId === block.id}
                  hasErrors={Boolean((validation.blocks[block.id] ?? []).length)}
                  onSelect={handleSelect}
                  onToggle={handleToggle}
                  onRemove={handleRemove}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}
    </Card>
  );
}

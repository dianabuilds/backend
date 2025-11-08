import React from 'react';
import { Link } from 'react-router-dom';
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
import { Badge, Button, Card, Select, Spinner, Switch } from '@ui';
import { AlertTriangle, ExternalLink, GripVertical, Trash2 } from '@icons';
import { managementSiteEditorApi } from '@shared/api/management';
import { extractErrorMessage } from '@shared/utils/errors';
import { reviewAppearance } from '../../site-editor/utils/pageHelpers';
import { STATUS_META } from '../../site-editor/components/SiteBlockLibraryPage.constants';
import type { SiteBlock, SitePageAttachedBlock, SitePageSummary } from '@shared/types/management';
import type { HomeBlock } from '../types';
import { useHomeEditorContext } from '../HomeEditorContext';
import { getBlockLabel } from '../blockDefinitions';

const DRAG_SENSOR_ACTIVATION = { distance: 5 } as const;

const SHARED_SECTIONS: Array<{
  key: 'header' | 'footer';
  label: string;
  position: 'top' | 'bottom';
}> = [
  { key: 'header', label: '', position: 'top' },
  { key: 'footer', label: '', position: 'bottom' },
];

const SHARED_SECTION_STYLES: Record<
  'header' | 'footer',
  { container: string; badgeColor: 'primary' | 'success' }
> = {
  header: {
    container: 'border-indigo-200/80 bg-indigo-50/70 backdrop-blur-[1px]',
    badgeColor: 'primary',
  },
  footer: {
    container: 'border-emerald-200/80 bg-emerald-50/70 backdrop-blur-[1px]',
    badgeColor: 'success',
  },
};

type SharedBlockOption = Pick<
  SiteBlock,
  | 'id'
  | 'key'
  | 'title'
  | 'section'
  | 'status'
  | 'review_status'
  | 'requires_publisher'
  | 'has_pending_publish'
  | 'locale'
  | 'default_locale'
  | 'available_locales'
  | 'updated_at'
  | 'updated_by'
> & {
  scope?: SiteBlock['scope'];
};

function normalizeSectionKey(value: string | null | undefined): 'header' | 'footer' | 'other' {
  if (!value) {
    return 'other';
  }
  const normalized = value.trim().toLowerCase();
  if (normalized === 'header' || normalized === 'footer') {
    return normalized;
  }
  return 'other';
}

function mapBaselineBindings(page: SitePageSummary | null): Record<string, SitePageAttachedBlock | null> {
  const map: Record<string, SitePageAttachedBlock | null> = {};
  const source = page?.shared_bindings ?? null;
  if (!Array.isArray(source)) {
    return map;
  }
  source.forEach((item) => {
    if (!item) {
      return;
    }
    const sectionKey = normalizeSectionKey(item.section);
    map[sectionKey] = item;
  });
  return map;
}

type SharedSlotsState = {
  loading: boolean;
  error: string | null;
  options: SharedBlockOption[];
};

function useSharedSlotOptions(defaultLocale: string): {
  state: SharedSlotsState;
  optionsByKey: Map<string, SharedBlockOption>;
  optionsBySection: Map<string, SharedBlockOption[]>;
  refresh: () => void;
} {
  const [state, setState] = React.useState<SharedSlotsState>({
    loading: false,
    error: null,
    options: [],
  });
  const [refreshToken, setRefreshToken] = React.useState(0);

  React.useEffect(() => {
    const controller = new AbortController();
    setState((prev) => ({ ...prev, loading: true, error: null }));
    managementSiteEditorApi
      .fetchSiteBlocks(
        {
          page: 1,
          pageSize: 200,
          scope: 'shared',
          status: 'published',
          locale: defaultLocale,
        },
        { signal: controller.signal },
      )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        const items = Array.isArray(response.items) ? response.items : [];
        const normalized = items.map((item) => ({
          id: item.id,
          key: item.key,
          title: item.title,
          section: item.section,
          status: item.status,
          review_status: item.review_status,
          requires_publisher: item.requires_publisher,
          has_pending_publish: item.has_pending_publish,
          locale: item.locale,
          default_locale: item.default_locale,
          available_locales: item.available_locales,
          updated_at: item.updated_at,
          updated_by: item.updated_by,
          scope: item.scope,
        } satisfies SharedBlockOption));
        setState({ loading: false, error: null, options: normalized });
      })
      .catch((error) => {
        if ((error as { name?: string })?.name === 'AbortError') {
          return;
        }
        setState({ loading: false, error: extractErrorMessage(error, '   shared-.'), options: [] });
      });
    return () => controller.abort();
  }, [defaultLocale, refreshToken]);

  const optionsByKey = React.useMemo(() => {
    const map = new Map<string, SharedBlockOption>();
    state.options.forEach((option) => {
      if (option?.key) {
        map.set(option.key, option);
      }
    });
    return map;
  }, [state.options]);

  const optionsBySection = React.useMemo(() => {
    const sectionMap = new Map<string, SharedBlockOption[]>();
    state.options.forEach((option) => {
      const key = normalizeSectionKey(option.section);
      if (!sectionMap.has(key)) {
        sectionMap.set(key, []);
      }
      sectionMap.get(key)!.push(option);
    });
    SHARED_SECTIONS.forEach((section) => {
      if (!sectionMap.has(section.key)) {
        sectionMap.set(section.key, []);
      }
    });
    return sectionMap;
  }, [state.options]);

  const refresh = React.useCallback(() => {
    setRefreshToken((value) => value + 1);
  }, []);

  return { state, optionsByKey, optionsBySection, refresh };
}

type SharedSlotRowProps = {
  section: 'header' | 'footer';
  label: string;
  baseline: SitePageAttachedBlock | null;
  binding: SitePageAttachedBlock | null;
  assignedKey: string | null;
  options: SharedBlockOption[];
  optionsByKey: Map<string, SharedBlockOption>;
  locale: string;
  loading: boolean;
  onAssign: (section: string, blockId: string, meta: { key: string; locale: string | null }) => Promise<void>;
  onClear: (section: string, locale: string | null) => Promise<void>;
};

function SharedSlotRow({
  section,
  label,
  baseline,
  binding,
  assignedKey,
  options,
  optionsByKey,
  locale,
  loading,
  onAssign,
  onClear,
}: SharedSlotRowProps): React.ReactElement {
  const assignedOption = assignedKey ? optionsByKey.get(assignedKey) ?? null : null;
  const statusValue = binding?.status ?? assignedOption?.status ?? baseline?.status ?? null;
  const statusMeta = statusValue && (statusValue === 'draft' || statusValue === 'published' || statusValue === 'archived')
    ? STATUS_META[statusValue]
    : null;
  const reviewMeta = binding?.review_status
    ? reviewAppearance(binding.review_status)
    : assignedOption?.review_status
      ? reviewAppearance(assignedOption.review_status)
      : null;
  const requiresPublisher = binding?.requires_publisher ?? assignedOption?.requires_publisher ?? baseline?.requires_publisher ?? false;
  const hasPendingPublish = Boolean(
    (binding?.extras && typeof binding.extras === 'object'
      ? (binding.extras as Record<string, unknown>).has_pending_publish
      : undefined) ?? assignedOption?.has_pending_publish,
  );
  const baselineTitle = baseline?.title ?? baseline?.key ?? 'Не привязан';
  const draftTitle = assignedOption?.title ?? binding?.title ?? binding?.key ?? 'Не выбран';
  const isOverride = Boolean(baseline?.block_id) && Boolean(binding?.block_id) && baseline?.block_id !== binding?.block_id;

  const handleChange = React.useCallback(
    async (event: React.ChangeEvent<HTMLSelectElement>) => {
      const value = event.target.value;
      if (!value) {
        await onClear(section, locale);
        return;
      }
      const option = optionsByKey.get(value);
      if (!option) {
        return;
      }
      await onAssign(section, option.id, { key: option.key, locale: option.locale ?? locale });
    },
    [locale, onAssign, onClear, optionsByKey, section],
  );

  const handleClear = React.useCallback(() => {
    void onClear(section, locale);
  }, [locale, onClear, section]);

  const detailBlockId = assignedOption?.id ?? binding?.block_id ?? baseline?.block_id ?? null;

  const palette = SHARED_SECTION_STYLES[section];

  return (
    <div
      className={`rounded-xl border px-3 py-2 shadow-sm transition ${palette?.container ?? 'border-gray-200 bg-white'}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-1 min-w-0 flex-col gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-gray-900">{label}</span>
            <Badge variant="outline" color={palette?.badgeColor ?? 'neutral'}>Shared-слот</Badge>
            {statusMeta ? (
              <Badge color={statusMeta.color} variant="soft">{statusMeta.label}</Badge>
            ) : null}
            {reviewMeta ? (
              <Badge color={reviewMeta.color} variant="outline">{reviewMeta.label}</Badge>
            ) : null}
            {requiresPublisher ? (
              <Badge color="warning" variant="soft">Требуется publisher</Badge>
            ) : null}
            {isOverride ? (
              <Badge color="primary" variant="outline">Override</Badge>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-wide text-gray-500">
            <span className="font-mono lowercase">{section}</span>
            <span className="opacity-40">•</span>
            <span className="font-mono uppercase">{(binding?.locale ?? assignedOption?.locale ?? locale).toUpperCase()}</span>
          </div>
        </div>
        {loading ? <Spinner size="sm" /> : null}
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Select
          aria-label={`Назначение shared-слота для секции ${label}`}
          value={assignedKey ?? ''}
          onChange={handleChange}
          disabled={loading}
        >
          <option value="">Не выбрано</option>
          {options.map((option) => (
            <option key={option.key} value={option.key}>
              {option.title || option.key}
            </option>
          ))}
          {assignedKey && !options.some((option) => option.key === assignedKey) ? (
            <option value={assignedKey}>{assignedKey} (недоступен)</option>
          ) : null}
        </Select>
        {assignedKey ? (
          <Button type="button" size="xs" variant="ghost" onClick={handleClear} disabled={loading}>
            Сбросить
          </Button>
        ) : null}
        {detailBlockId ? (
          <Button
            as={Link}
            to={`/management/site-editor/blocks/${detailBlockId}`}
            size="xs"
            variant="ghost"
            color="neutral"
          >
            Открыть блок
          </Button>
        ) : null}
      </div>

      <div className="mt-2 space-y-1 text-xs text-gray-600">
        <div>
          Базовый блок: <span className="font-medium text-gray-900">{baselineTitle}</span>
        </div>
        {!(baseline?.block_id && binding?.block_id && baseline.block_id === binding.block_id) ? (
          <div>
            Текущий выбор: <span className="font-medium text-gray-900">{draftTitle}</span>
          </div>
        ) : null}
        {hasPendingPublish ? (
          <div className="text-indigo-600">В библиотеке есть неопубликованные изменения.</div>
        ) : null}
      </div>
    </div>
  );
}

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
  const usesLibrary = block.source === 'site' && Boolean(block.siteBlockKey);
  const libraryStatusMeta =
    usesLibrary &&
    block.siteBlockStatus &&
    (block.siteBlockStatus === 'draft' || block.siteBlockStatus === 'published' || block.siteBlockStatus === 'archived')
      ? STATUS_META[block.siteBlockStatus]
      : null;
  const libraryLink = usesLibrary && block.siteBlockId ? `/management/site-editor/blocks/${block.siteBlockId}` : null;

  const cardClass = [
    'relative flex items-center gap-3 rounded-xl border bg-white px-3 py-2 shadow-sm transition-all',
    selected
      ? 'border-primary-400 shadow-primary-200/70 ring-1 ring-primary-300/50'
      : hasErrors
        ? 'border-amber-400 bg-amber-50/70'
        : 'border-gray-200 hover:border-gray-300 hover:shadow-md',
    isDragging ? 'cursor-grabbing shadow-lg ring-2 ring-primary-300/40' : '',
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
      <button
        type="button"
        aria-label="Переместить блок"
        className="inline-flex h-7 w-7 shrink-0 cursor-grab items-center justify-center rounded-lg border border-gray-200 bg-gray-50 text-gray-500 transition hover:border-gray-300 hover:text-gray-700"
        {...attributes}
        {...listeners}
        onClick={(event) => event.stopPropagation()}
      >
        <GripVertical className="h-4 w-4" />
      </button>

      <div className={`flex min-w-0 flex-1 flex-col gap-1 ${isDisabled ? 'opacity-60' : ''}`}>
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate text-sm font-semibold text-gray-900">{block.title || label}</span>
          <Badge variant="outline" color="neutral">{label}</Badge>
          {hasErrors ? <Badge color="warning">Есть ошибки</Badge> : null}
          {isDisabled ? <Badge color="neutral">Отключён</Badge> : null}
          {usesLibrary ? <Badge color="primary" variant="soft">Библиотека</Badge> : null}
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-wide text-gray-500">
          <span>#{index + 1}</span>
          <span className="opacity-40"></span>
          <span className="font-mono lowercase">{block.id}</span>
        </div>
        {usesLibrary ? (
          <div className="flex flex-wrap items-center gap-1 text-xs text-indigo-700">
            <span className="truncate font-semibold text-indigo-900">
              {block.siteBlockTitle ?? block.siteBlockKey ?? 'Блок из библиотеки'}
            </span>
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
            {block.siteBlockLocale ? (
              <span className="rounded-md border border-indigo-100 bg-indigo-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-indigo-700">
                {block.siteBlockLocale}
              </span>
            ) : null}
          </div>
        ) : null}
      </div>

      <div className="flex items-center gap-2">
        {libraryLink ? (
          <Button
            as={Link}
            to={libraryLink}
            type="button"
            size="icon"
            variant="ghost"
            color="neutral"
            onClick={(event) => event.stopPropagation()}
            aria-label="Открыть блок в библиотеке"
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        ) : null}
        <div onClick={(event) => event.stopPropagation()}>
          <Switch
            aria-label="Включить или выключить блок"
            checked={block.enabled}
            onChange={(event) => onToggle(block.id, event.target.checked)}
          />
        </div>
        <Button
          aria-label="Удалить блок"
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
  );
}

export function BlockCanvas(): React.ReactElement {
  const {
    page,
    data,
    setBlocks,
    selectBlock,
    selectedBlockId,
    validation,
    sharedBindings,
    sharedAssignments,
    assignSharedBinding,
    removeSharedBinding,
  } = useHomeEditorContext();
  const blocks = data.blocks;

  const defaultLocale = React.useMemo(
    () => page?.default_locale || page?.locale || 'ru',
    [page?.default_locale, page?.locale],
  );

  const baselineBindings = React.useMemo(() => mapBaselineBindings(page ?? null), [page]);

  const { state: sharedState, optionsByKey, optionsBySection, refresh: refreshShared } = useSharedSlotOptions(defaultLocale);

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
    <Card padding="sm" className="space-y-3 bg-white/95 shadow-sm">
      <div className="flex items-center justify-between rounded-xl border border-gray-100/80 bg-gray-50/60 px-3 py-2">
        <h3 className="text-sm font-semibold text-gray-900">Структура страницы</h3>
        <span className="text-xs text-gray-500">{blocks.length} блок(ов)</span>
      </div>

      {sharedState.error ? (
        <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <div className="flex-1">
            <p>{sharedState.error}</p>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              className="mt-2"
              onClick={refreshShared}
              disabled={sharedState.loading}
            >
              Повторить попытку
            </Button>
          </div>
        </div>
      ) : null}

      {SHARED_SECTIONS.filter((item) => item.position === 'top').map((item) => (
        <SharedSlotRow
          key={item.key}
          section={item.key}
          label={item.label}
          baseline={baselineBindings[item.key] ?? null}
          binding={sharedBindings[item.key] ?? null}
          assignedKey={sharedAssignments[item.key] ?? null}
          options={optionsBySection.get(item.key) ?? []}
          optionsByKey={optionsByKey}
          locale={defaultLocale}
          loading={sharedState.loading}
          onAssign={(sectionKey, blockId, meta) => assignSharedBinding(sectionKey, blockId, meta)}
          onClear={(sectionKey, localeHint) => removeSharedBinding(sectionKey, { locale: localeHint })}
        />
      ))}

      {blocks.length === 0 ? (
        <div className="flex h-full min-h-[240px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-gray-200 bg-gray-50 p-6 text-center text-sm text-gray-500">
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

      {SHARED_SECTIONS.filter((item) => item.position === 'bottom').map((item) => (
        <SharedSlotRow
          key={item.key}
          section={item.key}
          label={item.label}
          baseline={baselineBindings[item.key] ?? null}
          binding={sharedBindings[item.key] ?? null}
          assignedKey={sharedAssignments[item.key] ?? null}
          options={optionsBySection.get(item.key) ?? []}
          optionsByKey={optionsByKey}
          locale={defaultLocale}
          loading={sharedState.loading}
          onAssign={(sectionKey, blockId, meta) => assignSharedBinding(sectionKey, blockId, meta)}
          onClear={(sectionKey, localeHint) => removeSharedBinding(sectionKey, { locale: localeHint })}
        />
      ))}
    </Card>
  );
}

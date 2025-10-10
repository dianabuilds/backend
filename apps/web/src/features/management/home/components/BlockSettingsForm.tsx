import React from 'react';
import { Input, Textarea, Select, Switch, TagInput } from '@ui';
import type { HomeBlock, HomeBlockDataSource } from '../types';
import type { FieldError } from '../validation';

const DEFAULT_MODE_MAP: Record<HomeBlock['type'], 'auto' | 'manual'> = {
  hero: 'manual',
  dev_blog_list: 'auto',
  quests_carousel: 'auto',
  nodes_carousel: 'auto',
  popular_carousel: 'auto',
  editorial_picks: 'manual',
  recommendations: 'auto',
  custom_carousel: 'manual',
};

const MODE_OPTIONS: Array<{ value: 'auto' | 'manual'; label: string }> = [
  { value: 'auto', label: 'Авто' },
  { value: 'manual', label: 'Ручной' },
];

const ENTITY_OPTIONS: Array<{ value: string; label: string }> = [
  { value: 'node', label: 'Ноды' },
  { value: 'quest', label: 'Квесты' },
  { value: 'dev_blog', label: 'Dev Blog' },
  { value: 'custom', label: 'Произвольные данные' },
];

const MODE_LIMITS: Partial<Record<HomeBlock['type'], Array<'auto' | 'manual'>>> = {
  hero: [],
  editorial_picks: ['manual'],
  custom_carousel: ['manual'],
  popular_carousel: ['auto'],
  recommendations: ['auto'],
};

type BlockSettingsFormProps = {
  block: HomeBlock;
  onChange: (updater: (current: HomeBlock) => HomeBlock) => void;
  errors: FieldError[];
};

type SlotsRecord = Record<string, unknown>;

type DataSourceMutator = (current: HomeBlockDataSource) => HomeBlockDataSource | null;

type SlotsMutator = (slots: SlotsRecord) => SlotsRecord;

function asRecord(value: unknown): SlotsRecord {
  return value && typeof value === 'object' && !Array.isArray(value) ? { ...(value as SlotsRecord) } : {};
}

function fieldErrors(errors: FieldError[], path: string): string[] {
  return errors
    .filter((err) => err.path === path || err.path.startsWith(`${path}/`))
    .map((err) => err.message);
}

function firstFieldError(errors: FieldError[], path: string): string | undefined {
  return fieldErrors(errors, path)[0];
}

function ensureDataSource(block: HomeBlock, current?: HomeBlockDataSource | null): HomeBlockDataSource {
  if (current) {
    return {
      ...current,
      filter: current.filter ? { ...current.filter } : undefined,
      items: current.items ? [...current.items] : undefined,
    };
  }
  const defaultMode = DEFAULT_MODE_MAP[block.type] ?? 'manual';
  const defaultEntity = block.type === 'dev_blog_list' ? 'dev_blog'
    : block.type === 'custom_carousel' ? 'custom'
    : block.type === 'quests_carousel' ? 'quest'
    : 'node';
  const base: HomeBlockDataSource = {
    mode: defaultMode,
    entity: defaultEntity,
  };
  if (defaultMode === 'manual') {
    base.items = [];
  }
  return base;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-semibold text-gray-900">{title}</h4>
      </div>
      <div className="grid gap-4">{children}</div>
    </div>
  );
}

export function BlockSettingsForm({ block, onChange, errors }: BlockSettingsFormProps): React.ReactElement {
  const slots = React.useMemo(() => asRecord(block.slots), [block.slots]);
  const ctaSlots = React.useMemo(() => asRecord(slots.cta), [slots]);

  const allowedModes = MODE_LIMITS[block.type] ?? ['auto', 'manual'];

  const updateBlock = React.useCallback(
    (updater: (current: HomeBlock) => HomeBlock) => {
      onChange((current) => updater(current));
    },
    [onChange],
  );

  const updateSlots = React.useCallback(
    (mutator: SlotsMutator) => {
      updateBlock((current) => {
        const nextSlots = mutator(asRecord(current.slots));
        return {
          ...current,
          slots: nextSlots,
        };
      });
    },
    [updateBlock],
  );

  const updateDataSource = React.useCallback(
    (mutator: DataSourceMutator) => {
      updateBlock((current) => {
        const base = ensureDataSource(current, current.dataSource);
        const next = mutator(base);
        return {
          ...current,
          dataSource: next ?? undefined,
        };
      });
    },
    [updateBlock],
  );

  const handleTitleChange = (value: string) => {
    updateBlock((current) => ({
      ...current,
      title: value,
    }));
  };

  const handleEnabledChange = (enabled: boolean) => {
    updateBlock((current) => ({
      ...current,
      enabled,
    }));
  };

  const handleSlotChange = (key: string, value: string) => {
    updateSlots((prev) => {
      const next = { ...prev };
      if (value.trim()) {
        next[key] = value;
      } else {
        delete next[key];
      }
      return next;
    });
  };

  const handleCtaChange = (field: string, value: string) => {
    updateSlots((prev) => {
      const next = { ...prev };
      const cta = asRecord(next.cta);
      if (value.trim()) {
        cta[field] = value;
      } else {
        delete cta[field];
      }
      next.cta = Object.keys(cta).length ? cta : undefined;
      return next;
    });
  };

  const handleModeChange = (mode: 'auto' | 'manual') => {
    updateDataSource((current) => {
      const next: HomeBlockDataSource = {
        ...current,
        mode,
      };
      if (mode === 'manual') {
        next.items = Array.isArray(current.items) ? [...current.items] : [];
      } else {
        delete next.items;
      }
      return next;
    });
  };

  const handleEntityChange = (entity: string) => {
    updateDataSource((current) => ({
      ...current,
      entity: entity as HomeBlockDataSource['entity'],
    }));
  };

  const handleFilterChange = (key: string, value: string) => {
    updateDataSource((current) => {
      const filter = asRecord(current.filter);
      if (!value.trim()) {
        delete filter[key];
      } else if (key === 'limit') {
        const parsed = Number.parseInt(value, 10);
        if (Number.isFinite(parsed)) {
          filter.limit = parsed;
        } else {
          delete filter.limit;
        }
      } else {
        filter[key] = value;
      }
      const next: HomeBlockDataSource = {
        ...current,
        filter: Object.keys(filter).length ? filter : undefined,
      };
      return next;
    });
  };

  const handleItemsChange = (items: string[]) => {
    updateDataSource((current) => ({
      ...current,
      items,
    }));
  };

  const dataSource = React.useMemo(() => ensureDataSource(block, block.dataSource), [block]);

  const renderHeroSettings = block.type === 'hero';
  const renderDataSource = block.type !== 'hero';
  const renderEditorialSlots = block.type === 'editorial_picks';
  const renderDevBlogSlots = block.type === 'dev_blog_list';
  const renderCustomLayout = block.type === 'custom_carousel';

  const manualOnly = allowedModes.length === 1 && allowedModes[0] === 'manual';
  const autoOnly = allowedModes.length === 1 && allowedModes[0] === 'auto';

  const modeError = firstFieldError(errors, '/dataSource/mode');
  const entityError = firstFieldError(errors, '/dataSource/entity');
  const limitError = firstFieldError(errors, '/dataSource/filter/limit');
  const tagError = firstFieldError(errors, '/dataSource/filter/tag');
  const orderError = firstFieldError(errors, '/dataSource/filter/order');
  const itemsError = firstFieldError(errors, '/dataSource/items');

  return (
    <div className="space-y-8">
      <Section title="Основные настройки">
        <Input
          label="Название блока"
          value={block.title ?? ''}
          placeholder="Например, Главный блок"
          onChange={(event) => handleTitleChange(event.target.value)}
          error={firstFieldError(errors, '/title')}
        />
        <Input
          label="Идентификатор"
          value={block.id}
          readOnly
          disabled
          description="Используется для привязки в шаблонах."
        />
        <Switch
          label="Активировать блок"
          checked={block.enabled}
          onChange={(event) => handleEnabledChange(event.target.checked)}
        />
      </Section>

      {renderHeroSettings ? (
        <Section title="Hero-блок">
          <Input
            label="Заголовок"
            value={typeof slots.headline === 'string' ? slots.headline : ''}
            placeholder="Заголовок hero"
            onChange={(event) => handleSlotChange('headline', event.target.value)}
            error={firstFieldError(errors, '/slots/headline')}
          />
          <Textarea
            label="Описание"
            value={typeof slots.subheadline === 'string' ? slots.subheadline : ''}
            rows={3}
            placeholder="Краткое описание"
            onChange={(event) => handleSlotChange('subheadline', event.target.value)}
            error={firstFieldError(errors, '/slots/subheadline')}
          />
          <div className="grid gap-4 md:grid-cols-2">
            <Input
              label="CTA — текст кнопки"
              value={typeof ctaSlots.label === 'string' ? ctaSlots.label : ''}
              placeholder="Например, Узнать больше"
              onChange={(event) => handleCtaChange('label', event.target.value)}
              error={firstFieldError(errors, '/slots/cta/label')}
            />
            <Input
              label="CTA — ссылка"
              value={typeof ctaSlots.href === 'string' ? ctaSlots.href : ''}
              placeholder="/quests"
              onChange={(event) => handleCtaChange('href', event.target.value)}
              error={firstFieldError(errors, '/slots/cta/href')}
            />
          </div>
        </Section>
      ) : null}

      {renderEditorialSlots ? (
        <Section title="Контент секции">
          <Input
            label="Заголовок"
            value={typeof slots.headline === 'string' ? slots.headline : ''}
            onChange={(event) => handleSlotChange('headline', event.target.value)}
            error={firstFieldError(errors, '/slots/headline')}
          />
          <Textarea
            label="Описание"
            value={typeof slots.description === 'string' ? slots.description : ''}
            rows={3}
            onChange={(event) => handleSlotChange('description', event.target.value)}
            error={firstFieldError(errors, '/slots/description')}
          />
        </Section>
      ) : null}

      {renderDevBlogSlots ? (
        <Section title="Dev Blog">
          <Input
            label="Заголовок секции"
            value={typeof slots.headline === 'string' ? slots.headline : ''}
            onChange={(event) => handleSlotChange('headline', event.target.value)}
            error={firstFieldError(errors, '/slots/headline')}
          />
        </Section>
      ) : null}

      {renderCustomLayout ? (
        <Section title="Настройки макета">
          <Input
            label="Layout"
            value={typeof slots.layout === 'string' ? slots.layout : ''}
            placeholder="carousel"
            onChange={(event) => handleSlotChange('layout', event.target.value)}
            error={firstFieldError(errors, '/slots/layout')}
          />
        </Section>
      ) : null}

      {renderDataSource ? (
        <Section title="Источник данных">
          <div className="grid gap-4 md:grid-cols-2">
            <Select
              label="Режим"
              value={dataSource.mode}
              onChange={(event) => handleModeChange(event.target.value as 'auto' | 'manual')}
              disabled={allowedModes.length === 1}
            >
              {MODE_OPTIONS.filter((option) => allowedModes.includes(option.value)).map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </Select>
            <Select
              label="Сущности"
              value={dataSource.entity ?? ''}
              onChange={(event) => handleEntityChange(event.target.value)}
              error={entityError}
            >
              <option value="">Не выбрано</option>
              {ENTITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </Select>
          </div>

          {modeError ? <div className="text-xs text-error">{modeError}</div> : null}

          <div className="grid gap-4 md:grid-cols-3">
            <Input
              label="Лимит"
              type="number"
              min={1}
              max={24}
              value={typeof dataSource.filter?.limit === 'number' ? String(dataSource.filter.limit) : ''}
              onChange={(event) => handleFilterChange('limit', event.target.value)}
              error={limitError}
            />
            <Input
              label="Тег"
              value={typeof dataSource.filter?.tag === 'string' ? dataSource.filter.tag : ''}
              onChange={(event) => handleFilterChange('tag', event.target.value)}
              error={tagError}
            />
            <Input
              label="Сортировка"
              value={typeof dataSource.filter?.order === 'string' ? dataSource.filter.order : ''}
              onChange={(event) => handleFilterChange('order', event.target.value)}
              error={orderError}
              placeholder="например, publish_at_desc"
            />
          </div>

          {dataSource.mode === 'manual' ? (
            <div className="space-y-2">
              <TagInput
                value={Array.isArray(dataSource.items) ? dataSource.items.map((item) => String(item)) : []}
                onChange={handleItemsChange}
                label="Список элементов"
                placeholder="id или slug"
              />
              {itemsError ? <div className="text-xs text-error">{itemsError}</div> : null}
            </div>
          ) : null}

          {autoOnly ? (
            <div className="text-xs text-gray-500">Для этого блока доступен только автоматический режим.</div>
          ) : null}
          {manualOnly ? (
            <div className="text-xs text-gray-500">Для этого блока доступен только ручной режим.</div>
          ) : null}
        </Section>
      ) : null}
    </div>
  );
}

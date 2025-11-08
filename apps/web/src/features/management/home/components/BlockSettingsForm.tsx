import React from 'react';
import { Link } from 'react-router-dom';
import { Button, Input, Select, Spinner, Switch, Textarea } from '@ui';
import { ExternalLink } from '@icons';
import { managementSiteEditorApi } from '@shared/api/management';
import { formatDateTime } from '@shared/utils/format';
import type { SiteBlock } from '@shared/types/management';
import type { HomeBlock, HomeBlockDataSource } from '../types';
import type { FieldError } from '../validation';
import { useHomeEditorContext } from '../HomeEditorContext';
import { ManualItemsEditor } from './ManualItemsEditor';

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

type HeroMetadata = {
  id: string | null;
  key: string;
  title: string;
  status: SiteBlock['status'] | string | null;
  reviewStatus: SiteBlock['review_status'] | string | null;
  requiresPublisher: boolean | null;
  hasPendingPublish: boolean | null;
  hasDraft: boolean | null;
  section: string | null;
  locale: string | null;
  updatedAt: string | null;
  updatedBy: string | null;
};

type HeroContent = {
  headline?: string;
  subheadline?: string;
  description?: string;
  ctaLabel?: string;
  ctaHref?: string;
  image?: string | null;
};

type HeroContentState = {
  loading: boolean;
  error: string | null;
  content: HeroContent | null;
};

function asRecord(value: unknown): SlotsRecord {
  return value && typeof value === 'object' && !Array.isArray(value) ? { ...(value as SlotsRecord) } : {};
}

function normalizeHeroSlots(source: unknown): SlotsRecord {
  if (!source || typeof source !== 'object') {
    return {};
  }
  const record = source as Record<string, unknown>;
  if (record.slots && typeof record.slots === 'object') {
    return asRecord(record.slots);
  }
  if (record.content && typeof record.content === 'object') {
    return asRecord(record.content);
  }
  return asRecord(source);
}

function extractHeroMediaUrl(slots: SlotsRecord | null | undefined): string | null {
  if (!slots) {
    return null;
  }
  const mediaCandidate = (slots.media ?? slots.image ?? slots.picture) as unknown;
  if (typeof mediaCandidate === 'string') {
    return mediaCandidate;
  }
  if (mediaCandidate && typeof mediaCandidate === 'object') {
    const record = mediaCandidate as Record<string, unknown>;
    if (typeof record.url === 'string') {
      return record.url;
    }
    if (typeof record.src === 'string') {
      return record.src;
    }
    if (typeof record.image === 'string') {
      return record.image;
    }
  }
  return null;
}

function extractHeroContentFromAny(source: unknown): HeroContent | null {
  const slots = normalizeHeroSlots(source);
  if (!Object.keys(slots).length) {
    return null;
  }
  const cta = asRecord(slots.cta);
  const result: HeroContent = {
    headline: typeof slots.headline === 'string' ? slots.headline : undefined,
    subheadline: typeof slots.subheadline === 'string' ? slots.subheadline : undefined,
    description: typeof slots.description === 'string' ? slots.description : undefined,
    ctaLabel: typeof cta.label === 'string' ? cta.label : undefined,
    ctaHref: typeof cta.href === 'string' ? cta.href : undefined,
    image: extractHeroMediaUrl(slots),
  };
  const hasValue = Boolean(
    result.headline ||
      result.subheadline ||
      result.description ||
      result.ctaLabel ||
      result.ctaHref ||
      result.image,
  );
  return hasValue ? result : null;
}

function extractHeroContentFromSlots(slots: SlotsRecord | null | undefined): HeroContent | null {
  return extractHeroContentFromAny(slots);
}

function extractHeroContentFromBlockData(data: Record<string, unknown> | null | undefined): HeroContent | null {
  if (!data) {
    return null;
  }
  if (data.slots && typeof data.slots === 'object') {
    return extractHeroContentFromAny(data.slots);
  }
  return extractHeroContentFromAny(data);
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
  const { activeLocale } = useHomeEditorContext();

  const allowedModes = MODE_LIMITS[block.type] ?? ['auto', 'manual'];
  const [heroOptions, setHeroOptions] = React.useState<SiteBlock[]>([]);
  const [heroLoading, setHeroLoading] = React.useState(false);
  const [heroError, setHeroError] = React.useState<string | null>(null);
  const [heroReloadKey, setHeroReloadKey] = React.useState(0);

  React.useEffect(() => {
    if (block.type !== 'hero') {
      setHeroOptions([]);
      return;
    }
    let mounted = true;
    const controller = new AbortController();
    setHeroLoading(true);
    setHeroError(null);
    managementSiteEditorApi
      .fetchSiteBlocks(
        {
          section: 'hero',
          status: 'published',
          pageSize: 100,
          sort: 'updated_at_desc',
          includeData: false,
        },
        { signal: controller.signal },
      )
      .then((response) => {
        if (!mounted) {
          return;
        }
        setHeroOptions(response.items ?? []);
      })
      .catch((err) => {
        if (!mounted || (err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setHeroError(err instanceof Error ? err.message : 'Не удалось загрузить hero-блоки');
        setHeroOptions([]);
      })
      .finally(() => {
        if (mounted) {
          setHeroLoading(false);
        }
      });
    return () => {
      mounted = false;
      controller.abort();
    };
  }, [block.type, heroReloadKey]);

  const isHeroBlock = block.type === 'hero';

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
    const normalized = items.map((item) => item.trim()).filter((item) => item.length > 0);
    updateDataSource((current) => ({
      ...current,
      items: normalized,
    }));
  };

  const dataSource = React.useMemo(() => ensureDataSource(block, block.dataSource), [block]);
  const manualItems = React.useMemo(
    () => (Array.isArray(dataSource.items) ? dataSource.items.map((item) => String(item)) : []),
    [dataSource.items],
  );

  const heroSelection = React.useMemo(() => {
    if (!heroOptions.length) {
      return null;
    }
    if (block.siteBlockKey) {
      const byKey = heroOptions.find((option) => option.key === block.siteBlockKey);
      if (byKey) {
        return byKey;
      }
    }
    if (block.siteBlockId) {
      const byId = heroOptions.find((option) => option.id === block.siteBlockId);
      if (byId) {
        return byId;
      }
    }
    return null;
  }, [block.siteBlockId, block.siteBlockKey, heroOptions]);

  const heroMeta = React.useMemo<HeroMetadata | null>(() => {
    if (heroSelection) {
      const availableLocales = heroSelection.available_locales ?? [];
      const preferredLocale =
        availableLocales.includes(activeLocale) && activeLocale
          ? activeLocale
          : heroSelection.default_locale ??
            heroSelection.locale ??
            availableLocales[0] ??
            block.siteBlockLocale ??
            activeLocale ??
            null;
      const hasDraft =
        heroSelection.draft_version != null &&
        heroSelection.draft_version !== heroSelection.published_version;
      return {
        id: heroSelection.id,
        key: heroSelection.key,
        title: heroSelection.title ?? heroSelection.key,
        status: heroSelection.status ?? null,
        reviewStatus: heroSelection.review_status ?? null,
        requiresPublisher: heroSelection.requires_publisher ?? null,
        hasPendingPublish: heroSelection.has_pending_publish ?? null,
        hasDraft,
        section: heroSelection.section ?? 'hero',
        locale: preferredLocale,
        updatedAt: heroSelection.updated_at ?? null,
        updatedBy: heroSelection.updated_by ?? null,
      };
    }
    if (block.source === 'site' && block.siteBlockKey) {
      return {
        id: block.siteBlockId ?? null,
        key: block.siteBlockKey,
        title: block.siteBlockTitle ?? block.siteBlockKey,
        status: block.siteBlockStatus ?? null,
        reviewStatus: block.siteBlockReviewStatus ?? null,
        requiresPublisher: block.siteBlockRequiresPublisher ?? null,
        hasPendingPublish: block.siteBlockHasPendingPublish ?? null,
        hasDraft: block.siteBlockHasDraft ?? null,
        section: block.siteBlockSection ?? 'hero',
        locale: block.siteBlockLocale ?? activeLocale ?? null,
        updatedAt: block.siteBlockUpdatedAt ?? null,
        updatedBy: block.siteBlockUpdatedBy ?? null,
      };
    }
    return null;
  }, [
    activeLocale,
    block.siteBlockHasDraft,
    block.siteBlockHasPendingPublish,
    block.siteBlockId,
    block.siteBlockKey,
    block.siteBlockLocale,
    block.siteBlockRequiresPublisher,
    block.siteBlockReviewStatus,
    block.siteBlockSection,
    block.siteBlockStatus,
    block.siteBlockTitle,
    block.siteBlockUpdatedAt,
    block.siteBlockUpdatedBy,
    block.source,
    heroSelection,
  ]);

  const usesHeroLibrary = isHeroBlock && block.source === 'site' && Boolean(block.siteBlockKey);
  const heroSelectValue = usesHeroLibrary && block.siteBlockKey ? block.siteBlockKey : '';

  const handleHeroAttach = React.useCallback(
    (key: string) => {
      const option = heroOptions.find((item) => item.key === key);
      if (!option) {
        return;
      }
      const availableLocales = option.available_locales ?? [];
      const resolvedLocale =
        (availableLocales.includes(activeLocale) && activeLocale) ||
        option.default_locale ||
        option.locale ||
        availableLocales[0] ||
        block.siteBlockLocale ||
        activeLocale ||
        null;
      const hasDraft =
        option.draft_version != null && option.draft_version !== option.published_version;
      updateBlock((current) => ({
        ...current,
        source: 'site',
        siteBlockId: option.id,
        siteBlockKey: option.key,
        siteBlockTitle: option.title ?? option.key,
        siteBlockStatus: option.status ?? null,
        siteBlockReviewStatus: option.review_status ?? null,
        siteBlockRequiresPublisher: option.requires_publisher ?? null,
        siteBlockHasPendingPublish: option.has_pending_publish ?? null,
        siteBlockHasDraft: hasDraft ? true : null,
        siteBlockUpdatedAt: option.updated_at ?? null,
        siteBlockUpdatedBy: option.updated_by ?? null,
        siteBlockSection: option.section ?? current.siteBlockSection ?? current.type,
        siteBlockLocale: resolvedLocale,
      }));
    },
    [activeLocale, block.siteBlockLocale, heroOptions, updateBlock],
  );

  const handleHeroDetach = React.useCallback(() => {
    updateBlock((current) => ({
      ...current,
      source: 'manual',
      siteBlockId: null,
      siteBlockKey: null,
      siteBlockTitle: null,
      siteBlockStatus: null,
      siteBlockReviewStatus: null,
      siteBlockRequiresPublisher: null,
      siteBlockHasPendingPublish: null,
      siteBlockHasDraft: null,
      siteBlockUpdatedAt: null,
      siteBlockUpdatedBy: null,
      siteBlockSection: null,
      siteBlockLocale: null,
    }));
  }, [updateBlock]);

  const handleHeroRefresh = React.useCallback(() => {
    setHeroReloadKey((value) => value + 1);
  }, []);

  const [heroContentState, setHeroContentState] = React.useState<HeroContentState>(() => ({
    loading: false,
    error: null,
    content: isHeroBlock ? extractHeroContentFromSlots(slots) : null,
  }));

  React.useEffect(() => {
    if (!isHeroBlock) {
      setHeroContentState({ loading: false, error: null, content: null });
      return;
    }
    if (usesHeroLibrary && block.siteBlockId) {
      const controller = new AbortController();
      setHeroContentState({ loading: true, error: null, content: null });
      managementSiteEditorApi
        .fetchSiteBlock(block.siteBlockId, { signal: controller.signal })
        .then((response) => {
          if (controller.signal.aborted) {
            return;
          }
          const detail = response.block ?? null;
          const content = extractHeroContentFromBlockData(
            (detail?.data as Record<string, unknown> | null | undefined) ?? null,
          );
          setHeroContentState({
            loading: false,
            error: null,
            content: content ?? null,
          });
        })
        .catch((error) => {
          if (controller.signal.aborted) {
            return;
          }
          setHeroContentState({
            loading: false,
            error: error instanceof Error ? error.message : 'Не удалось загрузить содержимое hero-блока',
            content: null,
          });
        });
      return () => controller.abort();
    }
    setHeroContentState({
      loading: false,
      error: null,
      content: extractHeroContentFromSlots(slots),
    });
  }, [block.siteBlockId, block.source, isHeroBlock, usesHeroLibrary, slots, heroReloadKey]);

  const manualHeroImage = React.useMemo(() => extractHeroMediaUrl(slots), [slots]);

  const handleHeroImageUpload = React.useCallback(
    (file: File | null) => {
      if (!file) {
        updateSlots((prev) => {
          const next = { ...prev };
          delete next.media;
          delete next.image;
          delete next.picture;
          return next;
        });
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = typeof reader.result === 'string' ? reader.result : '';
        updateSlots((prev) => {
          const next = { ...prev };
          const mediaRecord = asRecord(next.media);
          next.media = {
            ...mediaRecord,
            url: dataUrl,
            name: file.name,
            mime: file.type,
          };
          return next;
        });
      };
      reader.readAsDataURL(file);
    },
    [updateSlots],
  );

  const renderHeroSettings = isHeroBlock;
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
          <div className="space-y-4">
            <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]">
              <Select
                label="Блок из библиотеки"
                value={heroSelectValue}
                onChange={(event) => {
                  const value = event.target.value;
                  if (!value) {
                    handleHeroDetach();
                    return;
                  }
                  handleHeroAttach(value);
                }}
                disabled={heroLoading}
              >
                <option value="">Ручной режим</option>
                {heroOptions.map((option) => (
                  <option key={option.id} value={option.key}>{option.title || option.key}</option>
                ))}
              </Select>
              <Button type="button" size="sm" variant="ghost" onClick={handleHeroRefresh} disabled={heroLoading}>
                {heroLoading ? 'Обновляем…' : 'Обновить'}
              </Button>
            </div>
            {heroError ? (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                {heroError}
              </div>
            ) : null}
            {!heroLoading && heroOptions.length === 0 && !heroError ? (
              <div className="rounded-xl border border-dashed border-gray-200 bg-gray-50 p-3 text-sm text-gray-500">
                В библиотеке пока нет опубликованных hero-блоков.
              </div>
            ) : null}
            <HeroPreviewCard
              source={usesHeroLibrary ? 'library' : 'manual'}
              meta={heroMeta}
              content={heroContentState.content}
              loading={heroContentState.loading}
              error={heroContentState.error}
              onDetach={usesHeroLibrary ? handleHeroDetach : undefined}
            />
            {!usesHeroLibrary ? (
              <>
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
                <HeroMediaUploader value={manualHeroImage} onSelectFile={handleHeroImageUpload} />
              </>
            ) : null}
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
            <ManualItemsEditor
              entity={dataSource.entity ?? null}
              items={manualItems}
              onChange={handleItemsChange}
              error={itemsError ?? undefined}
            />
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

type HeroPreviewCardProps = {
  source: 'library' | 'manual';
  meta: HeroMetadata | null;
  content: HeroContent | null;
  loading: boolean;
  error: string | null;
  onDetach?: () => void;
};

function HeroPreviewCard({ source, meta, content, loading, error, onDetach }: HeroPreviewCardProps) {
  const blockLink = meta?.id ? `/management/site-editor/blocks/${meta.id}` : null;
  const displayHeadline = content?.headline ?? meta?.title ?? '—';
  const description = content?.subheadline ?? content?.description ?? null;
  const ctaText = content?.ctaLabel ? `${content.ctaLabel}${content.ctaHref ? ` · ${content.ctaHref}` : ''}` : null;
  const locale = meta?.locale ?? (source === 'manual' ? 'ru' : null);
  const keyInfo = meta?.key ? `Ключ: ${meta.key}${meta?.section ? ` · ${meta.section}` : ''}` : null;
  const updatedLabel = meta?.updatedAt
    ? `Обновлён ${formatDateTime(meta.updatedAt, { fallback: '—' })}${meta.updatedBy ? ` · ${meta.updatedBy}` : ''}`
    : null;

  return (
    <div className="space-y-3 rounded-2xl border border-primary-100 bg-primary-50/40 p-4">
      <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-wide text-primary-700">
        <span>{source === 'library' ? 'Библиотека' : 'Ручной режим'}</span>
        {locale ? (
          <span className="rounded-full border border-white/70 bg-white px-2 py-0.5 text-[10px] text-primary-700">
            {locale.toUpperCase()}
          </span>
        ) : null}
      </div>
      {loading ? (
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <Spinner size="sm" />
          Загружаем содержимое hero…
        </div>
      ) : error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
      ) : (
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
          <div className="flex-1 space-y-2">
            <div className="text-lg font-semibold text-gray-900">{displayHeadline}</div>
            {description ? <p className="text-sm text-gray-600">{description}</p> : null}
            {ctaText ? <p className="text-sm text-indigo-700">CTA: {ctaText}</p> : null}
            {keyInfo ? <p className="text-xs text-gray-500">{keyInfo}</p> : null}
            {updatedLabel ? <p className="text-xs text-gray-500">{updatedLabel}</p> : null}
          </div>
          <div className="w-full max-w-[200px] flex-shrink-0">
            {content?.image ? (
              <img src={content.image} alt="Hero preview" className="h-32 w-full rounded-xl object-cover shadow-sm" />
            ) : (
              <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-primary-200 text-center text-xs text-primary-600">
                {source === 'library' ? 'Изображение отсутствует' : 'Добавьте изображение'}
              </div>
            )}
          </div>
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        {blockLink ? (
          <Button as={Link} to={blockLink} size="sm" variant="ghost">
            <ExternalLink className="mr-2 h-4 w-4" />
            Открыть блок
          </Button>
        ) : null}
        {source === 'library' && onDetach ? (
          <Button type="button" size="sm" variant="ghost" color="neutral" onClick={onDetach}>
            Перейти в ручной режим
          </Button>
        ) : null}
      </div>
      {source === 'library' ? (
        <p className="text-xs text-gray-500">Контент и оформление управляются в библиотеке блоков.</p>
      ) : (
        <p className="text-xs text-gray-500">Контент можно отредактировать ниже или подключить блок из библиотеки.</p>
      )}
    </div>
  );
}

type HeroMediaUploaderProps = {
  value: string | null;
  onSelectFile: (file: File | null) => void;
};

function HeroMediaUploader({ value, onSelectFile }: HeroMediaUploaderProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = React.useState(false);

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0] ?? null;
    if (file) {
      onSelectFile(file);
    }
  };

  return (
    <div
      className={`space-y-3 rounded-2xl border-2 border-dashed p-4 text-sm ${
        dragActive ? 'border-primary-400 bg-primary-50/60' : 'border-gray-200 bg-white'
      }`}
      onDragOver={(event) => {
        event.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={(event) => {
        event.preventDefault();
        setDragActive(false);
      }}
      onDrop={handleDrop}
    >
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-medium text-gray-900">Изображение hero</p>
          <p className="text-xs text-gray-500">Перетащите файл или выберите картинку с компьютера.</p>
        </div>
        <div className="flex gap-2">
          <Button type="button" size="sm" onClick={() => inputRef.current?.click()}>
            Выбрать файл
          </Button>
          {value ? (
            <Button type="button" size="sm" variant="ghost" color="neutral" onClick={() => onSelectFile(null)}>
              Очистить
            </Button>
          ) : null}
        </div>
      </div>
      {value ? (
        <img src={value} alt="Hero media" className="h-40 w-full rounded-xl object-cover shadow-sm" />
      ) : (
        <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-gray-200 text-center text-xs text-gray-500">
          Изображение не выбрано
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(event) => {
          const file = event.currentTarget.files?.[0] ?? null;
          onSelectFile(file);
          event.currentTarget.value = '';
        }}
      />
    </div>
  );
}


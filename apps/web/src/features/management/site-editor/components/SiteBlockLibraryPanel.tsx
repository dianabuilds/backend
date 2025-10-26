import React from 'react';
import { Button, Card, Input, Select, Badge, Tag, Spinner } from '@ui';
import { ListFilter, Search, Plus, ExternalLink } from '@icons';
import { useHomeEditorContext } from '../../home/HomeEditorContext';
import { createBlockInstance } from '../../home/blockDefinitions';
import type { HomeBlock, HomeBlockType } from '../../home/types';
import {
  SITE_BLOCK_LIBRARY,
  CATEGORY_LABELS,
  SOURCE_LABELS,
  SURFACE_LABELS,
  LOCALE_LABELS,
  STATUS_LABELS,
  type SiteBlockLibraryEntry,
  type BlockCategory,
  type BlockSourceMode,
  type BlockSurface,
  type BlockLocale,
  type BlockPreviewKind,
} from '../blockLibraryData';
import { useBlockPreview } from '../dataAdapters/useBlockPreview';

type FilterValue<T> = T | 'all';

type FiltersState = {
  search: string;
  category: FilterValue<BlockCategory>;
  source: FilterValue<BlockSourceMode>;
  surface: FilterValue<BlockSurface>;
  owner: FilterValue<string>;
  locale: FilterValue<BlockLocale>;
};

const INITIAL_FILTERS: FiltersState = {
  search: '',
  category: 'all',
  source: 'all',
  surface: 'all',
  owner: 'all',
  locale: 'all',
};

const statusOrder: Record<SiteBlockLibraryEntry['status'], number> = {
  available: 0,
  design: 1,
  research: 2,
};

function collectOwners(entries: SiteBlockLibraryEntry[]): string[] {
  const owners = new Set<string>();
  for (const entry of entries) {
    for (const owner of entry.owners) {
      owners.add(owner);
    }
  }
  return Array.from(owners).sort((a, b) => a.localeCompare(b, 'ru'));
}

function collectSurfaces(entries: SiteBlockLibraryEntry[]): BlockSurface[] {
  const surfaces = new Set<BlockSurface>();
  for (const entry of entries) {
    for (const surface of entry.surfaces) {
      surfaces.add(surface);
    }
  }
  return Array.from(surfaces).sort((a, b) => SURFACE_LABELS[a].localeCompare(SURFACE_LABELS[b], 'ru'));
}

function collectLocales(entries: SiteBlockLibraryEntry[]): BlockLocale[] {
  const locales = new Set<BlockLocale>();
  for (const entry of entries) {
    for (const locale of entry.locales) {
      locales.add(locale);
    }
  }
  return Array.from(locales).sort((a, b) => LOCALE_LABELS[a].localeCompare(LOCALE_LABELS[b], 'ru'));
}

const OWNER_OPTIONS = collectOwners(SITE_BLOCK_LIBRARY);
const SURFACE_OPTIONS = collectSurfaces(SITE_BLOCK_LIBRARY);
const LOCALE_OPTIONS = collectLocales(SITE_BLOCK_LIBRARY);
const CATEGORY_OPTIONS = Array.from(new Set<BlockCategory>(SITE_BLOCK_LIBRARY.map((entry) => entry.category))).sort(
  (a, b) => CATEGORY_LABELS[a].localeCompare(CATEGORY_LABELS[b], 'ru'),
);
const SOURCE_OPTIONS = Array.from(
  new Set<BlockSourceMode>(SITE_BLOCK_LIBRARY.flatMap((entry) => entry.sources)),
).sort((a, b) => SOURCE_LABELS[a].localeCompare(SOURCE_LABELS[b], 'ru'));

function matchesFilter<T>(value: FilterValue<T>, list: T[], predicate: (item: T) => boolean): boolean {
  if (value === 'all') return true;
  return list.some((item) => predicate(item));
}

function normalize(text: string): string {
  return text.normalize('NFKC').toLowerCase();
}

function blockMatchesSearch(entry: SiteBlockLibraryEntry, search: string): boolean {
  if (!search) return true;
  const haystack = [
    entry.label,
    entry.description,
    entry.id,
    entry.statusNote ?? '',
    entry.owners.join(' '),
    entry.surfaces.map((surface) => SURFACE_LABELS[surface]).join(' '),
    entry.sources.map((source) => SOURCE_LABELS[source]).join(' '),
    entry.keywords?.join(' ') ?? '',
  ]
    .map(normalize)
    .join(' ');
  return haystack.includes(normalize(search));
}

function sortEntries(a: SiteBlockLibraryEntry, b: SiteBlockLibraryEntry): number {
  const statusDiff = statusOrder[a.status] - statusOrder[b.status];
  if (statusDiff !== 0) {
    return statusDiff;
  }
  return a.label.localeCompare(b.label, 'ru');
}

function addBlock(
  type: HomeBlockType,
  blocks: HomeBlock[],
  setBlocks: (next: HomeBlock[]) => void,
  selectBlock: (blockId: string | null) => void,
) {
  const fresh = createBlockInstance(type, blocks);
  setBlocks([...blocks, fresh]);
  selectBlock(fresh.id);
}

function BlockPreview({ kind, status }: { kind: BlockPreviewKind; status: SiteBlockLibraryEntry['status'] }) {
  const containerCls = [
    'relative h-28 w-full overflow-hidden rounded-xl border border-gray-200 bg-white shadow-inner dark:border-dark-600 dark:bg-dark-700',
    status === 'available' ? '' : 'opacity-80',
  ]
    .filter(Boolean)
    .join(' ');

  switch (kind) {
    case 'hero':
      return (
        <div className={containerCls}>
          <div className="absolute inset-0 bg-gradient-to-br from-primary-100 via-primary-50 to-white dark:from-primary-900/50 dark:via-dark-700 dark:to-dark-700" />
          <div className="relative flex h-full w-full flex-col justify-end gap-2 p-4">
            <div className="h-3 w-2/3 rounded bg-white/90 dark:bg-dark-500" />
            <div className="h-2 w-1/2 rounded bg-white/70 dark:bg-dark-400" />
            <div className="flex gap-2 pt-1">
              <div className="h-7 w-24 rounded-lg bg-primary-500/90 dark:bg-primary-400/90" />
              <div className="h-7 w-16 rounded-lg border border-white/70 dark:border-dark-400" />
            </div>
          </div>
        </div>
      );
    case 'list':
      return (
        <div className={containerCls}>
          <div className="absolute inset-0 bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-dark-700 dark:via-dark-700 dark:to-dark-600" />
          <div className="relative flex h-full w-full flex-col gap-2 p-4">
            {[0, 1, 2].map((index) => (
              <div key={index} className="flex items-center gap-2">
                <div className="h-10 w-10 rounded-md bg-primary-200/70 dark:bg-primary-900/40" />
                <div className="flex-1 space-y-1">
                  <div className="h-2.5 w-2/3 rounded bg-gray-300/80 dark:bg-dark-400" />
                  <div className="h-2 w-1/2 rounded bg-gray-200/70 dark:bg-dark-500" />
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    case 'carousel':
      return (
        <div className={containerCls}>
          <div className="absolute inset-0 bg-gradient-to-r from-white via-primary-50 to-white dark:from-dark-700 dark:via-primary-950/30 dark:to-dark-700" />
          <div className="relative flex h-full items-center gap-2 px-4">
            {[0, 1, 2].map((index) => (
              <div
                key={index}
                className="flex h-20 w-20 flex-shrink-0 flex-col justify-between rounded-xl border border-white/70 bg-white/90 p-2 shadow-sm dark:border-dark-500 dark:bg-dark-600/90"
              >
                <div className="h-3 w-3/4 rounded bg-primary-500/50 dark:bg-primary-400/70" />
                <div className="h-2 w-full rounded bg-gray-200/80 dark:bg-dark-400" />
              </div>
            ))}
          </div>
        </div>
      );
    case 'custom':
      return (
        <div className={containerCls}>
          <div className="absolute inset-0 bg-gradient-to-br from-rose-50 via-white to-amber-50 dark:from-rose-950/50 dark:via-dark-700 dark:to-amber-900/40" />
          <div className="relative flex h-full items-center gap-2 px-4">
            {[0, 1, 2].map((index) => (
              <div
                key={index}
                className="flex h-20 w-20 flex-shrink-0 flex-col justify-between rounded-xl border border-rose-200/80 bg-white/90 p-2 shadow-sm dark:border-rose-900/40 dark:bg-dark-600/80"
              >
                <div className="h-3 w-3/4 rounded bg-rose-400/70 dark:bg-rose-500/70" />
                <div className="h-2 w-2/3 rounded bg-amber-300/80 dark:bg-amber-400/70" />
              </div>
            ))}
          </div>
        </div>
      );
    case 'personalized':
      return (
        <div className={containerCls}>
          <div className="absolute inset-0 bg-gradient-to-br from-sky-50 via-white to-emerald-50 dark:from-sky-950/40 dark:via-dark-700 dark:to-emerald-900/40" />
          <div className="relative flex h-full flex-col gap-2 p-4">
            <div className="flex items-center gap-2">
              <div className="h-3 w-20 rounded bg-sky-400/80 dark:bg-sky-500/70" />
              <div className="h-3 w-16 rounded bg-emerald-300/80 dark:bg-emerald-400/70" />
              <div className="h-3 w-12 rounded bg-purple-300/80 dark:bg-purple-400/70" />
            </div>
            <div className="flex gap-2">
              {[0, 1, 2].map((index) => (
                <div key={index} className="flex h-14 flex-1 flex-col justify-between rounded-lg bg-white/80 p-2 dark:bg-dark-500/70">
                  <div className="h-2.5 w-2/3 rounded bg-sky-400/70 dark:bg-sky-500/70" />
                  <div className="h-2 w-1/2 rounded bg-emerald-400/70 dark:bg-emerald-500/70" />
                </div>
              ))}
            </div>
          </div>
        </div>
      );
    case 'header':
      return (
        <div className={containerCls}>
          <div className="absolute inset-x-0 top-0 h-10 bg-gradient-to-r from-primary-500 to-primary-600 dark:from-primary-700 dark:to-primary-500" />
          <div className="relative flex h-full flex-col justify-end gap-2 p-4">
            <div className="flex gap-2">
              <div className="h-2 w-12 rounded bg-primary-100/90 dark:bg-primary-200/90" />
              <div className="h-2 w-10 rounded bg-primary-100/80 dark:bg-primary-200/80" />
              <div className="h-2 w-14 rounded bg-primary-100/70 dark:bg-primary-200/70" />
            </div>
            <div className="h-2 w-1/3 rounded bg-gray-200/60 dark:bg-dark-400" />
          </div>
        </div>
      );
    case 'footer':
      return (
        <div className={containerCls}>
          <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-800 to-gray-700 dark:from-dark-800 dark:via-dark-700 dark:to-dark-600" />
          <div className="relative flex h-full flex-col justify-between gap-3 p-4 text-white/80">
            <div className="h-4 w-32 rounded bg-white/40" />
            <div className="space-y-1">
              <div className="h-2 w-3/4 rounded bg-white/30" />
              <div className="h-2 w-1/2 rounded bg-white/20" />
            </div>
            <div className="flex gap-2">
              <div className="h-2 w-12 rounded bg-white/20" />
              <div className="h-2 w-10 rounded bg-white/20" />
              <div className="h-2 w-16 rounded bg-white/20" />
            </div>
          </div>
        </div>
      );
    case 'faq':
      return (
        <div className={containerCls}>
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-50 via-white to-emerald-100 dark:from-emerald-950/40 dark:via-dark-700 dark:to-emerald-900/40" />
          <div className="relative flex h-full flex-col gap-3 p-4">
            {[0, 1].map((index) => (
              <div key={index} className="space-y-2 rounded-lg bg-white/90 p-3 shadow-sm dark:bg-dark-600/80">
                <div className="h-2.5 w-2/3 rounded bg-emerald-400/60 dark:bg-emerald-400/70" />
                <div className="space-y-1">
                  <div className="h-2 w-full rounded bg-gray-200/80 dark:bg-dark-400" />
                  <div className="h-2 w-4/5 rounded bg-gray-200/60 dark:bg-dark-500" />
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    case 'promo':
      return (
        <div className={containerCls}>
          <div className="absolute inset-0 bg-gradient-to-br from-amber-50 via-white to-rose-50 dark:from-amber-900/40 dark:via-dark-700 dark:to-rose-900/40" />
          <div className="relative flex h-full w-full flex-col justify-between gap-2 p-4">
            <div className="h-16 rounded-lg bg-gradient-to-r from-rose-400/80 to-amber-300/80 dark:from-rose-500/60 dark:to-amber-400/60" />
            <div className="flex justify-between">
              <div className="h-3 w-1/3 rounded bg-gray-200/80 dark:bg-dark-400" />
              <div className="h-7 w-20 rounded-lg bg-primary-500/80 dark:bg-primary-400/80" />
            </div>
          </div>
        </div>
      );
    case 'metrics':
    default:
      return (
        <div className={containerCls}>
          <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-white to-emerald-50 dark:from-indigo-950/40 dark:via-dark-700 dark:to-emerald-900/40" />
          <div className="relative grid h-full grid-cols-3 gap-2 p-4">
            {[0, 1, 2].map((index) => (
              <div
                key={index}
                className="flex flex-col justify-center gap-2 rounded-lg bg-white/90 p-2 text-center shadow-sm dark:bg-dark-600/80"
              >
                <div className="mx-auto h-2 w-3/4 rounded bg-indigo-400/70 dark:bg-indigo-500/70" />
                <div className="mx-auto h-4 w-full rounded-md bg-emerald-400/80 dark:bg-emerald-500/70" />
              </div>
            ))}
          </div>
        </div>
      );
  }
}

type BlockCardProps = {
  entry: SiteBlockLibraryEntry;
  onAdd: (type: HomeBlockType) => void;
  saving: boolean;
};

function BlockCard({ entry, onAdd, saving }: BlockCardProps): React.ReactElement {
  const isAvailable = entry.status === 'available';
  const statusMeta = STATUS_LABELS[entry.status];
  const locale = entry.locales.includes('ru') ? 'ru' : entry.locales[0] ?? 'ru';
  const { data: previewData, loading: previewLoading, error: previewError } = useBlockPreview(entry.id, {
    locale,
    useLive: entry.status === 'available',
  });
  const previewSource = previewData?.source ?? (previewData ? 'mock' : 'error');
  const previewBadge =
    previewSource === 'live'
      ? { label: 'Live', color: 'success' as const }
      : previewSource === 'mock'
        ? { label: 'Mock', color: 'warning' as const }
        : previewSource === 'fallback'
          ? { label: 'Fallback', color: 'warning' as const }
          : { label: previewSource, color: 'neutral' as const };
  const previewMeta = previewData?.meta as Record<string, unknown> | undefined;
  const previewReason = typeof previewMeta?.reason === 'string' ? previewMeta.reason : null;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white/95 shadow-sm transition hover:border-primary-200 hover:shadow-md dark:border-dark-600 dark:bg-dark-700/80 dark:hover:border-primary-600/40">
        <div className="space-y-4 p-4">
          <BlockPreview kind={entry.preview} status={entry.status} />

          <div className="space-y-3">
          <div className="flex items-start justify-between gap-2">
            <div className="space-y-1">
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white">{entry.label}</h4>
              <p className="text-xs leading-4 text-gray-500 dark:text-dark-200">{entry.description}</p>
            </div>
            {statusMeta ? (
              <Badge color={statusMeta.color} variant="soft">
                {statusMeta.label}
              </Badge>
            ) : null}
          </div>

          {entry.statusNote ? <p className="text-xs text-gray-500 dark:text-dark-200">{entry.statusNote}</p> : null}

          <div className="flex flex-wrap gap-1.5">
            <Tag color="primary">{CATEGORY_LABELS[entry.category]}</Tag>
            {entry.sources.map((source) => (
              <Tag key={`${entry.id}-source-${source}`} color="sky">
                {SOURCE_LABELS[source]}
              </Tag>
            ))}
            {entry.locales.map((locale) => (
              <Tag key={`${entry.id}-locale-${locale}`} color="emerald">
                {LOCALE_LABELS[locale]}
              </Tag>
            ))}
          </div>

          <div className="flex flex-wrap gap-1.5">
            {entry.surfaces.map((surface) => (
              <Tag key={`${entry.id}-surface-${surface}`}>{SURFACE_LABELS[surface]}</Tag>
            ))}
          </div>

          <div className="flex flex-wrap gap-1.5">
            {entry.owners.map((owner) => (
              <Tag key={`${entry.id}-owner-${owner}`} color="gray">
                {owner}
              </Tag>
            ))}
          </div>

          <div className="space-y-2 rounded-xl border border-gray-200/80 bg-gray-50/70 p-3 text-xs text-gray-600 dark:border-dark-600/60 dark:bg-dark-700/40 dark:text-dark-100">
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold text-gray-700 dark:text-dark-50">Предпросмотр данных</span>
              <Badge color={previewBadge.color} className="text-[11px]">
                {previewBadge.label}
              </Badge>
            </div>
            {previewLoading ? (
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
                <Spinner className="h-3.5 w-3.5" />
                Загружаем примеры...
              </div>
            ) : previewError ? (
              <div className="rounded-md border border-rose-300 bg-rose-50 px-2 py-1 text-xs text-rose-600 dark:border-rose-600/60 dark:bg-rose-950/40 dark:text-rose-200">
                {previewError}
              </div>
            ) : previewData && previewData.items.length ? (
              <ul className="space-y-1.5">
                {previewData.items.slice(0, 3).map((item, index) => (
                  <li key={`${entry.id}-preview-${index}`} className="flex gap-2">
                    <span className="mt-0.5 text-[10px] font-semibold text-gray-400 dark:text-dark-300">{index + 1}.</span>
                    <div className="min-w-0">
                      <div className="truncate text-xs font-medium text-gray-800 dark:text-dark-50">{item.title}</div>
                      {item.subtitle ? (
                        <div className="truncate text-[11px] text-gray-500 dark:text-dark-200">{item.subtitle}</div>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="space-y-1 text-xs text-gray-500 dark:text-dark-200">
                <div>Ничего не найдено для предпросмотра.</div>
                {previewReason ? <div className="text-[11px] text-gray-400 dark:text-dark-300">{previewReason}</div> : null}
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              aria-label={
                isAvailable
                  ? `Добавить блок ${entry.label}`
                  : `Блок ${entry.label} скоро будет доступен`
              }
              onClick={() => {
                if (isAvailable && 'type' in entry) {
                  onAdd(entry.type);
                }
              }}
              disabled={!isAvailable || saving}
              className="flex-1"
            >
              {isAvailable ? (
                <span className="flex items-center justify-center gap-2">
                  <Plus className="h-4 w-4" />
                  Добавить блок
                </span>
              ) : (
                <span>Скоро</span>
              )}
            </Button>
            {entry.documentationUrl ? (
              <Button
                as="a"
                href={entry.documentationUrl}
                target="_blank"
                rel="noreferrer"
                variant="outlined"
                color="neutral"
                size="sm"
                className="flex items-center gap-1"
                aria-label={`Документация по блоку ${entry.label}`}
              >
                <ExternalLink className="h-3.5 w-3.5" />
                Документация
              </Button>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

export function SiteBlockLibraryPanel(): React.ReactElement {
  const { data, setBlocks, selectBlock, saving } = useHomeEditorContext();
  const [filters, setFilters] = React.useState<FiltersState>(INITIAL_FILTERS);

  const handleFilterChange = <Key extends keyof FiltersState>(key: Key, value: FiltersState[Key]) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const resetFilters = React.useCallback(() => {
    setFilters(INITIAL_FILTERS);
  }, []);

  const filteredEntries = React.useMemo(() => {
    return SITE_BLOCK_LIBRARY.filter((entry) => {
      if (!blockMatchesSearch(entry, filters.search)) {
        return false;
      }
      if (filters.category !== 'all' && entry.category !== filters.category) {
        return false;
      }
      if (!matchesFilter(filters.source, entry.sources, (source) => source === filters.source)) {
        return false;
      }
      if (!matchesFilter(filters.surface, entry.surfaces, (surface) => surface === filters.surface)) {
        return false;
      }
      if (!matchesFilter(filters.owner, entry.owners, (owner) => owner === filters.owner)) {
        return false;
      }
      if (!matchesFilter(filters.locale, entry.locales, (locale) => locale === filters.locale)) {
        return false;
      }
      return true;
    }).sort(sortEntries);
  }, [filters.category, filters.locale, filters.owner, filters.search, filters.source, filters.surface]);

  const availableCount = filteredEntries.filter((entry) => entry.status === 'available').length;
  const hasFiltersActive = React.useMemo(() => {
    if (filters.search.trim().length > 0) return true;
    return (
      filters.category !== 'all' ||
      filters.source !== 'all' ||
      filters.surface !== 'all' ||
      filters.owner !== 'all' ||
      filters.locale !== 'all'
    );
  }, [filters]);

  const onAddBlock = React.useCallback(
    (type: HomeBlockType) => {
      addBlock(type, data.blocks, setBlocks, selectBlock);
    },
    [data.blocks, selectBlock, setBlocks],
  );

  return (
    <Card padding="sm" className="flex h-full flex-col gap-4">
      <div className="space-y-2">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
          <ListFilter className="h-4 w-4 text-primary-500" />
          Библиотека блоков
        </h3>
        <p className="text-xs leading-4 text-gray-500 dark:text-dark-200">
          Подберите блок по категории, источникам данных и назначению. Фильтры и поиск помогут найти нужный шаблон.
        </p>
      </div>

      <div className="space-y-3">
        <Input
          value={filters.search}
          onChange={(event) => handleFilterChange('search', event.target.value)}
          placeholder="Поиск по названию, источнику или владельцу"
          prefix={<Search className="h-4 w-4" />}
        />

        <Select
          value={filters.category}
          onChange={(event) => handleFilterChange('category', event.target.value as FilterValue<BlockCategory>)}
        >
          <option value="all">Все категории</option>
          {CATEGORY_OPTIONS.map((category) => (
            <option key={category} value={category}>
              {CATEGORY_LABELS[category]}
            </option>
          ))}
        </Select>

        <Select
          value={filters.source}
          onChange={(event) => handleFilterChange('source', event.target.value as FilterValue<BlockSourceMode>)}
        >
          <option value="all">Любой источник данных</option>
          {SOURCE_OPTIONS.map((source) => (
            <option key={source} value={source}>
              {SOURCE_LABELS[source]}
            </option>
          ))}
        </Select>

        <Select
          value={filters.surface}
          onChange={(event) => handleFilterChange('surface', event.target.value as FilterValue<BlockSurface>)}
        >
          <option value="all">Любые страницы</option>
          {SURFACE_OPTIONS.map((surface) => (
            <option key={surface} value={surface}>
              {SURFACE_LABELS[surface]}
            </option>
          ))}
        </Select>

        <Select
          value={filters.owner}
          onChange={(event) => handleFilterChange('owner', event.target.value as FilterValue<string>)}
        >
          <option value="all">Все владельцы</option>
          {OWNER_OPTIONS.map((owner) => (
            <option key={owner} value={owner}>
              {owner}
            </option>
          ))}
        </Select>

        <Select
          value={filters.locale}
          onChange={(event) => handleFilterChange('locale', event.target.value as FilterValue<BlockLocale>)}
        >
          <option value="all">Любые локали</option>
          {LOCALE_OPTIONS.map((locale) => (
            <option key={locale} value={locale}>
              {LOCALE_LABELS[locale]}
            </option>
          ))}
        </Select>

        <div className="flex items-center justify-between text-xs text-gray-500 dark:text-dark-200">
          <span>
            Найдено {filteredEntries.length} блоков · доступно {availableCount}
          </span>
          {hasFiltersActive ? (
            <Button variant="ghost" color="neutral" size="xs" onClick={resetFilters}>
              Сбросить
            </Button>
          ) : null}
        </div>
      </div>

      <div className="scrollbar-thin -mr-2 flex-1 space-y-3 overflow-y-auto pr-1">
        {filteredEntries.length === 0 ? (
          <div className="flex h-40 items-center justify-center rounded-2xl border border-dashed border-gray-200 text-center text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
            По выбранным условиям блоков не найдено. Попробуйте изменить фильтры.
          </div>
        ) : (
          filteredEntries.map((entry) => (
            <BlockCard key={entry.id} entry={entry} onAdd={onAddBlock} saving={saving} />
          ))
        )}
      </div>
    </Card>
  );
}

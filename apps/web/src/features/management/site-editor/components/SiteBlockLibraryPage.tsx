import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge, Button, Card, Input, Select, Tag } from '@ui';
import { ExternalLink, Search } from '@icons';
import { useAuth } from '@shared/auth';
import type { CreateSiteGlobalBlockPayload } from '@shared/api/management/siteEditor/types';
import {
  CATEGORY_LABELS,
  LOCALE_LABELS,
  SITE_BLOCK_LIBRARY,
  SOURCE_LABELS,
  STATUS_LABELS,
  SURFACE_LABELS,
  type BlockCategory,
  type BlockLocale,
  type BlockSourceMode,
  type BlockSurface,
  type SiteBlockLibraryEntry,
} from '../blockLibraryData';

type FilterValue<T> = T | 'all';

type FiltersState = {
  search: string;
  status: FilterValue<SiteBlockLibraryEntry['status']>;
  category: FilterValue<BlockCategory>;
  source: FilterValue<BlockSourceMode>;
  surface: FilterValue<BlockSurface>;
  owner: FilterValue<string>;
  locale: FilterValue<BlockLocale>;
};

const INITIAL_FILTERS: FiltersState = {
  search: '',
  status: 'all',
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
  entries.forEach((entry) => entry.owners.forEach((owner) => owners.add(owner)));
  return Array.from(owners).sort((a, b) => a.localeCompare(b, 'ru'));
}

function collectSurfaces(entries: SiteBlockLibraryEntry[]): BlockSurface[] {
  const surfaces = new Set<BlockSurface>();
  entries.forEach((entry) => entry.surfaces.forEach((surface) => surfaces.add(surface)));
  return Array.from(surfaces).sort((a, b) => SURFACE_LABELS[a].localeCompare(SURFACE_LABELS[b], 'ru'));
}

function collectLocales(entries: SiteBlockLibraryEntry[]): BlockLocale[] {
  const locales = new Set<BlockLocale>();
  entries.forEach((entry) => entry.locales.forEach((locale) => locales.add(locale)));
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
const STATUS_OPTIONS = (Object.keys(statusOrder) as SiteBlockLibraryEntry['status'][]).sort(
  (a, b) => statusOrder[a] - statusOrder[b],
);

function matchesFilter<T>(value: FilterValue<T>, list: T[], predicate: (item: T) => boolean): boolean {
  if (value === 'all') return true;
  return list.some((item) => predicate(item));
}

function normalize(text: string): string {
  return text.normalize('NFKC').toLowerCase();
}

function blockMatchesSearch(entry: SiteBlockLibraryEntry, search: string): boolean {
  if (!search.trim()) {
    return true;
  }
  const normalized = normalize(search);
  const haystack = [
    entry.label,
    entry.description,
    entry.id,
    'type' in entry ? entry.type : '',
    ...entry.owners,
    ...entry.surfaces.map((surface) => SURFACE_LABELS[surface]),
    ...entry.sources.map((source) => SOURCE_LABELS[source]),
    ...(entry.keywords ?? []),
  ].map(normalize).join(' ');
  return haystack.includes(normalized);
}

type TemplateNavigationState = {
  id: string;
  label: string;
  locale: string | null;
  documentationUrl: string | null;
  note: string | null;
  defaults: CreateSiteGlobalBlockPayload;
};

function makeGlobalBlockKey(prefix: string): string {
  const normalized =
    prefix
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9_-]+/g, '-')
      .replace(/^-+|-+$/g, '') || 'block';
  const suffix = Date.now().toString(36);
  return `${normalized}-${suffix}`;
}

type LibraryCardProps = {
  entry: SiteBlockLibraryEntry;
  canCreate: boolean;
  onCreate?: (entry: SiteBlockLibraryEntry) => void;
};

function LibraryCard({ entry, canCreate, onCreate }: LibraryCardProps): React.ReactElement {
  const statusMeta = STATUS_LABELS[entry.status];
  const surfaces = entry.surfaces.map((surface) => SURFACE_LABELS[surface]).join(', ');
  const sources = entry.sources.map((source) => SOURCE_LABELS[source]).join(', ');
  const locales = entry.locales.map((locale) => LOCALE_LABELS[locale]).join(', ');
  const showTemplateCta = Boolean(entry.globalTemplate && onCreate);
  const templateMessage =
    entry.globalTemplate?.note ?? entry.statusNote ?? 'Создайте глобальный блок на основе шаблона.';

  return (
    <Card padding="sm" className="flex flex-col gap-4 bg-white/95 shadow-sm dark:bg-dark-800/80">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="text-2xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">
            {CATEGORY_LABELS[entry.category]}
          </div>
          <h3 className="text-base font-semibold text-gray-900 dark:text-white">{entry.label}</h3>
          <p className="text-sm text-gray-600 dark:text-dark-200">{entry.description}</p>
        </div>
        <Badge color={statusMeta.color} variant="soft">
          {statusMeta.label}
        </Badge>
      </div>

      <div className="grid gap-3 text-xs text-gray-600 dark:text-dark-200 sm:grid-cols-2 lg:grid-cols-3">
        {'type' in entry ? (
          <div className="space-y-1 rounded-xl bg-gray-50/80 px-3 py-2 dark:bg-dark-700/50">
            <div className="text-2xs font-semibold uppercase tracking-wide text-gray-400 dark:text-dark-300">Тип блокa</div>
            <div className="font-mono text-[11px] text-gray-700 dark:text-dark-50">{entry.type}</div>
          </div>
        ) : null}
        <div className="space-y-1 rounded-xl bg-gray-50/80 px-3 py-2 dark:bg-dark-700/50">
          <div className="text-2xs font-semibold uppercase tracking-wide text-gray-400 dark:text-dark-300">Источники</div>
          <div>{sources}</div>
        </div>
        <div className="space-y-1 rounded-xl bg-gray-50/80 px-3 py-2 dark:bg-dark-700/50">
          <div className="text-2xs font-semibold uppercase tracking-wide text-gray-400 dark:text-dark-300">Поверхности</div>
          <div>{surfaces}</div>
        </div>
        <div className="space-y-1 rounded-xl bg-gray-50/80 px-3 py-2 dark:bg-dark-700/50">
          <div className="text-2xs font-semibold uppercase tracking-wide text-gray-400 dark:text-dark-300">Локали</div>
          <div>{locales}</div>
        </div>
        <div className="space-y-1 rounded-xl bg-gray-50/80 px-3 py-2 dark:bg-dark-700/50">
          <div className="text-2xs font-semibold uppercase tracking-wide text-gray-400 dark:text-dark-300">Владельцы</div>
          <div>{entry.owners.join(', ')}</div>
        </div>
        {entry.keywords?.length ? (
          <div className="space-y-1 rounded-xl bg-gray-50/80 px-3 py-2 dark:bg-dark-700/50">
            <div className="text-2xs font-semibold uppercase tracking-wide text-gray-400 dark:text-dark-300">Ключевые слова</div>
            <div className="flex flex-wrap gap-1">
              {entry.keywords.map((keyword) => (
                <Tag key={keyword} color="gray">
                  {keyword}
                </Tag>
              ))}
            </div>
          </div>
        ) : null}
      </div>

      {entry.statusNote ? (
        <div className="rounded-xl border border-amber-200/60 bg-amber-50/70 px-3 py-2 text-xs text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
          {entry.statusNote}
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-2">
        {entry.documentationUrl ? (
          <Button
            as="a"
            href={entry.documentationUrl}
            target="_blank"
            rel="noreferrer"
            variant="outlined"
            color="neutral"
            size="sm"
            className="flex items-center gap-2"
          >
            <ExternalLink className="h-4 w-4" />
            Документация
          </Button>
        ) : null}
        {'type' in entry ? (
          <Tag color="primary">ID: {entry.id}</Tag>
        ) : (
          <Tag color="amber">Планируется: {entry.id}</Tag>
        )}
      </div>

      {showTemplateCta ? (
        <div className="flex flex-col gap-2 rounded-xl border border-primary-200/70 bg-primary-50/70 px-3 py-2 text-xs text-primary-800 dark:border-primary-500/30 dark:bg-primary-500/10 dark:text-primary-100 md:flex-row md:items-center md:justify-between">
          <div className="flex-1">{templateMessage}</div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              disabled={!canCreate}
              onClick={() => onCreate?.(entry)}
            >
              Создать глобальный блок
            </Button>
            {!canCreate ? (
              <span className="text-[11px] text-primary-500/70 dark:text-primary-200/70">Недостаточно прав</span>
            ) : null}
          </div>
        </div>
      ) : null}
    </Card>
  );
}

export default function SiteBlockLibraryPage(): React.ReactElement {
  const [filters, setFilters] = React.useState<FiltersState>(INITIAL_FILTERS);
  const { user } = useAuth();
  const navigate = useNavigate();

  const roles = React.useMemo(() => {
    const set = new Set<string>();
    if (Array.isArray(user?.roles)) {
      user.roles.forEach((role) => {
        if (role) {
          set.add(String(role));
        }
      });
    }
    if (user?.role) {
      set.add(String(user.role));
    }
    return set;
  }, [user]);

  const canCreateGlobalBlock = React.useMemo(
    () =>
      roles.has('site.editor') ||
      roles.has('site.publisher') ||
      roles.has('site.admin') ||
      roles.has('platform.admin') ||
      roles.has('admin') ||
      roles.has('moderator'),
    [roles],
  );

  const handleFilterChange = <Key extends keyof FiltersState>(key: Key, value: FiltersState[Key]) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const resetFilters = React.useCallback(() => {
    setFilters(INITIAL_FILTERS);
  }, []);

  const buildTemplatePayload = React.useCallback(
    (entry: SiteBlockLibraryEntry): TemplateNavigationState | null => {
      const template = entry.globalTemplate;
      if (!template) {
        return null;
      }
      const key = makeGlobalBlockKey(template.keyPrefix || entry.id);
      const payload: CreateSiteGlobalBlockPayload = {
        key,
        title: template.title ?? entry.label,
        section: template.section,
        locale: template.defaultLocale ?? entry.locales[0] ?? 'ru',
        requires_publisher: template.requiresPublisher ?? true,
      };
      if (template.data) {
        payload.data = JSON.parse(JSON.stringify(template.data));
      }
      const meta: Record<string, unknown> = {
        template_entry_id: entry.id,
        template_label: entry.label,
      };
      if (template.meta) {
        Object.assign(meta, JSON.parse(JSON.stringify(template.meta)));
      }
      payload.meta = meta;
      return {
        id: entry.id,
        label: entry.label,
        locale: template.defaultLocale ?? entry.locales[0] ?? null,
        documentationUrl: entry.documentationUrl ?? null,
        note: template.note ?? entry.statusNote ?? null,
        defaults: payload,
      };
    },
    [],
  );

  const handleCreateGlobalBlock = React.useCallback(
    (entry: SiteBlockLibraryEntry) => {
      if (!canCreateGlobalBlock || !entry.globalTemplate) {
        return;
      }
      const templateState = buildTemplatePayload(entry);
      if (!templateState) {
        return;
      }
      navigate('/management/site-editor/global-blocks/new', {
        state: {
          template: templateState,
        },
        replace: false,
      });
    },
    [buildTemplatePayload, canCreateGlobalBlock, navigate],
  );

  const filteredEntries = React.useMemo(() => {
    return SITE_BLOCK_LIBRARY.filter((entry) => {
      if (!blockMatchesSearch(entry, filters.search)) {
        return false;
      }
      if (filters.status !== 'all' && entry.status !== filters.status) {
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
    }).sort((a, b) => {
      const statusDiff = statusOrder[a.status] - statusOrder[b.status];
      if (statusDiff !== 0) {
        return statusDiff;
      }
      return a.label.localeCompare(b.label, 'ru');
    });
  }, [filters]);

  const hasActiveFilters = React.useMemo(() => {
    if (filters.search.trim().length > 0) return true;
    return ['status', 'category', 'source', 'surface', 'owner', 'locale'].some((key) => filters[key as keyof FiltersState] !== 'all');
  }, [filters]);

  return (
    <div className="space-y-6" data-testid="site-block-library-page">
      <header className="space-y-2">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Библиотека блоков</h1>
        <p className="text-sm text-gray-600 dark:text-dark-200">
          Страница со всеми шаблонами блоков, статусами реализации и ответственными командами. Используйте фильтры,
          чтобы подобрать подходящий блок для конкретной поверхности или аудитории.
        </p>
      </header>

      <Card padding="sm" className="space-y-3 bg-white/95 shadow-sm dark:bg-dark-800/80">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <Input
            value={filters.search}
            onChange={(event) => handleFilterChange('search', event.target.value)}
            placeholder="Поиск по названию, ID, владельцу или ключевому слову"
            prefix={<Search className="h-4 w-4 text-gray-400" />}
            className="sm:col-span-2 xl:col-span-3"
          />
          <Select
            value={filters.status}
            onChange={(event) => handleFilterChange('status', event.target.value as FilterValue<SiteBlockLibraryEntry['status']>)}
          >
            <option value="all">Любой статус</option>
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {STATUS_LABELS[status].label}
              </option>
            ))}
          </Select>
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
            <option value="all">Любой источник</option>
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
            <option value="all">Любые поверхности</option>
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
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500 dark:text-dark-200">
          <span>Найдено {filteredEntries.length} блоков из {SITE_BLOCK_LIBRARY.length}</span>
          {hasActiveFilters ? (
            <Button variant="ghost" color="neutral" size="xs" onClick={resetFilters}>
              Сбросить фильтры
            </Button>
          ) : null}
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {filteredEntries.length === 0 ? (
          <div className="col-span-full flex h-48 items-center justify-center rounded-3xl border border-dashed border-gray-200 bg-gray-50 text-center text-sm text-gray-500 dark:border-dark-600 dark:bg-dark-800/60 dark:text-dark-200">
            По выбранным условиям блоков не найдено. Попробуйте изменить фильтры или поиск.
          </div>
        ) : (
          filteredEntries.map((entry) => (
            <LibraryCard
              key={entry.id}
              entry={entry}
              canCreate={canCreateGlobalBlock}
              onCreate={entry.globalTemplate ? handleCreateGlobalBlock : undefined}
            />
          ))
        )}
      </div>
    </div>
  );
}

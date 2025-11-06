import React from 'react';
import { Search } from '@icons';
import { Button, Card, Input, Select, Spinner, useToast } from '@ui';
import { managementSiteEditorApi } from '@shared/api/management';
import type { SiteBlock, SiteBlockStatus } from '@shared/types/management';
import type { CreateSiteBlockPayload } from '@shared/api/management/siteEditor/types';
import { extractErrorMessage } from '@shared/utils/errors';
import {
  BLOCKS_PAGE_SIZE,
  REVIEW_STATUS_OPTIONS,
  SCOPE_LABELS,
  STATUS_META,
} from './SiteBlockLibraryPage.constants';
import { SiteBlockCreateDialog } from './SiteBlockCreateDialog';
import SiteBlockDetailPanel from './SiteBlockDetailPanel';
import { SiteBlockListItem, sortBlocksForList } from './SiteBlockListItem';
import { filterBlocks, pickOwner, collectLocales } from './SiteBlockLibrary.utils';
import type { FiltersState } from './SiteBlockLibrary.types';

const INITIAL_FILTERS: FiltersState = {
  search: '',
  status: 'all',
  scope: 'all',
  locale: 'all',
  owner: 'all',
  requiresPublisher: 'all',
  reviewStatus: 'all',
};
export default function SiteBlockLibraryPage(): React.ReactElement {
  const [filters, setFilters] = React.useState<FiltersState>(INITIAL_FILTERS);
  const [blocks, setBlocks] = React.useState<SiteBlock[]>([]);
  const [total, setTotal] = React.useState<number | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [refreshKey, setRefreshKey] = React.useState(0);
  const [selectedBlockId, setSelectedBlockId] = React.useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
  const { pushToast } = useToast();

  React.useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    managementSiteEditorApi
      .fetchSiteBlocks(
        { pageSize: BLOCKS_PAGE_SIZE, sort: 'updated_at_desc', isTemplate: false },
        { signal: controller.signal },
      )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        setBlocks(Array.isArray(response.items) ? response.items : []);
        setTotal(typeof response.total === 'number' ? response.total : null);
      })
      .catch((err) => {
        if ((err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setError(extractErrorMessage(err, 'Не удалось загрузить блоки'));
        setBlocks([]);
        setTotal(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [refreshKey]);
  const ownerOptions = React.useMemo(() => {
    const owners = new Set<string>();
    blocks.forEach((block) => {
      const owner = pickOwner(block);
      if (owner) {
        owners.add(owner);
      }
    });
    return Array.from(owners).sort((a, b) => a.localeCompare(b, 'ru'));
  }, [blocks]);

  const localeOptions = React.useMemo(() => {
    const locales = new Set<string>();
    blocks.forEach((block) => {
      collectLocales(block).forEach((locale) => locales.add(locale));
    });
    return Array.from(locales).sort((a, b) => a.localeCompare(b, 'ru'));
  }, [blocks]);

  const scopeOptions = React.useMemo(() => {
    const scopes = new Set<string>();
    blocks.forEach((block) => scopes.add(block.scope ?? 'unknown'));
    return Array.from(scopes).sort((a, b) => a.localeCompare(b, 'ru'));
  }, [blocks]);

  const filteredBlocks = React.useMemo(() => {
    const list = filterBlocks(blocks, filters);
    return list.slice().sort(sortBlocksForList);
  }, [blocks, filters]);

  React.useEffect(() => {
    if (!filteredBlocks.length) {
      setSelectedBlockId(null);
      return;
    }
    if (!selectedBlockId || !filteredBlocks.some((block) => block.id === selectedBlockId)) {
      setSelectedBlockId(filteredBlocks[0].id);
    }
  }, [filteredBlocks, selectedBlockId]);
  const hasActiveFilters = React.useMemo(() => {
    if (filters.search.trim().length > 0) {
      return true;
    }
    return (Object.keys(filters) as Array<keyof FiltersState>).some((key) => filters[key] !== 'all');
  }, [filters]);

  const handleFilterChange = React.useCallback(
    <Key extends keyof FiltersState>(key: Key, value: FiltersState[Key]) => {
      setFilters((prev) => ({
        ...prev,
        [key]: value,
      }));
    },
    [],
  );

  const resetFilters = React.useCallback(() => {
    setFilters(INITIAL_FILTERS);
  }, []);

  const handleRefresh = React.useCallback(() => {
    setRefreshKey((key) => key + 1);
  }, []);

  const handleSelectBlock = React.useCallback((block: SiteBlock) => {
    setSelectedBlockId(block.id);
  }, []);

  const openCreateDialog = React.useCallback(() => {
    setCreateDialogOpen(true);
  }, []);

  const closeCreateDialog = React.useCallback(() => {
    setCreateDialogOpen(false);
  }, []);

  const handleCreateBlock = React.useCallback(
    async (payload: CreateSiteBlockPayload) => {
      const created = await managementSiteEditorApi.createSiteBlock(payload);
      setBlocks((prev) => [created, ...prev]);
      setSelectedBlockId(created.id);
      pushToast({ intent: 'success', description: 'Блок создан' });
    },
    [pushToast],
  );

  const handleBlockMutated = React.useCallback((next: SiteBlock) => {
    setBlocks((prev) => prev.map((item) => (item.id === next.id ? next : item)));
    setSelectedBlockId(next.id);
  }, []);

  const effectiveTotal = total ?? blocks.length;
  return (
    <div className="space-y-6" data-testid="site-block-library-page">
      <header className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">Библиотека блоков</h1>
            <p className="text-sm text-gray-600 dark:text-dark-200">
              Управляйте общими блоками сайта: редактируйте, публикуйте и отслеживайте историю изменений.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={openCreateDialog} disabled={loading}>Создать блок</Button>
            <Button
              variant="ghost"
              color="neutral"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
            >
              {loading ? 'Обновляем…' : 'Обновить'}
            </Button>
          </div>
        </div>
      </header>

      <Card padding="sm" className="space-y-3 bg-white/95 shadow-sm dark:bg-dark-800/80">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <Input
            value={filters.search}
            onChange={(event) => handleFilterChange('search', event.target.value)}
            placeholder="Поиск по названию, ключу или секции"
            prefix={<Search className="h-4 w-4 text-gray-400" />}
            className="sm:col-span-2 xl:col-span-3"
          />
          <Select
            value={filters.status}
            onChange={(event) => handleFilterChange('status', event.target.value as FiltersState['status'])}
            aria-label="Фильтр по статусу"
          >
            <option value="all">Все статусы</option>
            {(Object.keys(STATUS_META) as SiteBlockStatus[]).map((status) => (
              <option key={status} value={status}>
                {STATUS_META[status].label}
              </option>
            ))}
          </Select>
          <Select
            value={filters.reviewStatus}
            onChange={(event) => handleFilterChange('reviewStatus', event.target.value as FiltersState['reviewStatus'])}
            aria-label="Фильтр по статусу ревью"
          >
            <option value="all">Все статусы ревью</option>
            {REVIEW_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <Select
            value={filters.scope}
            onChange={(event) => handleFilterChange('scope', event.target.value as FiltersState['scope'])}
            aria-label="Фильтр по области"
          >
            <option value="all">Все области</option>
            {scopeOptions.map((scope) => (
              <option key={scope} value={scope}>
                {SCOPE_LABELS[scope] ?? scope}
              </option>
            ))}
          </Select>
          <Select
            value={filters.requiresPublisher}
            onChange={(event) => handleFilterChange('requiresPublisher', event.target.value as FiltersState['requiresPublisher'])}
            aria-label="Фильтр по requirement publisher"
          >
            <option value="all">Publisher не важен</option>
            <option value="true">Требует publisher</option>
            <option value="false">Не требует publisher</option>
          </Select>
          <Select
            value={filters.owner}
            onChange={(event) => handleFilterChange('owner', event.target.value as FiltersState['owner'])}
            aria-label="Фильтр по владельцу"
          >
            <option value="all">Все владельцы</option>
            {ownerOptions.map((owner) => (
              <option key={owner} value={owner}>
                {owner}
              </option>
            ))}
          </Select>
          <Select
            value={filters.locale}
            onChange={(event) => handleFilterChange('locale', event.target.value as FiltersState['locale'])}
            aria-label="Фильтр по локали"
          >
            <option value="all">Все локали</option>
            {localeOptions.map((locale) => (
              <option key={locale} value={locale}>
                {locale.toUpperCase()}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500 dark:text-dark-200">
          <span>
            Найдено {filteredBlocks.length} блоков из {effectiveTotal}
          </span>
          <div className="flex items-center gap-2">
            {loading ? <Spinner className="h-4 w-4 text-primary-400" /> : null}
            {hasActiveFilters ? (
              <Button variant="ghost" color="neutral" size="xs" onClick={resetFilters}>
                Сбросить фильтры
              </Button>
            ) : null}
          </div>
        </div>
        {error ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
            {error}
          </div>
        ) : null}
      </Card>

      <div className="grid gap-4 lg:grid-cols-[minmax(280px,320px)_minmax(0,1fr)]">
        <Card className="space-y-3 border border-white/70 bg-white/95 p-4 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Список блоков</h2>
            <span className="text-2xs text-gray-500 dark:text-dark-300">{blocks.length}</span>
          </div>
          <div className="space-y-2">
            {filteredBlocks.length ? (
              filteredBlocks.map((block) => (
                <SiteBlockListItem
                  key={block.id}
                  block={block}
                  selected={block.id === selectedBlockId}
                  onSelect={handleSelectBlock}
                />
              ))
            ) : (
              <div className="space-y-2 rounded-xl border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-200">
                <div>Подходящих блоков не найдено.</div>
                {hasActiveFilters ? (
                  <Button variant="ghost" color="neutral" size="xs" onClick={resetFilters}>
                    Сбросить фильтры
                  </Button>
                ) : null}
              </div>
            )}
          </div>
        </Card>

        <SiteBlockDetailPanel blockId={selectedBlockId} onBlockMutated={handleBlockMutated} />
      </div>

      <SiteBlockCreateDialog
        open={createDialogOpen}
        onClose={closeCreateDialog}
        onSubmit={handleCreateBlock}
      />
    </div>
  );
}

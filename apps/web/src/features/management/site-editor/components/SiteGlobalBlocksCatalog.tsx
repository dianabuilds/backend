import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Boxes, CheckCircle2, Edit3, FileCode2, Plus, Search, Send } from '@icons';
import { Badge, Button, Card, Input, Select, Spinner, TablePagination } from '@ui';
import { usePaginatedQuery } from '@shared/hooks/usePaginatedQuery';
import { extractErrorMessage } from '@shared/utils/errors';
import { formatDateTime, formatNumber } from '@shared/utils/format';
import { managementSiteEditorApi } from '@shared/api/management';
import { pushGlobalToast } from '@shared/ui/toastBus';
import { globalBlockStatusAppearance, reviewAppearance } from '../utils/pageHelpers';
import {
  GlobalBlockHistoryPanel,
  GlobalBlockMetricsPanel,
  GlobalBlockUsageList,
  GlobalBlockWarnings,
  MetaItem,
} from './SiteGlobalBlockPanels';
import type {
  SiteGlobalBlock,
  SiteGlobalBlockHistoryItem,
  SiteGlobalBlockListResponse,
  SiteGlobalBlockMetricsResponse,
  SiteGlobalBlockStatus,
  SiteGlobalBlockUsage,
  SiteGlobalBlockWarning,
  SiteMetricsPeriod,
} from '@shared/types/management';


type SortOrder = 'updated_at_desc' | 'updated_at_asc' | 'title_asc' | 'usage_desc';
type DraftFilter = 'all' | 'with' | 'without';
type RequiresFilter = 'all' | 'yes' | 'no';

type FiltersState = {
  search: string;
  status: '' | SiteGlobalBlockStatus;
  reviewStatus: '' | SiteGlobalBlock['review_status'];
  locale: string;
  section: string;
  hasDraft: DraftFilter;
  requiresPublisher: RequiresFilter;
  sort: SortOrder;
};

const INITIAL_FILTERS: FiltersState = {
  search: '',
  status: '',
  reviewStatus: '',
  locale: '',
  section: '',
  hasDraft: 'all',
  requiresPublisher: 'all',
  sort: 'updated_at_desc',
};

const STATUS_OPTIONS: Array<{ value: FiltersState['status']; label: string }> = [
  { value: '', label: 'Любой статус' },
  { value: 'draft', label: 'Черновик' },
  { value: 'published', label: 'Опубликован' },
  { value: 'archived', label: 'Архив' },
];

const REVIEW_OPTIONS: Array<{ value: FiltersState['reviewStatus']; label: string }> = [
  { value: '', label: 'Ревью (любое)' },
  { value: 'none', label: 'Не требуется' },
  { value: 'pending', label: 'На ревью' },
  { value: 'approved', label: 'Одобрено' },
  { value: 'rejected', label: 'Отклонено' },
];

const DRAFT_OPTIONS: Array<{ value: DraftFilter; label: string }> = [
  { value: 'all', label: 'Черновик: любой' },
  { value: 'with', label: 'Есть черновик' },
  { value: 'without', label: 'Без черновика' },
];

const REQUIRES_OPTIONS: Array<{ value: RequiresFilter; label: string }> = [
  { value: 'all', label: 'Права публикации' },
  { value: 'yes', label: 'Только publisher' },
  { value: 'no', label: 'Доступно редакторам' },
];

const SORT_OPTIONS: Array<{ value: SortOrder; label: string }> = [
  { value: 'updated_at_desc', label: 'По обновлению (новые)' },
  { value: 'updated_at_asc', label: 'По обновлению (старые)' },
  { value: 'title_asc', label: 'По названию (A–Я)' },
  { value: 'usage_desc', label: 'По использованию' },
];

const LOCALE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: '', label: 'Любая локаль' },
  { value: 'ru', label: 'Русский (ru)' },
  { value: 'en', label: 'Английский (en)' },
];

const FILTER_CONTROL_CLASS =
  'h-11 w-full rounded-full border border-gray-200/80 bg-white/80 px-4 text-sm font-medium text-gray-700 placeholder:text-gray-400 shadow-sm transition focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100 dark:border-dark-600 dark:bg-dark-900/80 dark:text-dark-100 dark:placeholder:text-dark-300';

function draftFilterToBoolean(filter: DraftFilter): boolean | undefined {
  if (filter === 'with') return true;
  if (filter === 'without') return false;
  return undefined;
}

function requiresFilterToBoolean(filter: RequiresFilter): boolean | undefined {
  if (filter === 'yes') return true;
  if (filter === 'no') return false;
  return undefined;
}

export default function SiteGlobalBlocksCatalog(): React.ReactElement {
  const [filters, setFilters] = React.useState<FiltersState>({ ...INITIAL_FILTERS });
  const [selectedBlock, setSelectedBlock] = React.useState<SiteGlobalBlock | null>(null);
  const [detailLoading, setDetailLoading] = React.useState(false);
  const [detailRefreshKey, setDetailRefreshKey] = React.useState(0);
  const [usage, setUsage] = React.useState<SiteGlobalBlockUsage[]>([]);
  const [warnings, setWarnings] = React.useState<SiteGlobalBlockWarning[]>([]);
  const [history, setHistory] = React.useState<SiteGlobalBlockHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = React.useState(false);
  const [historyError, setHistoryError] = React.useState<string | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = React.useState(0);
  const [metrics, setMetrics] = React.useState<SiteGlobalBlockMetricsResponse | null>(null);
  const [metricsLoading, setMetricsLoading] = React.useState(false);
  const [metricsError, setMetricsError] = React.useState<string | null>(null);
  const [metricsPeriod, setMetricsPeriod] = React.useState<SiteMetricsPeriod>('7d');
  const [metricsRefreshKey, setMetricsRefreshKey] = React.useState(0);

  const selectedBlockId = selectedBlock?.id ?? null;
  const createBlockPath = '/management/site-editor/global-blocks/new';
  const [reviewingId, setReviewingId] = React.useState<string | null>(null);
  const [publishingId, setPublishingId] = React.useState<string | null>(null);

  const {
    items,
    setItems,
    page,
    setPage,
    pageSize,
    setPageSize,
    hasNext,
    loading,
    error,
    setError,
    refresh,
  } = usePaginatedQuery<SiteGlobalBlock, SiteGlobalBlockListResponse>({
    initialPageSize: 10,
    dependencies: [
      filters.search,
      filters.status,
      filters.reviewStatus,
      filters.locale,
      filters.section,
      filters.hasDraft,
      filters.requiresPublisher,
      filters.sort,
    ],
    fetcher: async ({ page: currentPage, pageSize: currentPageSize, signal }) => {
      return managementSiteEditorApi.fetchSiteGlobalBlocks(
        {
          page: currentPage,
          pageSize: currentPageSize,
          query: filters.search,
          status: filters.status || undefined,
          reviewStatus: filters.reviewStatus || undefined,
          locale: filters.locale.trim() || undefined,
          section: filters.section.trim() || undefined,
          hasDraft: draftFilterToBoolean(filters.hasDraft),
          requiresPublisher: requiresFilterToBoolean(filters.requiresPublisher),
          sort: filters.sort,
        },
        { signal },
      );
    },
    mapResponse: (response, { page: currentPage, pageSize: currentPageSize }) => {
      const list = Array.isArray(response.items) ? response.items : [];
      const total = typeof response.total === 'number' ? response.total : null;
      const hasMore =
        total != null ? currentPage * currentPageSize < total : list.length >= currentPageSize;

      setSelectedBlock((prev) => {
        if (!list.length) {
          return null;
        }
        if (prev) {
          const match = list.find((item) => item.id === prev.id);
          if (match) {
            return { ...prev, ...match };
          }
        }
        return list[0];
      });

      return {
        items: list,
        hasNext: hasMore,
        total: total ?? undefined,
      };
    },
    onError: (err) => extractErrorMessage(err, 'Не удалось загрузить глобальные блоки'),
  });

  const handleFilterChange = React.useCallback(
    <K extends keyof FiltersState>(key: K, value: FiltersState[K]) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
      setPage(1);
    },
    [setPage],
  );

  const clearError = React.useCallback(() => setError(null), [setError]);
  const triggerDetailReload = React.useCallback(
    () => setDetailRefreshKey((key) => key + 1),
    [],
  );
  const triggerHistoryReload = React.useCallback(
    () => setHistoryRefreshKey((key) => key + 1),
    [],
  );
  const triggerMetricsReload = React.useCallback(
    () => setMetricsRefreshKey((key) => key + 1),
    [],
  );

  const handleSendBlockToReview = React.useCallback(
    async (block: SiteGlobalBlock) => {
      if (!block?.id || block.review_status === 'pending') {
        return;
      }
      const blockId = block.id;
      setReviewingId(blockId);
      try {
        const updated = await managementSiteEditorApi.saveSiteGlobalBlock(blockId, {
          review_status: 'pending',
        });
        setItems((prev) =>
          prev.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)),
        );
        setSelectedBlock((prev) => {
          if (prev && prev.id === updated.id) {
            return { ...prev, ...updated };
          }
          return prev;
        });
        pushGlobalToast({
          description: `Блок «${updated.title}» отправлен на ревью`,
          intent: 'success',
        });
      } catch (err) {
        pushGlobalToast({
          description: extractErrorMessage(err, 'Не удалось отправить на ревью'),
          intent: 'error',
        });
      } finally {
        setReviewingId((prev) => (prev === blockId ? null : prev));
      }
    },
    [setItems, setSelectedBlock],
  );

  const handlePublishBlock = React.useCallback(
    async (block: SiteGlobalBlock) => {
      if (!block?.id) {
        return;
      }
      const blockId = block.id;
      setPublishingId(blockId);
      try {
        const response = await managementSiteEditorApi.publishSiteGlobalBlock(blockId, {
          version: block.draft_version ?? undefined,
        });
        const updated = response.block;
        setItems((prev) =>
          prev.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)),
        );
        setSelectedBlock((prev) => {
          if (prev && prev.id === updated.id) {
            return { ...prev, ...updated };
          }
          return prev;
        });
        setUsage(response.usage ?? []);
        pushGlobalToast({
          description: `Блок «${updated.title}» опубликован`,
          intent: 'success',
        });
        triggerDetailReload();
        triggerHistoryReload();
        triggerMetricsReload();
      } catch (err) {
        pushGlobalToast({
          description: extractErrorMessage(err, 'Не удалось опубликовать блок'),
          intent: 'error',
        });
      } finally {
        setPublishingId((prev) => (prev === blockId ? null : prev));
      }
    },
    [
      setItems,
      setSelectedBlock,
      setUsage,
      triggerDetailReload,
      triggerHistoryReload,
      triggerMetricsReload,
    ],
  );

  React.useEffect(() => {
    if (!selectedBlockId) {
      setDetailLoading(false);
      setUsage([]);
      setWarnings([]);
      return;
    }
    const controller = new AbortController();
    setDetailLoading(true);
    managementSiteEditorApi
      .fetchSiteGlobalBlock(selectedBlockId, { signal: controller.signal })
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        const { block, usage: usageList, warnings: warningList } = response;
        setSelectedBlock((prev) => {
          if (prev && prev.id === block.id) {
            return { ...prev, ...block };
          }
          return block;
        });
        setUsage(usageList);
        setWarnings(warningList);
      })
      .catch((err) => {
        if (controller.signal.aborted || (err as { name?: string })?.name === 'AbortError') {
          return;
        }
        if (process.env.NODE_ENV !== 'production') {
          // eslint-disable-next-line no-console
          console.warn('Не удалось загрузить детали глобального блока', err);
        }
        setUsage([]);
        setWarnings([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setDetailLoading(false);
        }
      });
    return () => controller.abort();
  }, [selectedBlockId, detailRefreshKey]);

  React.useEffect(() => {
    if (!selectedBlockId) {
      setHistory([]);
      setHistoryError(null);
      setHistoryLoading(false);
      return;
    }
    const controller = new AbortController();
    setHistoryLoading(true);
    setHistoryError(null);
    managementSiteEditorApi
      .fetchSiteGlobalBlockHistory(
        selectedBlockId,
        { limit: 10 },
        { signal: controller.signal },
      )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        setHistory(response.items);
      })
      .catch((err) => {
        if (controller.signal.aborted || (err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setHistoryError(extractErrorMessage(err, 'Не удалось загрузить историю блока'));
        setHistory([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setHistoryLoading(false);
        }
      });
    return () => controller.abort();
  }, [selectedBlockId, historyRefreshKey]);

  React.useEffect(() => {
    if (!selectedBlockId) {
      setMetrics(null);
      setMetricsError(null);
      setMetricsLoading(false);
      return;
    }
    const controller = new AbortController();
    setMetricsLoading(true);
    setMetricsError(null);
    managementSiteEditorApi
      .fetchSiteGlobalBlockMetrics(
        selectedBlockId,
        { period: metricsPeriod },
        { signal: controller.signal },
      )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        setMetrics(response);
      })
      .catch((err) => {
        if (controller.signal.aborted || (err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setMetricsError(extractErrorMessage(err, 'Не удалось загрузить метрики блока'));
        setMetrics(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setMetricsLoading(false);
        }
      });
    return () => controller.abort();
  }, [selectedBlockId, metricsPeriod, metricsRefreshKey]);

  const selectedStatus = selectedBlock ? globalBlockStatusAppearance(selectedBlock.status) : null;
  const selectedReview = selectedBlock ? reviewAppearance(selectedBlock.review_status) : null;

  return (
    <div className="space-y-6 pb-12">
      <header className="rounded-3xl bg-white/95 p-6 shadow-sm ring-1 ring-gray-200/70 dark:bg-dark-900/90 dark:ring-dark-700">
        <div className="text-xs font-semibold uppercase tracking-[0.32em] text-primary-500 dark:text-primary-300">
          Site editor
        </div>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white sm:text-3xl">
              Каталог глобальных блоков
            </h1>
            <p className="max-w-2xl text-sm text-gray-600 dark:text-dark-200">
              Управляйте общими секциями сайта, следите за зависимостями страниц и готовностью к
              публикации.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 text-sm text-gray-500 dark:text-dark-200">
            <Boxes className="h-4 w-4 text-primary-500" />
            <span>Фильтруйте по зоне, статусу публикации и необходимости подтверждения.</span>
          </div>
        </div>
      </header>

      <Card className="space-y-4 p-5">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-dark-300">
          <Search className="h-4 w-4" />
          Поиск и фильтры
        </div>
        <div className="flex flex-wrap items-stretch gap-3">
          <div className="flex flex-1 min-w-[240px] xl:flex-[2.2]">
            <Input
              aria-label="Поиск по глобальным блокам"
              placeholder="Поиск по названию или key"
              value={filters.search}
              onChange={(event) => handleFilterChange('search', event.currentTarget.value)}
              className={FILTER_CONTROL_CLASS}
            />
          </div>
          <div className="flex flex-1 min-w-[160px] sm:flex-[1] xl:flex-[1.05]">
            <Select
              aria-label="Фильтр по статусу"
              value={filters.status}
              onChange={(event) => handleFilterChange('status', event.currentTarget.value as FiltersState['status'])}
              className={FILTER_CONTROL_CLASS}
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value || 'all'} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-1 min-w-[160px] sm:flex-[1] xl:flex-[1.05]">
            <Select
              aria-label="Фильтр по ревью"
              value={filters.reviewStatus}
              onChange={(event) =>
                handleFilterChange('reviewStatus', event.currentTarget.value as FiltersState['reviewStatus'])
              }
              className={FILTER_CONTROL_CLASS}
            >
              {REVIEW_OPTIONS.map((option) => (
                <option key={option.value || 'all'} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-1 min-w-[160px] sm:flex-[1] xl:flex-[1.05]">
            <Select
              aria-label="Фильтр по черновикам"
              value={filters.hasDraft}
              onChange={(event) => handleFilterChange('hasDraft', event.currentTarget.value as DraftFilter)}
              className={FILTER_CONTROL_CLASS}
            >
              {DRAFT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-1 min-w-[160px] sm:flex-[1] xl:flex-[1.05]">
            <Select
              aria-label="Фильтр по правам публикации"
              value={filters.requiresPublisher}
              onChange={(event) =>
                handleFilterChange('requiresPublisher', event.currentTarget.value as RequiresFilter)
              }
              className={FILTER_CONTROL_CLASS}
            >
              {REQUIRES_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-1 min-w-[160px] sm:flex-[1] xl:flex-[0.9]">
            <Select
              aria-label="Фильтр по локали"
              value={filters.locale}
              onChange={(event) => handleFilterChange('locale', event.currentTarget.value)}
              className={FILTER_CONTROL_CLASS}
            >
              {LOCALE_OPTIONS.map((option) => (
                <option key={option.value || 'all-locales'} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-1 min-w-[180px] sm:flex-[1] xl:flex-[1.1]">
            <Input
              aria-label="Фильтр по зоне использования"
              placeholder="Зона (header, footer...)"
              value={filters.section}
              onChange={(event) => handleFilterChange('section', event.currentTarget.value)}
              className={FILTER_CONTROL_CLASS}
            />
          </div>
          <div className="flex flex-1 min-w-[180px] sm:flex-[1] xl:flex-[1.2]">
            <Select
              aria-label="Сортировка"
              value={filters.sort}
              onChange={(event) => handleFilterChange('sort', event.currentTarget.value as SortOrder)}
              className={FILTER_CONTROL_CLASS}
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </Card>

      <div className="grid gap-6 lg:grid-cols-12">
        <Card className="flex flex-col gap-0 p-0 lg:col-span-7 xl:col-span-8">
          <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
            <div>
              <h2 className="text-base font-semibold text-gray-900 dark:text-white">Глобальные блоки</h2>
              <p className="text-xs text-gray-500 dark:text-dark-200">
                {items.length
                  ? `Найдено ${items.length} блоков на этой странице выдачи.`
                  : 'Используйте фильтры, чтобы получить список блоков.'}
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-3">
              {loading && items.length > 0 ? (
                <span className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
                  <Spinner className="h-4 w-4" />
                  Обновляем...
                </span>
              ) : null}
              <Button
                as={Link}
                to={createBlockPath}
                size="sm"
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                <span>Создать глобальный блок</span>
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => {
                  clearError();
                  void refresh();
                }}
              >
                Обновить
              </Button>
            </div>
          </div>
          <div className="space-y-3 px-5 pb-5">
            {error ? (
              <div className="rounded-2xl border border-rose-200/70 bg-rose-50/70 p-4 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0" />
                  <div className="space-y-2">
                    <p>{error}</p>
                    <div className="flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        variant="outlined"
                        onClick={() => {
                          clearError();
                          void refresh();
                        }}
                      >
                        Повторить
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            ) : loading && items.length === 0 ? (
              <div className="flex items-center gap-2 rounded-2xl border border-dashed border-gray-200 py-10 text-sm text-gray-500 dark:border-dark-700 dark:text-dark-200">
                <Spinner className="h-5 w-5" />
                Загружаем глобальные блоки...
              </div>
            ) : items.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-gray-200 py-12 text-center text-sm text-gray-500 dark:border-dark-700 dark:text-dark-200">
                <FileCode2 className="h-10 w-10 text-primary-400" />
                <div className="space-y-1">
                  <p>Каталог пуст.</p>
                  <p className="text-xs text-gray-400 dark:text-dark-300">
                    Создайте новый глобальный блок или скорректируйте фильтры.
                  </p>
                </div>
                <div className="flex flex-wrap justify-center gap-2">
                  <Button
                    as={Link}
                    to={createBlockPath}
                    size="sm"
                    className="gap-2"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Создать глобальный блок</span>
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      void refresh();
                    }}
                  >
                    Обновить список
                  </Button>
                </div>
              </div>
            ) : (
                  <ul className="space-y-2">
                {items.map((blockItem) => {
                  const isSelected = selectedBlock?.id === blockItem.id;
                  const status = globalBlockStatusAppearance(blockItem.status);
                  const review = reviewAppearance(blockItem.review_status);
                  const isReviewing = reviewingId === blockItem.id;
                  const isPublishing = publishingId === blockItem.id;
                  const draftVersion = blockItem.draft_version ?? null;
                  const publishedVersion = blockItem.published_version ?? null;
                  const versionsDiffer =
                    draftVersion != null &&
                    (publishedVersion == null || draftVersion > publishedVersion);
                  const hasPendingChanges =
                    Boolean(blockItem.has_pending_publish) ||
                    versionsDiffer ||
                    blockItem.status !== 'published';
                  const reviewDisabled = blockItem.review_status === 'pending' || isReviewing;
                  const publishDisabled = isPublishing || !hasPendingChanges;
                  const blockDetailHref = `/management/site-editor/global-blocks/${blockItem.id}`;
                  return (
                    <li key={blockItem.id}>
                      <div
                        role="button"
                        tabIndex={0}
                        data-testid="site-global-block-item"
                        aria-pressed={isSelected}
                        aria-label={`Выбрать блок ${blockItem.title}`}
                        onClick={() =>
                          setSelectedBlock((prev) => (prev ? { ...prev, ...blockItem } : blockItem))
                        }
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault();
                            setSelectedBlock((prev) =>
                              prev ? { ...prev, ...blockItem } : blockItem,
                            );
                          }
                        }}
                        className={[
                          'group flex flex-col gap-3 rounded-2xl border px-5 py-4 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 dark:bg-dark-800/60 dark:focus-visible:ring-primary-300',
                          isSelected
                            ? 'border-primary-300 bg-primary-50/70 shadow-sm dark:border-primary-500/40 dark:bg-primary-500/10'
                            : 'border-transparent bg-gray-50/70 hover:border-primary-200/60 hover:bg-white dark:border-transparent dark:hover:bg-dark-700',
                        ].join(' ')}
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-sm font-semibold text-gray-900 dark:text-white">
                                {blockItem.title}
                              </span>
                              <Badge color={status.color} variant="soft" className="text-[10px] uppercase tracking-wide">
                                {status.label}
                              </Badge>
                              <Badge color={review.color} variant="outline" className="text-[10px] uppercase tracking-wide">
                                {review.label}
                              </Badge>
                              {blockItem.requires_publisher ? (
                                <Badge color="warning" variant="soft" className="text-[10px] uppercase tracking-wide">
                                  Publisher
                                </Badge>
                              ) : null}
                              {blockItem.has_pending_publish ? (
                                <Badge color="primary" variant="soft" className="text-[10px] uppercase tracking-wide">
                                  Новые изменения
                                </Badge>
                              ) : null}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-dark-200">{blockItem.key}</div>
                          </div>
                          <div className="flex flex-wrap items-center justify-end gap-2">
                            <Button
                              as={Link}
                              to={blockDetailHref}
                              size="sm"
                              variant="ghost"
                              className="gap-1"
                              onClick={(event) => event.stopPropagation()}
                            >
                              <Edit3 className="h-4 w-4" />
                              <span>Редактировать</span>
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              variant="ghost"
                              className="gap-1"
                              disabled={reviewDisabled}
                              onClick={(event) => {
                                event.stopPropagation();
                                void handleSendBlockToReview(blockItem);
                              }}
                            >
                              {isReviewing ? (
                                <Spinner className="h-4 w-4" />
                              ) : (
                                <Send className="h-4 w-4" />
                              )}
                              <span>{isReviewing ? 'Отправляем...' : 'Отправить на ревью'}</span>
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              variant="ghost"
                              className="gap-1"
                              disabled={publishDisabled}
                              onClick={(event) => {
                                event.stopPropagation();
                                void handlePublishBlock(blockItem);
                              }}
                            >
                              {isPublishing ? (
                                <Spinner className="h-4 w-4" />
                              ) : (
                                <CheckCircle2 className="h-4 w-4" />
                              )}
                              <span>{isPublishing ? 'Публикуем...' : 'Опубликовать'}</span>
                            </Button>
                          </div>
                        </div>
                        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-gray-600 dark:text-dark-200">
                          <MetaItem label="Зона" value={blockItem.section || '—'} />
                          <MetaItem label="Локаль" value={blockItem.locale || '—'} />
                          <MetaItem
                            label="Версии"
                            value={
                              blockItem.published_version != null || blockItem.draft_version != null
                                ? `v${blockItem.published_version ?? '—'} · draft ${blockItem.draft_version ?? '—'}`
                                : '—'
                            }
                          />
                          <MetaItem
                            label="Обновлён"
                            value={formatDateTime(blockItem.updated_at, { fallback: '—' })}
                          />
                          <MetaItem
                            label="Использование"
                            value={formatNumber(blockItem.usage_count ?? 0, {
                              defaultValue: '0',
                              compact: true,
                              maximumFractionDigits: 0,
                            })}
                          />
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
          <div className="border-t border-gray-100 px-5 py-4 dark:border-dark-700">
            {loading && items.length === 0 ? (
              <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-dark-200">
                <Spinner className="h-4 w-4" />
                Загрузка...
              </div>
            ) : (
              <TablePagination
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
                currentCount={items.length}
                totalItems={!hasNext ? (page - 1) * pageSize + items.length : undefined}
                hasNext={hasNext}
                summaryPrefix="Показываем"
              />
            )}
          </div>
        </Card>

        <Card className="space-y-4 p-6 lg:col-span-5 xl:col-span-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-gray-900 dark:text-white">Карточка блока</h2>
              <p className="text-sm text-gray-500 dark:text-dark-200">
                Выберите глобальный блок, чтобы увидеть подробности и историю.
              </p>
            </div>
            {selectedBlock ? (
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  size="xs"
                  variant="ghost"
                  onClick={triggerDetailReload}
                  disabled={detailLoading}
                >
                  {detailLoading ? 'Обновляем...' : 'Обновить детали'}
                </Button>
                <Button
                  type="button"
                  size="xs"
                  variant="ghost"
                  onClick={triggerMetricsReload}
                  disabled={metricsLoading}
                >
                  {metricsLoading ? 'Метрики...' : 'Обновить метрики'}
                </Button>
              </div>
            ) : null}
          </div>

          {selectedBlock ? (
            <div className="space-y-4 text-sm text-gray-700 dark:text-dark-100">
              <div className="space-y-1">
                <div className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-300">Блок</div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-base font-semibold text-gray-900 dark:text-white">
                    {selectedBlock.title}
                  </span>
                  {selectedStatus ? (
                    <Badge color={selectedStatus.color} variant="soft">
                      {selectedStatus.label}
                    </Badge>
                  ) : null}
                  {selectedReview ? (
                    <Badge color={selectedReview.color} variant="outline">
                      {selectedReview.label}
                    </Badge>
                  ) : null}
                  {selectedBlock.requires_publisher ? (
                    <Badge color="warning" variant="soft">
                      Publisher
                    </Badge>
                  ) : null}
                  {selectedBlock.has_pending_publish ? (
                    <Badge color="primary" variant="soft">
                      Новые изменения
                    </Badge>
                  ) : null}
                </div>
                <div className="text-xs text-gray-500 dark:text-dark-200">{selectedBlock.key}</div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <DetailRow label="Зона" value={selectedBlock.section || '—'} />
                <DetailRow label="Локаль" value={selectedBlock.locale || '—'} />
                <DetailRow label="Версия (публик.)" value={selectedBlock.published_version ?? '—'} />
                <DetailRow
                  label="Версия черновика"
                  value={selectedBlock.draft_version ?? '—'}
                  tone={
                    selectedBlock.draft_version != null &&
                    selectedBlock.published_version != null &&
                    selectedBlock.draft_version > selectedBlock.published_version
                      ? 'warning'
                      : 'neutral'
                  }
                />
                <DetailRow
                  label="Обновлён"
                  value={formatDateTime(selectedBlock.updated_at, {
                    fallback: '—',
                    withSeconds: true,
                  })}
                />
                <DetailRow label="Изменил" value={selectedBlock.updated_by || '—'} />
              </div>

              {selectedBlock.comment ? (
                <div className="rounded-2xl border border-gray-100 bg-gray-50 p-3 text-xs text-gray-600 dark:border-dark-600 dark:bg-dark-800 dark:text-dark-200">
                  Комментарий: {selectedBlock.comment}
                </div>
              ) : null}

              <GlobalBlockWarnings warnings={warnings} />

              <GlobalBlockUsageList usage={usage} loading={detailLoading} />

              <GlobalBlockHistoryPanel
                entries={history}
                loading={historyLoading}
                error={historyError}
                onRefresh={triggerHistoryReload}
              />

              <GlobalBlockMetricsPanel
                metrics={metrics}
                loading={metricsLoading}
                error={metricsError}
                period={metricsPeriod}
                onChangePeriod={setMetricsPeriod}
                onRefresh={triggerMetricsReload}
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-gray-200 p-6 text-center dark:border-dark-600">
              <FileCode2 className="h-10 w-10 text-primary-400" />
              <div className="text-sm text-gray-600 dark:text-dark-200">
                Выберите глобальный блок, чтобы посмотреть детали.
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
type DetailRowProps = {
  label: string;
  value: React.ReactNode;
  tone?: 'success' | 'warning' | 'error' | 'neutral';
};

function DetailRow({ label, value, tone }: DetailRowProps) {
  const color =
    tone === 'success'
      ? 'text-emerald-600 dark:text-emerald-300'
      : tone === 'warning'
      ? 'text-amber-600 dark:text-amber-300'
      : tone === 'error'
      ? 'text-red-600 dark:text-red-300'
      : 'text-gray-800 dark:text-dark-50';

  return (
    <div className="space-y-1">
      <div className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-300">{label}</div>
      <div className={['text-sm font-medium', color].join(' ')}>{value}</div>
    </div>
  );
}





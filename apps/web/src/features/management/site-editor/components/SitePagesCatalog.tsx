import React from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { AlertTriangle, FileCode2, ListFilter, Pin, Plus, Search, Trash2 } from '@icons';
import { Badge, Button, Card, Dialog, Input, Select, Spinner, Switch, TablePagination } from '@ui';
import { usePaginatedQuery } from '@shared/hooks/usePaginatedQuery';
import { extractErrorMessage } from '@shared/utils/errors';
import { formatDateTime } from '@shared/utils/format';
import { pushGlobalToast } from '@shared/ui/toastBus';
import { managementSiteEditorApi } from '@shared/api/management';
import { globalBlockStatusAppearance, reviewAppearance, statusAppearance, typeLabel } from '../utils/pageHelpers';
import { SitePageHistoryPanel } from './PageHistoryPanel';
import { SitePageAuditPanel } from './PageAuditPanel';
import type {
  SitePageAttachedGlobalBlock,
  SitePageListResponse,
  SitePageStatus,
  SitePageSummary,
  SitePageType,
  SitePageVersion,
  SiteAuditEntry,
} from '@shared/types/management';

type SortOrder = 'updated_at_desc' | 'updated_at_asc' | 'title_asc' | 'title_desc' | 'pinned_desc' | 'pinned_asc';

type DraftFilter = 'all' | 'with' | 'without';

type PinnedFilter = 'all' | 'only' | 'without';

type FiltersState = {
  search: string;
  type: '' | SitePageType;
  status: '' | SitePageStatus;
  locale: string;
  hasDraft: DraftFilter;
  pinned: PinnedFilter;
  sort: SortOrder;
};

const INITIAL_FILTERS: FiltersState = {
  search: '',
  type: '',
  status: '',
  locale: '',
  hasDraft: 'all',
  pinned: 'all',
  sort: 'updated_at_desc',
};

type CreatePageFormState = {
  title: string;
  slug: string;
  type: SitePageType;
  locale: string;
  owner: string;
  pinned: boolean;
};

const CREATE_PAGE_INITIAL: CreatePageFormState = {
  title: '',
  slug: '',
  type: 'landing',
  locale: 'ru',
  owner: '',
  pinned: false,
};

const HOME_SLUGS = new Set<string>(['/', 'main']);


const STATUS_OPTIONS: Array<{ value: SitePageStatus | ''; label: string }> = [
  { value: '', label: 'Все статусы' },
  { value: 'draft', label: 'Черновик' },
  { value: 'published', label: 'Опубликована' },
  { value: 'archived', label: 'Архив' },
];

const TYPE_OPTIONS: Array<{ value: SitePageType | ''; label: string }> = [
  { value: '', label: 'Все типы' },
  { value: 'landing', label: 'Лэндинг' },
  { value: 'collection', label: 'Коллекция' },
  { value: 'article', label: 'Статья' },
  { value: 'system', label: 'Системная' },
];

const DRAFT_OPTIONS: Array<{ value: DraftFilter; label: string }> = [
  { value: 'all', label: 'Любые черновики' },
  { value: 'with', label: 'Только с черновиком' },
  { value: 'without', label: 'Без черновика' },
];

const PINNED_OPTIONS: Array<{ value: PinnedFilter; label: string }> = [
  { value: 'all', label: 'Все страницы' },
  { value: 'only', label: 'Только закреплённые' },
  { value: 'without', label: 'Не закреплённые' },
];

const LOCALE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: '', label: 'Все локали' },
  { value: 'ru', label: 'ru (основная)' },
  { value: 'en', label: 'en' },
  { value: 'es', label: 'es' },
  { value: 'de', label: 'de' },
];

const FILTER_CONTROL_CLASS =
  'h-11 w-full rounded-full border border-gray-200/80 bg-white/80 px-4 text-sm font-medium text-gray-700 placeholder:text-gray-400 shadow-sm transition focus:border-primary-300 focus:outline-none focus:ring-2 focus:ring-primary-100 dark:border-dark-600 dark:bg-dark-900/80 dark:text-dark-100 dark:placeholder:text-dark-300';

const SORT_OPTIONS: Array<{ value: SortOrder; label: string }> = [
  { value: 'updated_at_desc', label: 'По обновлению (новые)' },
  { value: 'updated_at_asc', label: 'По обновлению (старые)' },
  { value: 'title_asc', label: 'По названию (A–Я)' },
  { value: 'title_desc', label: 'По названию (Я–A)' },
  { value: 'pinned_desc', label: 'Закреплённые выше' },
  { value: 'pinned_asc', label: 'Сначала незакреплённые' },
];

function draftFilterToBoolean(filter: DraftFilter): boolean | undefined {
  if (filter === 'with') return true;
  if (filter === 'without') return false;
  return undefined;
}

function pinnedFilterToBoolean(filter: PinnedFilter): boolean | undefined {
  if (filter === 'only') return true;
  if (filter === 'without') return false;
  return undefined;
}

function normalizeSlugInput(value: string): string {
  if (!value) {
    return '';
  }
  const sanitized = value.trim().replace(/\s+/g, '-');
  if (!sanitized) {
    return '';
  }
  return sanitized.startsWith('/') ? sanitized : `/${sanitized}`;
}

export default function SitePagesCatalog(): React.ReactElement {
  const [filters, setFilters] = React.useState<FiltersState>({ ...INITIAL_FILTERS });
  const [selectedPage, setSelectedPage] = React.useState<SitePageSummary | null>(null);
  const [detailLoading, setDetailLoading] = React.useState(false);
  const [detailError, setDetailError] = React.useState<string | null>(null);
  const [detailRefreshKey, setDetailRefreshKey] = React.useState(0);
  const [history, setHistory] = React.useState<SitePageVersion[]>([]);
  const [historyLoading, setHistoryLoading] = React.useState(false);
  const [historyError, setHistoryError] = React.useState<string | null>(null);
  const [auditEntries, setAuditEntries] = React.useState<SiteAuditEntry[]>([]);
  const [auditLoading, setAuditLoading] = React.useState(false);
  const [auditError, setAuditError] = React.useState<string | null>(null);
  const [restoringVersion, setRestoringVersion] = React.useState<number | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = React.useState(0);
  const [auditRefreshKey, setAuditRefreshKey] = React.useState(0);
  const [createDialogOpen, setCreateDialogOpen] = React.useState(false);
  const [createForm, setCreateForm] = React.useState<CreatePageFormState>({ ...CREATE_PAGE_INITIAL });
  const [createSubmitting, setCreateSubmitting] = React.useState(false);
  const [createError, setCreateError] = React.useState<string | null>(null);
  const [deleteDialogPage, setDeleteDialogPage] = React.useState<SitePageSummary | null>(null);
  const [deleteSubmitting, setDeleteSubmitting] = React.useState(false);
  const [deleteError, setDeleteError] = React.useState<string | null>(null);
  const selectedPageId = selectedPage?.id ?? null;
  const triggerHistoryReload = React.useCallback(() => {
    setHistoryRefreshKey((key) => key + 1);
  }, []);
  const triggerAuditReload = React.useCallback(() => {
    setAuditRefreshKey((key) => key + 1);
  }, []);
  const triggerDetailReload = React.useCallback(() => {
    setDetailRefreshKey((key) => key + 1);
  }, []);
  const attachedBlocks = React.useMemo<SitePageAttachedGlobalBlock[]>(() => {
    if (!selectedPage || !Array.isArray(selectedPage.global_blocks)) {
      return [];
    }
    return selectedPage.global_blocks.filter(
      (item): item is SitePageAttachedGlobalBlock => item != null,
    );
  }, [selectedPage]);

  // eslint-disable-next-line no-console

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
  } = usePaginatedQuery<SitePageSummary, SitePageListResponse>({
    initialPageSize: 10,
    dependencies: [
      filters.search,
      filters.type,
      filters.status,
      filters.locale,
      filters.hasDraft,
      filters.pinned,
      filters.sort,
    ],
    fetcher: async ({ page: currentPage, pageSize: currentPageSize, signal }) => {
      return managementSiteEditorApi.fetchSitePages(
        {
          page: currentPage,
          pageSize: currentPageSize,
          query: filters.search,
          type: filters.type || undefined,
          status: filters.status || undefined,
          locale: filters.locale || undefined,
          hasDraft: draftFilterToBoolean(filters.hasDraft),
          pinned: pinnedFilterToBoolean(filters.pinned),
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

      setSelectedPage((prev) => {
        if (!list.length) return null;
        if (prev && list.some((item) => item.id === prev.id)) {
          return list.find((item) => item.id === prev.id) ?? list[0];
        }
        return list[0];
      });

      return {
        items: list,
        hasNext: hasMore,
        total: total ?? undefined,
      };
    },
    onError: (err) => extractErrorMessage(err, 'Не удалось загрузить страницы'),
  });

  React.useEffect(() => {
    if (!selectedPageId) {
      setDetailLoading(false);
      setDetailError(null);
      return;
    }
    const controller = new AbortController();
    setDetailLoading(true);
    setDetailError(null);
    managementSiteEditorApi
      .fetchSitePage(selectedPageId, { signal: controller.signal })
      .then((response) => {
        if (controller.signal.aborted || !response) {
          return;
        }
        setSelectedPage((prev) => {
          if (!prev || prev.id !== response.id) {
            return prev;
          }
          return { ...prev, ...response };
        });
      })
      .catch((err) => {
        if (controller.signal.aborted || (err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setDetailError(extractErrorMessage(err, 'Не удалось загрузить детали страницы'));
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setDetailLoading(false);
        }
      });
    return () => controller.abort();
  }, [selectedPageId, detailRefreshKey]);

  React.useEffect(() => {
    if (!selectedPageId) {
      setHistory([]);
      setHistoryError(null);
      setHistoryLoading(false);
      return;
    }
    const controller = new AbortController();
    setHistoryLoading(true);
    setHistoryError(null);
    managementSiteEditorApi
      .fetchSitePageHistory(selectedPageId, { limit: 10 }, { signal: controller.signal })
      .then((response) => {
        if (!controller.signal.aborted) {
          setHistory(response.items);
        }
      })
      .catch((err) => {
        if (controller.signal.aborted || (err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setHistoryError(extractErrorMessage(err, 'Failed to load history'));
        setHistory([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setHistoryLoading(false);
        }
      });
    return () => controller.abort();
  }, [selectedPageId, historyRefreshKey]);

  React.useEffect(() => {
    if (!selectedPageId) {
      setAuditEntries([]);
      setAuditError(null);
      setAuditLoading(false);
      return;
    }
    const controller = new AbortController();
    setAuditLoading(true);
    setAuditError(null);
    managementSiteEditorApi
      .fetchSiteAudit(
        { entityType: 'page', entityId: selectedPageId, limit: 10 },
        { signal: controller.signal },
      )
      .then((response) => {
        if (!controller.signal.aborted) {
          setAuditEntries(response.items);
        }
      })
      .catch((err) => {
        if (controller.signal.aborted || (err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setAuditError(extractErrorMessage(err, 'Failed to load audit log'));
        setAuditEntries([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setAuditLoading(false);
        }
      });
    return () => controller.abort();
  }, [selectedPageId, auditRefreshKey]);

  const handleRestoreVersion = React.useCallback(
    async (version: number) => {
      if (!selectedPageId) {
        return;
      }
      const pageId = selectedPageId;
      setRestoringVersion(version);
      setHistoryError(null);
      try {
        await managementSiteEditorApi.restoreSitePageVersion(pageId, version);
        pushGlobalToast({ description: `Версия v${version} восстановлена в черновик`, intent: 'success' });
        await refresh();
        triggerHistoryReload();
        triggerAuditReload();
      } catch (err) {
        setHistoryError(extractErrorMessage(err, 'Не удалось восстановить версию'));
      } finally {
        setRestoringVersion((prev) => (prev === version ? null : prev));
      }
    },
    [selectedPageId, refresh, triggerHistoryReload, triggerAuditReload],
  );

  const handleFilterChange = React.useCallback(
    <K extends keyof FiltersState>(key: K, value: FiltersState[K]) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
      setPage(1);
    },
    [setPage],
  );

  const clearError = React.useCallback(() => setError(null), [setError]);

  const openCreateDialog = React.useCallback(() => {
    setCreateForm((prev) => ({ ...CREATE_PAGE_INITIAL, locale: prev.locale || 'ru' }));
    setCreateError(null);
    setCreateDialogOpen(true);
  }, []);

  const closeCreateDialog = React.useCallback(() => {
    if (createSubmitting) {
      return;
    }
    setCreateDialogOpen(false);
    setCreateError(null);
  }, [createSubmitting]);

  const handleCreateFieldChange = React.useCallback(
    <K extends keyof CreatePageFormState>(key: K, value: CreatePageFormState[K]) => {
      setCreateForm((prev) => ({ ...prev, [key]: value }));
    },
    [],
  );

  const handleSlugBlur = React.useCallback(() => {
    setCreateForm((prev) => ({ ...prev, slug: normalizeSlugInput(prev.slug) }));
  }, []);

  const canDeletePage = React.useCallback(
    (page: SitePageSummary | null | undefined) =>
      Boolean(page) && !HOME_SLUGS.has((page?.slug ?? '').trim()) && !page?.pinned,
    [],
  );

  const handleOpenDeleteDialog = React.useCallback((page: SitePageSummary) => {
    setDeleteDialogPage(page);
    setDeleteError(null);
  }, []);

  const handleCloseDeleteDialog = React.useCallback(() => {
    if (deleteSubmitting) {
      return;
    }
    setDeleteDialogPage(null);
    setDeleteError(null);
  }, [deleteSubmitting]);

  const handleSubmitCreate = React.useCallback(async () => {
    if (createSubmitting) {
      return;
    }
    const normalizedTitle = createForm.title.trim();
    const normalizedSlug = normalizeSlugInput(createForm.slug);
    const locale = createForm.locale.trim() || 'ru';
    if (!normalizedTitle || !normalizedSlug) {
      setCreateError('Введите название страницы и slug');
      return;
    }
    setCreateSubmitting(true);
    setCreateError(null);
    try {
      const newPage = await managementSiteEditorApi.createSitePage({
        title: normalizedTitle,
        slug: normalizedSlug,
        type: createForm.type,
        locale,
        owner: createForm.owner.trim() || undefined,
        pinned: createForm.pinned,
      });
      setCreateDialogOpen(false);
      setCreateForm({ ...CREATE_PAGE_INITIAL, locale });
      setItems((prev) => {
        const filtered = prev.filter((item) => item.id !== newPage.id);
        return [newPage, ...filtered];
      });
      setSelectedPage(newPage);
      setHistory([]);
      setAuditEntries([]);
      pushGlobalToast({ description: `Страница «${newPage.title}» создана`, intent: 'success' });
      await refresh();
    } catch (err) {
      setCreateError(extractErrorMessage(err, 'Не удалось создать страницу'));
    } finally {
      setCreateSubmitting(false);
    }
  }, [
    createForm.locale,
    createForm.owner,
    createForm.pinned,
    createForm.slug,
    createForm.title,
    createForm.type,
    createSubmitting,
    refresh,
    setItems,
  ]);

  const handleConfirmDelete = React.useCallback(async () => {
    const pageToDelete = deleteDialogPage;
    if (!pageToDelete || deleteSubmitting) {
      return;
    }
    setDeleteSubmitting(true);
    setDeleteError(null);
    try {
      await managementSiteEditorApi.deleteSitePage(pageToDelete.id);
      setItems((prev) => prev.filter((item) => item.id !== pageToDelete.id));
      if (selectedPage?.id === pageToDelete.id) {
        setSelectedPage(null);
        setHistory([]);
        setAuditEntries([]);
      }
      pushGlobalToast({ description: `Страница «${pageToDelete.title}» удалена`, intent: 'success' });
      setDeleteDialogPage(null);
      await refresh();
    } catch (err) {
      setDeleteError(extractErrorMessage(err, 'Не удалось удалить страницу'));
    } finally {
      setDeleteSubmitting(false);
    }
  }, [deleteDialogPage, deleteSubmitting, refresh, selectedPage, setItems]);

  const renderStatus = React.useCallback((status: SitePageStatus, hasPending: boolean | null | undefined) => {
    const { label, color } = statusAppearance(status);
    return (
      <div className="flex items-center gap-2">
        <Badge color={color} variant="soft">
          {label}
        </Badge>
        {hasPending ? (
          <Badge color="warning" variant="soft" className="text-xs">
            На ревью
          </Badge>
        ) : null}
      </div>
    );
  }, []);

  return (
    <div className="space-y-6 pb-12">
      <header className="rounded-3xl bg-white/95 p-6 shadow-sm ring-1 ring-gray-200/70 dark:bg-dark-900/90 dark:ring-dark-700">
        <div className="text-xs font-semibold uppercase tracking-[0.32em] text-primary-500 dark:text-primary-300">
          Site editor
        </div>
        <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-white sm:text-3xl">Каталог страниц</h1>
            <p className="max-w-2xl text-sm text-gray-600 dark:text-dark-200">
              Управление страницами публичного сайта, черновиками и статусами публикаций.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-500 dark:text-dark-200">
            <div className="inline-flex items-center gap-2">
              <ListFilter className="h-4 w-4 text-primary-500" />
              <span>Используйте фильтры ниже, чтобы найти нужную страницу.</span>
            </div>
            <Button type="button" size="sm" className="gap-2" onClick={openCreateDialog} disabled={createSubmitting || createDialogOpen}>
              <Plus className="h-4 w-4" />
              <span>Создать страницу</span>
            </Button>
          </div>
        </div>
      </header>

      <Card className="space-y-4 rounded-3xl border border-white/80 bg-white/95 p-5 shadow-sm dark:border-dark-700/70 dark:bg-dark-800">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-dark-300">
          <Search className="h-4 w-4" />
          Поиск и фильтры
        </div>
        <div className="flex flex-wrap items-stretch gap-3">
          <div className="flex flex-1 min-w-[240px] xl:flex-[2.2]">
            <Input
              aria-label="Поиск по страницам"
              placeholder="Поиск по названию или slug"
              value={filters.search}
              onChange={(event) => handleFilterChange('search', event.currentTarget.value)}
              className={FILTER_CONTROL_CLASS}
            />
          </div>
          <div className="flex flex-1 min-w-[160px] sm:flex-[1] xl:flex-[1.05]">
            <Select
              aria-label="Фильтр по типу страницы"
              value={filters.type}
              onChange={(event) => handleFilterChange('type', event.currentTarget.value as FiltersState['type'])}
              className={FILTER_CONTROL_CLASS}
            >
              {TYPE_OPTIONS.map((option) => (
                <option key={option.value || 'all'} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
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
              aria-label="Фильтр по закреплению"
              value={filters.pinned}
              onChange={(event) => handleFilterChange('pinned', event.currentTarget.value as PinnedFilter)}
              className={FILTER_CONTROL_CLASS}
            >
              {PINNED_OPTIONS.map((option) => (
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

      <div className="rounded-4xl border border-gray-100/70 bg-gray-50/80 p-4 shadow-inner dark:border-dark-700/70 dark:bg-dark-900/50 sm:p-5">
        <div className="grid gap-6 lg:grid-cols-12">
          <Card className="flex flex-col gap-0 rounded-3xl border border-white/80 bg-white/95 p-0 shadow-sm dark:border-dark-700/70 dark:bg-dark-800 lg:col-span-7 xl:col-span-8">
          <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4">
            <div>
              <h2 className="text-base font-semibold text-gray-900 dark:text-white">Страницы</h2>
              <p className="text-xs text-gray-500 dark:text-dark-200">
                {items.length
                  ? `Показываем ${items.length} страниц(ы) на этой странице выдачи.`
                  : 'Подберите фильтры, чтобы получить список страниц.'}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {loading && items.length > 0 ? (
                <span className="flex items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
                  <Spinner className="h-4 w-4" />
                  Обновляем...
                </span>
              ) : null}
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => {
                  clearError();
                  openCreateDialog();
                }}
                disabled={createSubmitting || createDialogOpen}
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
                Загружаем страницы...
              </div>
            ) : items.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-gray-200 py-12 text-center text-sm text-gray-500 dark:border-dark-700 dark:text-dark-200">
                <FileCode2 className="h-10 w-10 text-primary-400" />
                <div className="space-y-1">
                  <p>Каталог пуст.</p>
                  <p className="text-xs text-gray-400 dark:text-dark-300">
                    Создайте новую страницу или скорректируйте фильтры.
                  </p>
                </div>
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
            ) : (
                  <ul className="space-y-2">
                {items.map((pageItem) => {
                  const isSelected = selectedPage?.id === pageItem.id;
                  const isHome = pageItem.slug === '/' || pageItem.slug === 'main';
                  const isPinned = Boolean(pageItem.pinned);
                  return (
                    <li key={pageItem.id}>
                      <div
                        role="button"
                        tabIndex={0}
                        data-testid="site-page-item"
                        aria-pressed={isSelected}
                        aria-label={`Выбрать страницу ${pageItem.title}`}
                        onClick={() => setSelectedPage(pageItem)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault();
                            setSelectedPage(pageItem);
                          }
                        }}
                        className={clsx(
                          'group flex flex-col gap-3 rounded-2xl border px-5 py-4 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 dark:bg-dark-800/60 dark:focus-visible:ring-primary-300',
                          isSelected
                            ? 'border-primary-300 bg-primary-50/70 shadow-sm dark:border-primary-500/40 dark:bg-primary-500/10'
                            : 'border-transparent bg-gray-50/70 hover:border-primary-200/60 hover:bg-white dark:border-transparent dark:hover:bg-dark-700'
                        )}
                      >
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-sm font-semibold text-gray-900 dark:text-white">
                                {pageItem.title}
                              </span>
                              {isHome ? (
                                <Badge color="info" variant="soft" className="text-[10px] uppercase tracking-wide">
                                  Главная
                                </Badge>
                              ) : null}
                              {isPinned ? (
                                <Badge
                                  color="info"
                                  variant="solid"
                                  className="gap-1 text-[10px] uppercase tracking-wide"
                                >
                                  <Pin className="h-3 w-3" />
                                  Закреплена
                                </Badge>
                              ) : null}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-dark-200">
                              {getDisplaySlug(pageItem.slug)}
                            </div>
                          </div>
                          <div className="flex flex-wrap items-center justify-end gap-2">
                            {renderStatus(pageItem.status, pageItem.has_pending_review ?? false)}
                            {canDeletePage(pageItem) ? (
                              <Button
                                type="button"
                                size="sm"
                                variant="ghost"
                                className="text-rose-500 hover:text-rose-600 dark:text-rose-300 dark:hover:text-rose-200"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  handleOpenDeleteDialog(pageItem);
                                }}
                                aria-label="Удалить страницу"
                                disabled={deleteSubmitting && deleteDialogPage?.id === pageItem.id}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            ) : null}
                            <Button
                              as={Link}
                              to={`/management/site-editor/pages/${pageItem.id}`}
                              size="sm"
                              variant="ghost"
                              onClick={(event) => event.stopPropagation()}
                            >
                              Открыть
                            </Button>
                          </div>
                        </div>
                        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-gray-600 dark:text-dark-200">
                          <MetaItem label="Тип" value={typeLabel(pageItem.type)} />
                          <MetaItem label="Локаль" value={pageItem.locale || '—'} />
                          <MetaItem
                            label="Версии"
                            value={
                              pageItem.published_version != null || pageItem.draft_version != null
                                ? `v${pageItem.published_version ?? '—'} · draft ${pageItem.draft_version ?? '—'}`
                                : '—'
                            }
                          />
                          <MetaItem label="Ответственный" value={pageItem.owner || '—'} />
                          <MetaItem
                            label="Обновлена"
                            value={formatDateTime(pageItem.updated_at, { fallback: '—' })}
                          />
                          <MetaItem label="Закрепление" value={isPinned ? 'Да' : 'Нет'} />
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

          <Card className="space-y-4 rounded-3xl border border-white/80 bg-white/95 p-6 shadow-sm dark:border-dark-700/70 dark:bg-dark-800 lg:col-span-5 xl:col-span-4" data-testid="site-page-detail">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-gray-900 dark:text-white">Карточка страницы</h2>
              <p className="text-sm text-gray-500 dark:text-dark-200">
                Выберите страницу в списке, чтобы увидеть подробности и версии.
              </p>
            </div>
            {selectedPage ? (
              <Button
                type="button"
                size="xs"
                variant="ghost"
                onClick={triggerDetailReload}
                disabled={detailLoading}
              >
                {detailLoading ? 'Обновляем...' : 'Обновить детали'}
              </Button>
            ) : null}
          </div>
          {selectedPage ? (
            <div className="space-y-4 text-sm text-gray-700 dark:text-dark-100">
              <div>
                <div className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-300">Название</div>
                <div className="text-base font-semibold text-gray-900 dark:text-white">{selectedPage.title}</div>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
                  <span>{getDisplaySlug(selectedPage.slug)}</span>
                  {selectedPage.pinned ? (
                    <Badge color="info" variant="soft" className="inline-flex items-center gap-1">
                      <Pin className="h-3 w-3" />
                      Закреплена
                    </Badge>
                  ) : null}
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <DetailRow label="Тип" value={typeLabel(selectedPage.type)} />
                <DetailRow
                  label="Статус"
                  value={statusAppearance(selectedPage.status).label}
                  tone={statusAppearance(selectedPage.status).color}
                />
                <DetailRow label="Локаль" value={selectedPage.locale || '—'} />
                <DetailRow label="Ответственный" value={selectedPage.owner || '—'} />
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <DetailRow label="Версия (публик.)" value={selectedPage.published_version ?? '—'} />
                <DetailRow label="Версия черновика" value={selectedPage.draft_version ?? '—'} />
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <DetailRow
                  label="Обновлена"
                  value={formatDateTime(selectedPage.updated_at, { fallback: '—', withSeconds: true })}
                />
                <DetailRow
                  label="Ревью"
                  value={selectedPage.has_pending_review ? 'Ожидает' : '—'}
                  tone={selectedPage.has_pending_review ? 'warning' : undefined}
                />
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-300">
                    Глобальные блоки
                  </div>
                  {detailLoading ? <Spinner className="h-4 w-4 text-primary-500" /> : null}
                </div>
                {detailError ? (
                  <div className="rounded-2xl border border-rose-200/70 bg-rose-50/70 p-4 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                      <div className="space-y-2">
                        <p>{detailError}</p>
                        <div>
                  <Button size="xs" variant="outlined" onClick={triggerDetailReload}>
                            Повторить
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : attachedBlocks.length ? (
                  <ul className="space-y-3">
                    {attachedBlocks.map((block) => {
                      const statusMeta = globalBlockStatusAppearance(block.status);
                      const reviewMeta = reviewAppearance(block.review_status);
                      return (
                        <li key={block.key}>
                          <div className="space-y-3 rounded-2xl border border-gray-200 p-4 dark:border-dark-600">
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div>
                                <div className="text-sm font-semibold text-gray-900 dark:text-white">
                                  {block.title || block.key}
                                </div>
                                <div className="text-xs text-gray-500 dark:text-dark-200">{block.key}</div>
                              </div>
                              <div className="flex flex-wrap items-center gap-2">
                                <Badge color={statusMeta.color} variant="soft">
                                  {statusMeta.label}
                                </Badge>
                <Badge color={reviewMeta.color} variant="outline">
                  {reviewMeta.label}
                </Badge>
                              </div>
                            </div>
                            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-gray-600 dark:text-dark-200">
                              <MetaItem label="Секция" value={block.section || '—'} />
                              <MetaItem label="Локаль" value={block.locale || '—'} />
                              <MetaItem
                                label="Версии"
                                value={`v${block.published_version ?? '—'} · draft ${block.draft_version ?? '—'}`}
                              />
                              <MetaItem
                                label="Обновлён"
                                value={formatDateTime(block.updated_at, { fallback: '—' })}
                              />
                              <MetaItem label="Изменил" value={block.updated_by || '—'} />
                              <MetaItem
                                label="Публикация"
                                value={block.requires_publisher ? 'Требует publisher' : '—'}
                              />
                            </div>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <div className="rounded-2xl border border-dashed border-gray-200 p-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-200">
                    Нет связанных глобальных блоков.
                  </div>
                )}
              </div>
              <SitePageHistoryPanel
                entries={history}
                loading={historyLoading}
                error={historyError}
                onRestore={handleRestoreVersion}
                restoringVersion={restoringVersion}
                onRefresh={triggerHistoryReload}
              />
              <SitePageAuditPanel
                entries={auditEntries}
                loading={auditLoading}
                error={auditError}
                onRefresh={triggerAuditReload}
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-gray-200 p-6 text-center dark:border-dark-600">
              <FileCode2 className="h-10 w-10 text-primary-400" />
              <div className="text-sm text-gray-600 dark:text-dark-200">Выберите страницу, чтобы посмотреть детали.</div>
            </div>
          )}
        </Card>
        </div>
      </div>
      <Dialog
        open={createDialogOpen}
        onClose={closeCreateDialog}
        title="Создать страницу"
        footer={(
          <>
            <Button variant="outlined" color="neutral" onClick={closeCreateDialog} disabled={createSubmitting}>
              Отмена
            </Button>
            <Button onClick={handleSubmitCreate} disabled={createSubmitting}>
              {createSubmitting ? 'Создание…' : 'Создать'}
            </Button>
          </>
        )}
      >
        <div className="space-y-4">
          {createError ? (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
              {createError}
            </div>
          ) : null}
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200">
              <span>Название</span>
              <Input
                value={createForm.title}
                onChange={(event) => handleCreateFieldChange('title', event.currentTarget.value)}
                placeholder="Главная"
              />
            </label>
            <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200">
              <span>Слаг</span>
              <Input
                value={createForm.slug}
                onChange={(event) => handleCreateFieldChange('slug', event.currentTarget.value)}
                onBlur={handleSlugBlur}
                placeholder="/new-page"
              />
              <span className="text-[11px] font-normal normal-case text-gray-400 dark:text-dark-300">
                Задайте относительный путь. Мы автоматически добавим слэш в начале.
              </span>
            </label>
            <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200">
              <span>Тип</span>
              <Select
                value={createForm.type}
                onChange={(event) => handleCreateFieldChange('type', event.currentTarget.value as SitePageType)}
              >
                {TYPE_OPTIONS.filter((option) => option.value).map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </label>
            <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200">
              <span>Локаль</span>
              <Input
                value={createForm.locale}
                onChange={(event) => handleCreateFieldChange('locale', event.currentTarget.value)}
                placeholder="ru"
              />
            </label>
            <label className="space-y-1 text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-200 sm:col-span-2">
              <span>Ответственный</span>
              <Input
                value={createForm.owner}
                onChange={(event) => handleCreateFieldChange('owner', event.currentTarget.value)}
                placeholder="marketing"
              />
            </label>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-600 dark:bg-dark-700 dark:text-dark-200">
            <div>
              <div className="font-semibold uppercase tracking-wide">Закрепить</div>
              <div className="text-[11px] font-normal normal-case text-gray-400 dark:text-dark-300">
                Страница появится в закреплённых разделах.
              </div>
            </div>
            <Switch checked={createForm.pinned} onChange={(event: any) => handleCreateFieldChange('pinned', Boolean(event.currentTarget?.checked))} />
          </div>
        </div>
      </Dialog>
      <Dialog
        open={Boolean(deleteDialogPage)}
        onClose={handleCloseDeleteDialog}
        title="Удалить страницу"
        footer={(
          <>
            <Button variant="outlined" color="neutral" onClick={handleCloseDeleteDialog} disabled={deleteSubmitting}>
              Отмена
            </Button>
            <Button
              variant="ghost"
              className="text-rose-600 hover:text-rose-500 dark:text-rose-300 dark:hover:text-rose-200"
              onClick={handleConfirmDelete}
              disabled={deleteSubmitting}
            >
              {deleteSubmitting ? 'Удаление…' : 'Удалить'}
            </Button>
          </>
        )}
      >
        <div className="space-y-3 text-sm text-gray-600 dark:text-dark-200">
          {deleteError ? (
            <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-xs text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200">
              {deleteError}
            </div>
          ) : null}
          <p>Вы действительно хотите удалить страницу «{deleteDialogPage?.title ?? ''}»?</p>
          <p className="text-xs text-gray-400 dark:text-dark-300">Действие необратимо: черновики, история версий и привязки будут удалены автоматически.</p>
        </div>
      </Dialog>
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
      <div className={clsx('text-sm font-medium', color)}>{value}</div>
    </div>
  );
}

function getDisplaySlug(slug?: string | null): string {
  if (!slug) return '—';
  const normalized = slug.trim();
  if (!normalized || normalized === '/' || normalized === 'main') {
    return '/';
  }
  return normalized.startsWith('/') ? normalized : `/${normalized}`;
}

type MetaItemProps = {
  label: string;
  value: React.ReactNode;
};

function MetaItem({ label, value }: MetaItemProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] uppercase tracking-wide text-gray-400 dark:text-dark-300">{label}</span>
      <span className="text-xs font-medium text-gray-700 dark:text-dark-50">{value}</span>


    </div>
  );
}


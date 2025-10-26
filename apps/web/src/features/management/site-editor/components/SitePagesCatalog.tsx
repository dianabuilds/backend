import React from 'react';
import { Link } from 'react-router-dom';
import clsx from 'clsx';
import { AlertTriangle, FileCode2, ListFilter, Search, Users } from '@icons';
import { Badge, Button, Card, Input, Select, Spinner, TablePagination } from '@ui';
import * as Table from '@ui/table';
import type { PlatformAdminQuickLink } from '@shared/layouts/management';
import { PlatformAdminFrame } from '@shared/layouts/management';
import { usePaginatedQuery } from '@shared/hooks/usePaginatedQuery';
import { extractErrorMessage } from '@shared/utils/errors';
import { formatDateTime } from '@shared/utils/format';
import { pushGlobalToast } from '@shared/ui/toastBus';
import { managementSiteEditorApi } from '@shared/api/management';
import { statusAppearance, typeLabel } from '../utils/pageHelpers';
import { SitePageHistoryPanel } from './PageHistoryPanel';
import { SitePageAuditPanel } from './PageAuditPanel';
import type {
  SitePageListResponse,
  SitePageStatus,
  SitePageSummary,
  SitePageType,
  SitePageVersion,
  SiteAuditEntry,
} from '@shared/types/management';

type SortOrder = 'updated_at_desc' | 'updated_at_asc' | 'title_asc';

type DraftFilter = 'all' | 'with' | 'without';

type FiltersState = {
  search: string;
  type: '' | SitePageType;
  status: '' | SitePageStatus;
  locale: string;
  hasDraft: DraftFilter;
  sort: SortOrder;
};

const INITIAL_FILTERS: FiltersState = {
  search: '',
  type: '',
  status: '',
  locale: '',
  hasDraft: 'all',
  sort: 'updated_at_desc',
};

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

const SORT_OPTIONS: Array<{ value: SortOrder; label: string }> = [
  { value: 'updated_at_desc', label: 'По обновлению (новые)' },
  { value: 'updated_at_asc', label: 'По обновлению (старые)' },
  { value: 'title_asc', label: 'По названию (A–Я)' },
];

const ROLE_HINT = (
  <div className="space-y-2 text-sm leading-relaxed">
    <p>
      Доступ к каталогу страниц есть у ролей <code>site.viewer</code> и выше. Редактирование и публикация требуют{' '}
      <code>site.editor</code> или <code>site.publisher</code>.
    </p>
    <p className="text-xs text-gray-500 dark:text-dark-200">
      Пользователи без прав редактирования видят только опубликованные страницы и черновики собственных страниц.
    </p>
  </div>
);

const QUICK_LINKS: PlatformAdminQuickLink[] = [
  {
    label: 'ADR: Редактор сайта',
    href: '/docs/adr/2025-10-25-site-editor',
    description: 'Этапы внедрения, зоны ответственности и критерии готовности.',
  },
  {
    label: 'API каталога страниц',
    href: '/docs/site-editor-api',
    description: 'Описание параметров фильтрации, сортировки и примеры ответов.',
  },
];

const HELP_TEXT = (
  <span className="text-sm leading-relaxed text-gray-600 dark:text-dark-200">
    Фильтруйте страницы по типу, статусу и черновикам, чтобы готовить релизы. Выделите страницу в таблице, чтобы увидеть
    детали и версии.
  </span>
);

function draftFilterToBoolean(filter: DraftFilter): boolean | undefined {
  if (filter === 'with') return true;
  if (filter === 'without') return false;
  return undefined;
}

export default function SitePagesCatalog(): React.ReactElement {
  const [filters, setFilters] = React.useState<FiltersState>({ ...INITIAL_FILTERS });
  const [selectedPage, setSelectedPage] = React.useState<SitePageSummary | null>(null);
  const [history, setHistory] = React.useState<SitePageVersion[]>([]);
  const [historyLoading, setHistoryLoading] = React.useState(false);
  const [historyError, setHistoryError] = React.useState<string | null>(null);
  const [auditEntries, setAuditEntries] = React.useState<SiteAuditEntry[]>([]);
  const [auditLoading, setAuditLoading] = React.useState(false);
  const [auditError, setAuditError] = React.useState<string | null>(null);
  const [restoringVersion, setRestoringVersion] = React.useState<number | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = React.useState(0);
  const [auditRefreshKey, setAuditRefreshKey] = React.useState(0);
  const selectedPageId = selectedPage?.id ?? null;
  const triggerHistoryReload = React.useCallback(() => {
    setHistoryRefreshKey((key) => key + 1);
  }, []);
  const triggerAuditReload = React.useCallback(() => {
    setAuditRefreshKey((key) => key + 1);
  }, []);

  // eslint-disable-next-line no-console

  const {
    items,
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
    initialPageSize: 20,
    dependencies: [
      filters.search,
      filters.type,
      filters.status,
      filters.locale,
      filters.hasDraft,
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
    <PlatformAdminFrame
      title="Каталог страниц"
      description={(
        <span className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-dark-200">
          <ListFilter className="h-4 w-4 text-primary-500" />
          Управление страницами публичного сайта, черновиками и статусами публикаций.
        </span>
      )}
      roleHint={ROLE_HINT}
      quickLinks={QUICK_LINKS}
      helpText={HELP_TEXT}
    >
      <Card className="space-y-4 p-5">
        <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.24em] text-gray-500 dark:text-dark-300">
          <Search className="h-4 w-4" />
          Поиск и фильтры
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          <Input
            aria-label="Поиск по страницам"
            placeholder="Поиск по названию или slug"
            value={filters.search}
            onChange={(event) => handleFilterChange('search', event.currentTarget.value)}
          />
          <Select
            aria-label="Фильтр по типу страницы"
            value={filters.type}
            onChange={(event) => handleFilterChange('type', event.currentTarget.value as FiltersState['type'])}
          >
            {TYPE_OPTIONS.map((option) => (
              <option key={option.value || 'all'} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Фильтр по статусу"
            value={filters.status}
            onChange={(event) => handleFilterChange('status', event.currentTarget.value as FiltersState['status'])}
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value || 'all'} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <Select
            aria-label="Фильтр по черновикам"
            value={filters.hasDraft}
            onChange={(event) => handleFilterChange('hasDraft', event.currentTarget.value as DraftFilter)}
          >
            {DRAFT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
          <div className="flex gap-2">
            <Input
              aria-label="Фильтр по локали"
              placeholder="Локаль (ru, en...)"
              value={filters.locale}
              onChange={(event) => handleFilterChange('locale', event.currentTarget.value)}
            />
            <Select
              aria-label="Сортировка"
              value={filters.sort}
              onChange={(event) => handleFilterChange('sort', event.currentTarget.value as SortOrder)}
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
        <Card className="space-y-4 p-0 lg:col-span-8">
          <div className="flex items-center justify-between px-5 py-4">
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">Страницы</h2>
            <button
              type="button"
              className="text-sm font-medium text-primary-600 hover:text-primary-500 dark:text-primary-300"
              onClick={() => { void refresh(); }}
            >
              Обновить
            </button>
          </div>
          <div className="hide-scrollbar overflow-x-auto">
            <Table.Table
              preset="management"
              hover
              zebra
              headerSticky
              className="min-w-[840px]"
            >
              <Table.THead>
                <Table.TR>
                  <Table.TH className="min-w-[220px]">Страница</Table.TH>
                  <Table.TH className="min-w-[120px]">Тип</Table.TH>
                  <Table.TH className="min-w-[150px]">Статус</Table.TH>
                  <Table.TH className="min-w-[100px]">Локаль</Table.TH>
                  <Table.TH className="min-w-[160px]">Ответственный</Table.TH>
                  <Table.TH className="min-w-[140px]">Версии</Table.TH>
                  <Table.TH className="min-w-[160px]">Обновлена</Table.TH>
                  <Table.TH className="min-w-[140px]">Действия</Table.TH>
                </Table.TR>
              </Table.THead>
              <Table.TBody>
                {loading ? (
                  <Table.TableLoading rows={4} colSpan={8} />
                ) : error ? (
                  <Table.TableError
                    colSpan={8}
                    title="Не удалось загрузить страницы"
                    description={error}
                    icon={<AlertTriangle className="h-6 w-6 text-error" />}
                    onRetry={() => {
                      clearError();
                      void refresh();
                    }}
                  />
                ) : items.length === 0 ? (
                  <Table.TableEmpty
                    colSpan={8}
                    title="Каталог пуст"
                    description="Создайте новую страницу или измените фильтры, чтобы увидеть результаты."
                    icon={<FileCode2 className="h-6 w-6 text-primary-500" />}
                  />
                ) : (
                  items.map((pageItem) => {
                    const isSelected = selectedPage?.id === pageItem.id;
                    return (
                      <Table.TR
                        key={pageItem.id}
                        onClick={() => setSelectedPage(pageItem)}
                        className={clsx(
                          'cursor-pointer',
                          isSelected && 'bg-primary-50/60 hover:bg-primary-50/70 dark:bg-primary-500/10',
                        )}
                      >
                        <Table.TD>
                          <div className="flex flex-col gap-1">
                            <span className="font-semibold text-gray-900 dark:text-white">{pageItem.title}</span>
                            <span className="text-xs text-gray-500 dark:text-dark-200">
                              <code className="rounded bg-gray-100 px-1.5 py-0.5 text-[11px] text-gray-700 dark:bg-dark-700 dark:text-dark-100">
                                {pageItem.slug}
                              </code>
                            </span>
                          </div>
                        </Table.TD>
                        <Table.TD className="text-gray-600 dark:text-dark-100">{typeLabel(pageItem.type)}</Table.TD>
                        <Table.TD>{renderStatus(pageItem.status, pageItem.has_pending_review ?? false)}</Table.TD>
                        <Table.TD className="text-gray-600 dark:text-dark-100">{pageItem.locale || '—'}</Table.TD>
                        <Table.TD className="text-gray-600 dark:text-dark-100">
                          {pageItem.owner || (
                            <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                              <Users className="h-4 w-4" />
                              Не назначен
                            </span>
                          )}
                        </Table.TD>
                        <Table.TD className="text-gray-600 dark:text-dark-100">
                          <div className="flex flex-col text-xs">
                            <span>Опубликовано: {pageItem.published_version ?? '—'}</span>
                            <span>Черновик: {pageItem.draft_version ?? '—'}</span>
                          </div>
                        </Table.TD>
                        <Table.TD className="text-gray-600 dark:text-dark-100">
                          {formatDateTime(pageItem.updated_at, { fallback: '—', withSeconds: true })}
                        </Table.TD>
                        <Table.TD className="text-right">
                          <Button
                            as={Link}
                            to={`/management/site-editor/pages/${pageItem.id}`}
                            size="sm"
                            variant="ghost"
                            onClick={(event) => event.stopPropagation()}
                          >
                            Открыть
                          </Button>
                        </Table.TD>
                      </Table.TR>
                    );
                  })
                )}
              </Table.TBody>
            </Table.Table>
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
                totalItems={typeof items.length === 'number' && !hasNext ? (page - 1) * pageSize + items.length : undefined}
                hasNext={hasNext}
                summaryPrefix="Показываем"
              />
            )}
          </div>
        </Card>

        <Card className="space-y-4 p-6 lg:col-span-4" data-testid="site-page-detail">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-gray-900 dark:text-white">Карточка страницы</h2>
              <p className="text-sm text-gray-500 dark:text-dark-200">
                Выберите страницу в списке, чтобы увидеть подробности и версии.
              </p>
            </div>
          </div>
          {selectedPage ? (
            <div className="space-y-4 text-sm text-gray-700 dark:text-dark-100">
              <div>
                <div className="text-xs uppercase tracking-wide text-gray-400 dark:text-dark-300">Название</div>
                <div className="text-base font-semibold text-gray-900 dark:text-white">{selectedPage.title}</div>
                <div className="mt-1 text-xs text-gray-500 dark:text-dark-200">{selectedPage.slug}</div>
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
    </PlatformAdminFrame>
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

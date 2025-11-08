import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Search } from '@icons';
import { Badge, Button, Card, Input, Select, Spinner } from '@ui';
import { managementSiteEditorApi } from '@shared/api/management';
import type { SiteBlock, SiteBlockStatus } from '@shared/types/management';
import { extractErrorMessage } from '@shared/utils/errors';
import { formatDateTime } from '@shared/utils/format';
import { BLOCK_SCOPE_OPTIONS, STATUS_META, SCOPE_LABELS } from './SiteBlockLibraryPage.constants';
import type { FilterValue } from './SiteBlockLibrary.types';

const PAGE_SIZE = 50;

type BlockFiltersState = {
  search: string;
  status: FilterValue<SiteBlockStatus>;
  scope: FilterValue<NonNullable<SiteBlock['scope']>>;
};

const INITIAL_BLOCK_FILTERS: BlockFiltersState = {
  search: '',
  status: 'all',
  scope: 'all',
};

export default function SiteBlockLibraryPage(): React.ReactElement {
  const navigate = useNavigate();
  const [blocks, setBlocks] = React.useState<SiteBlock[]>([]);
  const [blocksLoading, setBlocksLoading] = React.useState(false);
  const [blocksError, setBlocksError] = React.useState<string | null>(null);
  const [blockFilters, setBlockFilters] = React.useState<BlockFiltersState>(INITIAL_BLOCK_FILTERS);
  const [blockRefreshKey, setBlockRefreshKey] = React.useState(0);

  React.useEffect(() => {
    const controller = new AbortController();
    setBlocksLoading(true);
    setBlocksError(null);

    managementSiteEditorApi
      .fetchSiteBlocks(
        {
          pageSize: PAGE_SIZE,
          status: blockFilters.status !== 'all' ? (blockFilters.status as SiteBlockStatus) : undefined,
          scope: blockFilters.scope !== 'all' ? blockFilters.scope : undefined,
          query: blockFilters.search.trim() || undefined,
          sort: 'updated_at_desc',
          includeData: false,
        },
        { signal: controller.signal },
      )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        const items = Array.isArray(response.items) ? response.items : [];
        setBlocks(items.filter((item) => item?.is_template !== true));
      })
      .catch((err) => {
        if ((err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setBlocks([]);
        setBlocksError(extractErrorMessage(err, 'Не удалось загрузить блоки'));
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setBlocksLoading(false);
        }
      });

    return () => controller.abort();
  }, [blockFilters.scope, blockFilters.search, blockFilters.status, blockRefreshKey]);

  const blockHasFilters = React.useMemo(
    () =>
      Boolean(
        blockFilters.search.trim() || blockFilters.status !== 'all' || blockFilters.scope !== 'all',
      ),
    [blockFilters.search, blockFilters.scope, blockFilters.status],
  );

  const handleBlockFilterChange = React.useCallback(
    (field: keyof BlockFiltersState, value: BlockFiltersState[typeof field]) => {
      setBlockFilters((current) => ({
        ...current,
        [field]: value,
      }));
    },
    [],
  );

  const resetBlockFilters = React.useCallback(() => {
    setBlockFilters(INITIAL_BLOCK_FILTERS);
  }, []);

  const handleBlockRefresh = React.useCallback(() => {
    setBlockRefreshKey((value) => value + 1);
  }, []);

  return (
    <div className="space-y-6" data-testid="site-block-library-page">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Библиотека блоков</h1>
          <p className="text-sm text-gray-600 dark:text-dark-200">
            Просматривайте актуальные блоки и переходите к редактированию нужного экземпляра.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="ghost"
            color="neutral"
            size="sm"
            onClick={resetBlockFilters}
            disabled={!blockHasFilters}
          >
            Сбросить фильтры
          </Button>
          <Button variant="ghost" color="neutral" size="sm" onClick={handleBlockRefresh}>
            {blocksLoading ? 'Обновляем…' : 'Обновить'}
          </Button>
        </div>
      </header>

      <Card padding="sm" className="space-y-4 bg-white/95 shadow-sm dark:bg-dark-800/80">
        <div className="grid gap-3 md:grid-cols-[1.5fr_1fr_1fr]">
          <Input
            value={blockFilters.search}
            onChange={(event) => handleBlockFilterChange('search', event.target.value)}
            placeholder="Поиск по названию, ключу или секции"
            prefix={<Search className="h-4 w-4 text-gray-400" />}
          />
          <Select
            value={blockFilters.status}
            onChange={(event) =>
              handleBlockFilterChange('status', event.target.value as BlockFiltersState['status'])
            }
          >
            <option value="all">Любой статус</option>
            {Object.entries(STATUS_META).map(([value, meta]) => (
              <option key={value} value={value}>
                {meta.label}
              </option>
            ))}
          </Select>
          <Select
            value={blockFilters.scope}
            onChange={(event) =>
              handleBlockFilterChange('scope', event.target.value as BlockFiltersState['scope'])
            }
          >
            <option value="all">Любая область</option>
            {BLOCK_SCOPE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>

        {blocksError ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-400/40 dark:bg-rose-400/10 dark:text-rose-100">
            {blocksError}
          </div>
        ) : null}

        <div className="space-y-2">
          {blocksLoading ? (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Spinner className="h-4 w-4" /> Загружаем блоки…
            </div>
          ) : blocks.length ? (
            blocks.map((block) => {
              const statusMeta = STATUS_META[block.status] ?? STATUS_META.draft;
              const scopeLabel = SCOPE_LABELS[block.scope ?? 'unknown'] ?? '—';
              return (
                <button
                  key={block.id}
                  type="button"
                  onClick={() => navigate(`/management/site-editor/blocks/${block.id}`)}
                  className="w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-left shadow-sm transition hover:border-primary-300 dark:border-dark-700 dark:bg-dark-800"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 space-y-1">
                      <div className="text-sm font-semibold text-gray-900 dark:text-white">
                        {block.title || block.key}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-dark-200">
                        {block.section || '—'} · {scopeLabel}
                      </div>
                      <div className="font-mono text-[11px] text-gray-400 dark:text-dark-300">
                        {block.key}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1 text-xs text-gray-500 dark:text-dark-200">
                      <Badge color={statusMeta.color} variant="soft">
                        {statusMeta.label}
                      </Badge>
                      <span>
                        Обновлён {block.updated_at ? formatDateTime(block.updated_at, { fallback: '—' }) : '—'}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })
          ) : (
            <div className="rounded-2xl border border-dashed border-gray-200 bg-gray-50 p-6 text-center text-sm text-gray-500 dark:border-dark-700 dark:bg-dark-900/40 dark:text-dark-200">
              Блоки не найдены. Измените фильтры или создайте блок в другом разделе.
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

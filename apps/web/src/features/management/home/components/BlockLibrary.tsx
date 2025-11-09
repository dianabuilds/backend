import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, ExternalLink, RefreshCcw, Search } from '@icons';
import { Badge, Button, Card, Input, useToast } from '@ui';
import { extractErrorMessage } from '@shared/utils/errors';
import type { SiteBlock } from '@shared/types/management';
import { managementSiteEditorApi } from '@shared/api/management';
import { REVIEW_STATUS_META } from '../../site-editor/components/SiteBlockLibraryPage.constants';
import { useHomeEditorContext } from '../HomeEditorContext';
import { listBlockDefinitions } from '../blockDefinitions';
import { createBlockFromSiteBlock } from '../createBlockFromSiteBlock';

const TYPE_LABELS = listBlockDefinitions().reduce<Record<string, string>>((acc, definition) => {
  acc[definition.type] = definition.label;
  return acc;
}, {});

type LibraryState = {
  loading: boolean;
  error: string | null;
  blocks: SiteBlock[];
};

const INITIAL_STATE: LibraryState = {
  loading: false,
  error: null,
  blocks: [],
};

function formatLocales(block: SiteBlock): string {
  const primary = (block.locale ?? block.default_locale ?? '—').toUpperCase();
  if (!Array.isArray(block.available_locales) || !block.available_locales.length) {
    return primary;
  }
  const extras = block.available_locales
    .map((locale) => locale?.trim().toUpperCase())
    .filter((locale) => locale && locale.length && locale !== primary);
  if (!extras.length) {
    return primary;
  }
  return `${primary}, ${extras.join(', ')}`;
}

const SECTION_ACCENTS: Record<
  string,
  { marker: string; badge: string; card: string; locale: string }
> = {
  hero: {
    marker: 'bg-indigo-400 dark:bg-indigo-500',
    badge: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-100',
    card: 'bg-indigo-50/60 dark:bg-indigo-500/10',
    locale: 'text-indigo-700 dark:text-indigo-100',
  },
  header: {
    marker: 'bg-emerald-400 dark:bg-emerald-500',
    badge: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-100',
    card: 'bg-emerald-50/60 dark:bg-emerald-500/10',
    locale: 'text-emerald-700 dark:text-emerald-100',
  },
  footer: {
    marker: 'bg-orange-400 dark:bg-orange-500',
    badge: 'bg-orange-50 text-orange-700 dark:bg-orange-500/20 dark:text-orange-100',
    card: 'bg-orange-50/60 dark:bg-orange-500/10',
    locale: 'text-orange-700 dark:text-orange-100',
  },
  default: {
    marker: 'bg-primary-400 dark:bg-primary-500',
    badge: 'bg-primary-50 text-primary-700 dark:bg-primary-500/20 dark:text-primary-100',
    card: 'bg-primary-50/60 dark:bg-primary-500/10',
    locale: 'text-primary-700 dark:text-primary-100',
  },
};

function BlockRow({
  block,
  saving,
  onAttach,
}: {
  block: SiteBlock;
  saving: boolean;
  onAttach: (block: SiteBlock) => void;
}): React.ReactElement {
  const reviewMeta =
    block.review_status && block.review_status !== 'none' ? REVIEW_STATUS_META[block.review_status] : null;
  const sectionLabel = TYPE_LABELS[block.section ?? ''] ?? block.section ?? 'Блок';
  const accent = SECTION_ACCENTS[block.section ?? ''] ?? SECTION_ACCENTS.default;

  const handleAttach = React.useCallback(() => {
    if (saving) {
      return;
    }
    onAttach(block);
  }, [block, onAttach, saving]);

  const handleKeyDown = React.useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (saving) {
        return;
      }
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        onAttach(block);
      }
    },
    [block, onAttach, saving],
  );

  const stopPropagation = React.useCallback((event: React.MouseEvent) => {
    event.stopPropagation();
  }, []);

  return (
    <div
      role="button"
      tabIndex={saving ? -1 : 0}
      aria-disabled={saving}
      onClick={handleAttach}
      onKeyDown={handleKeyDown}
      className={`group flex w-full items-start gap-3 rounded-xl border border-gray-200/80 px-3 py-2 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-primary-300 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 dark:border-dark-700/70 ${
        accent.card
      } ${saving ? 'cursor-not-allowed opacity-60 hover:-translate-y-0' : ''}`}
    >
      <span className={`mt-0.5 h-8 w-1 rounded-full ${accent.marker}`} aria-hidden="true" />
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="truncate text-sm font-semibold text-gray-900 dark:text-dark-50">
            {block.title || block.key}
          </span>
          <span
            className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${accent.badge}`}
          >
            {sectionLabel}
          </span>
          {reviewMeta ? (
            <Badge color={reviewMeta.color} variant="outline">
              {reviewMeta.label}
            </Badge>
          ) : null}
        </div>
        <div className="flex flex-wrap items-center gap-2 text-[11px] uppercase tracking-wide text-gray-500 dark:text-dark-200">
          <span className="font-mono text-xs text-gray-700 dark:text-dark-100">{block.key || block.id}</span>
          <span className="opacity-40">•</span>
          <span className={accent.locale}>{formatLocales(block)}</span>
        </div>
      </div>
      <Link
        to={`/management/site-editor/blocks/${block.id}`}
        onClick={stopPropagation}
        className="ml-auto flex h-7 w-7 items-center justify-center rounded-full text-gray-400 transition hover:bg-white/60 hover:text-primary-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-400 dark:text-dark-200 dark:hover:bg-dark-700/80 dark:hover:text-primary-300"
        aria-label={`Открыть блок ${block.title || block.key}`}
      >
        <ExternalLink className="h-3.5 w-3.5" />
      </Link>
    </div>
  );
}

export function BlockLibraryPanel(): React.ReactElement {
  const { data, setBlocks, selectBlock, saving, activeLocale } = useHomeEditorContext();
  const { pushToast } = useToast();
  const [query, setQuery] = React.useState('');
  const [state, setState] = React.useState<LibraryState>(INITIAL_STATE);
  const [refreshKey, setRefreshKey] = React.useState(0);

  React.useEffect(() => {
    const controller = new AbortController();
    setState((prev) => ({ ...prev, loading: true, error: null }));
    managementSiteEditorApi
      .fetchSiteBlocks(
        {
          status: 'published',
          pageSize: 200,
          sort: 'updated_at_desc',
          includeData: false,
          isTemplate: false,
        },
        { signal: controller.signal },
      )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        const items = Array.isArray(response.items) ? response.items : [];
        setState({
          loading: false,
          error: null,
          blocks: items,
        });
      })
      .catch((error) => {
        if (controller.signal.aborted) {
          return;
        }
        setState({
          loading: false,
          error: extractErrorMessage(error, 'Не удалось загрузить библиотеку блоков'),
          blocks: [],
        });
      });
    return () => controller.abort();
  }, [refreshKey]);

  const filteredBlocks = React.useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return state.blocks;
    }
    return state.blocks.filter((block) => {
      const haystack = [
        block.title,
        block.key,
        block.section,
        block.locale,
        block.default_locale,
        block.available_locales?.join(' '),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(normalized);
    });
  }, [query, state.blocks]);

  const handleSearchChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(event.target.value);
  }, []);

  const refreshLibrary = React.useCallback(() => {
    setRefreshKey((value) => value + 1);
  }, []);

  const totalBlocks = state.blocks.length;
  const filteredCount = filteredBlocks.length;
  const showEmptyState = !state.loading && filteredCount === 0;

  const handleAttach = React.useCallback(
    (siteBlock: SiteBlock) => {
      const nextBlock = createBlockFromSiteBlock({
        siteBlock,
        existingBlocks: data.blocks,
        preferredLocale: activeLocale,
      });
      if (!nextBlock) {
        pushToast({ intent: 'error', description: 'Этот блок пока нельзя добавить' });
        return;
      }
      setBlocks([...data.blocks, nextBlock]);
      selectBlock(nextBlock.id);
      pushToast({ intent: 'success', description: `Блок «${siteBlock.title || siteBlock.key}» добавлен` });
    },
    [activeLocale, data.blocks, pushToast, selectBlock, setBlocks],
  );

  return (
    <Card padding="sm" className="flex h-full flex-col gap-4 bg-white/95 shadow-sm dark:bg-dark-800/80">
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">Библиотека блоков</h3>
        <p className="text-xs text-gray-500 dark:text-dark-200">
          Блоки берутся из опубликованных элементов библиотеки и не содержат ручного контента.
        </p>
      </div>
      <Input
        value={query}
        onChange={handleSearchChange}
        placeholder="Поиск по названию, ключу или секции"
        prefix={<Search className="h-4 w-4 text-gray-400" />}
      />
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-dark-300">
        <span>
          Найдено {filteredCount} из {totalBlocks}
        </span>
        <Button
          type="button"
          size="xs"
          variant="ghost"
          color="neutral"
          disabled={state.loading}
          onClick={refreshLibrary}
          className="inline-flex items-center gap-1.5"
        >
          <RefreshCcw className="h-3.5 w-3.5" aria-hidden="true" />
          <span>Обновить</span>
        </Button>
      </div>
      {state.error ? (
        <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-500/50 dark:bg-rose-500/10 dark:text-rose-100">
          <AlertTriangle className="mt-0.5 h-4 w-4" />
          <div className="flex-1">
            <p>{state.error}</p>
            <Button type="button" size="xs" variant="ghost" color="neutral" onClick={refreshLibrary}>
              Повторить попытку
            </Button>
          </div>
        </div>
      ) : null}
      <div className="scrollbar-thin -mr-2 flex-1 space-y-2 overflow-y-auto pr-1">
        {showEmptyState ? (
          <div className="flex h-32 items-center justify-center rounded-xl border border-dashed border-gray-200 bg-gray-50 p-4 text-center text-sm text-gray-500 dark:border-dark-600 dark:bg-dark-800/40 dark:text-dark-200">
            По запросу ничего не найдено.
          </div>
        ) : (
          filteredBlocks.map((block) => (
            <BlockRow key={block.id} block={block} saving={saving} onAttach={handleAttach} />
          ))
        )}
      </div>
      <Button
        as={Link}
        to="/management/site-editor/library"
        variant="ghost"
        color="neutral"
        size="sm"
        className="w-full justify-center"
      >
        Открыть полную библиотеку
      </Button>
    </Card>
  );
}

export default BlockLibraryPanel;

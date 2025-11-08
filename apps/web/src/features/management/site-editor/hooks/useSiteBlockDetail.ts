import * as React from 'react';
import { managementSiteEditorApi } from '@shared/api/management';
import { extractErrorMessage } from '@shared/utils/errors';
import type {
  SiteBlock,
  SiteBlockHistoryItem,
  SiteBlockUsage,
  SiteBlockWarning,
} from '@shared/types/management';

const HISTORY_PAGE_SIZE = 20;

type HistoryState = {
  items: SiteBlockHistoryItem[];
  total: number;
  loading: boolean;
  loadingMore: boolean;
  error: string | null;
};

type HistoryActions = {
  refresh: () => void;
  loadMore: () => Promise<void>;
};

type BlockDetailState = {
  block: SiteBlock | null;
  usage: SiteBlockUsage[];
  warnings: SiteBlockWarning[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
  history: HistoryState & HistoryActions;
  mutate: (next: {
    block?: SiteBlock | null;
    usage?: SiteBlockUsage[];
    warnings?: SiteBlockWarning[];
  }) => void;
};

function createEmptyHistoryState(): HistoryState {
  return {
    items: [],
    total: 0,
    loading: false,
    loadingMore: false,
    error: null,
  };
}

export function useSiteBlockDetail(blockId: string | null): BlockDetailState {
  const [detail, setDetail] = React.useState<{
    block: SiteBlock | null;
    usage: SiteBlockUsage[];
    warnings: SiteBlockWarning[];
    loading: boolean;
    error: string | null;
  }>({
    block: null,
    usage: [],
    warnings: [],
    loading: false,
    error: null,
  });
  const [history, setHistory] = React.useState<HistoryState>(createEmptyHistoryState);
  const [refreshToken, setRefreshToken] = React.useState(0);
  const [historyRefreshKey, setHistoryRefreshKey] = React.useState(0);

  React.useEffect(() => {
    if (!blockId) {
      setDetail({
        block: null,
        usage: [],
        warnings: [],
        loading: false,
        error: null,
      });
      return;
    }
    const controller = new AbortController();
    setDetail((prev) => ({ ...prev, loading: true, error: null }));
    Promise.resolve(
      managementSiteEditorApi.fetchSiteBlock(blockId, { signal: controller.signal }),
    )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        if (response && response.block) {
          setDetail({
            block: response.block,
            usage: Array.isArray(response.usage) ? response.usage : [],
            warnings: Array.isArray(response.warnings) ? response.warnings : [],
            loading: false,
            error: null,
          });
        } else {
          setDetail({
            block: null,
            usage: [],
            warnings: [],
            loading: false,
            error: null,
          });
        }
      })
      .catch((err) => {
        if ((err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setDetail({
          block: null,
          usage: [],
          warnings: [],
          loading: false,
          error: extractErrorMessage(err, 'Не удалось загрузить блок'),
        });
      });

    return () => controller.abort();
  }, [blockId, refreshToken]);

  React.useEffect(() => {
    if (!blockId) {
      setHistory(createEmptyHistoryState());
      return;
    }
    const controller = new AbortController();
    setHistory((prev) => ({
      ...prev,
      loading: true,
      loadingMore: false,
      error: null,
      items: [],
    }));
    Promise.resolve(
      managementSiteEditorApi.fetchSiteBlockHistory(
        blockId,
        { limit: HISTORY_PAGE_SIZE, offset: 0 },
        { signal: controller.signal },
      ),
    )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        const items = Array.isArray(response?.items) ? response.items : [];
        const total =
          typeof response?.total === 'number'
            ? response.total
            : Array.isArray(response?.items)
            ? response.items.length
            : 0;
        setHistory({
          items,
          total,
          loading: false,
          loadingMore: false,
          error: null,
        });
      })
      .catch((err) => {
        if ((err as { name?: string })?.name === 'AbortError') {
          return;
        }
        setHistory({
          ...createEmptyHistoryState(),
          error: extractErrorMessage(err, 'Не удалось загрузить историю версий'),
        });
      });

    return () => controller.abort();
  }, [blockId, historyRefreshKey, refreshToken]);

  const refresh = React.useCallback(() => {
    setRefreshToken((value) => value + 1);
  }, []);

  const refreshHistory = React.useCallback(() => {
    setHistoryRefreshKey((value) => value + 1);
  }, []);

  const loadMoreHistory = React.useCallback(async () => {
    setHistory((prev) => {
      if (prev.loadingMore || prev.loading || !detail.block) {
        return prev;
      }
      if (prev.items.length >= prev.total) {
        return prev;
      }
      return { ...prev, loadingMore: true, error: null };
    });
    const currentBlock = detail.block;
    if (!currentBlock) {
      return;
    }
    try {
      const response = await Promise.resolve(
        managementSiteEditorApi.fetchSiteBlockHistory(currentBlock.id, {
          limit: HISTORY_PAGE_SIZE,
          offset: history.items.length,
        }),
      );
      const items = Array.isArray(response.items) ? response.items : [];
      setHistory((prev) => ({
        items: [...prev.items, ...items],
        total: typeof response.total === 'number' ? response.total : prev.total,
        loading: false,
        loadingMore: false,
        error: null,
      }));
    } catch (err) {
      setHistory((prev) => ({
        ...prev,
        loadingMore: false,
        error: extractErrorMessage(err, 'Не удалось загрузить историю версий'),
      }));
    }
  }, [detail.block, history.items.length]);

  const mutate = React.useCallback(
    (next: {
      block?: SiteBlock | null;
      usage?: SiteBlockUsage[];
      warnings?: SiteBlockWarning[];
    }) => {
      setDetail((prev) => ({
        block: next.block !== undefined ? next.block : prev.block,
        usage: next.usage !== undefined ? next.usage : prev.usage,
        warnings: next.warnings !== undefined ? next.warnings : prev.warnings,
        loading: prev.loading,
        error: prev.error,
      }));
    },
    [],
  );

  return {
    block: detail.block,
    usage: detail.usage,
    warnings: detail.warnings,
    loading: detail.loading,
    error: detail.error,
    refresh,
    mutate,
    history: {
      ...history,
      refresh: refreshHistory,
      loadMore: loadMoreHistory,
    },
  };
}

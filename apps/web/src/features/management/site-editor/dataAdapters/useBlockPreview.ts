import React from 'react';
import type { HomeBlockType } from '../../home/types';
import { getBlockPreview, type BlockPreviewData } from './blockPreview';

type UseBlockPreviewOptions = {
  locale: string;
  useLive?: boolean;
};

type UseBlockPreviewState = {
  data: BlockPreviewData | null;
  loading: boolean;
  error: string | null;
};

const DEFAULT_STATE: UseBlockPreviewState = {
  data: null,
  loading: true,
  error: null,
};

export function useBlockPreview(block: HomeBlockType | string, options: UseBlockPreviewOptions): UseBlockPreviewState {
  const locale = options.locale;
  const useLive = options.useLive ?? true;
  const cacheKey = React.useMemo(() => `${block}:${locale}:${useLive ? 'live' : 'mock'}`, [block, locale, useLive]);

  const [state, setState] = React.useState<UseBlockPreviewState>(DEFAULT_STATE);

  React.useEffect(() => {
    let cancelled = false;
    setState((prev) => ({
      ...prev,
      loading: true,
      error: null,
    }));
    getBlockPreview(block, { locale, useLive })
      .then((data) => {
        if (!cancelled) {
          setState({
            data,
            loading: false,
            error: null,
          });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setState({
            data: null,
            loading: false,
            error: error instanceof Error ? error.message : 'Не удалось загрузить предпросмотр блока.',
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [block, cacheKey, locale, useLive]);

  return state;
}


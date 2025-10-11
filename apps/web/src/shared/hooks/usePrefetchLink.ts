import React from 'react';
import { prefetchUrl } from '../utils/prefetch';

type PrefetchHandlers = {
  onPointerEnter: React.PointerEventHandler<HTMLElement>;
  onFocus: React.FocusEventHandler<HTMLElement>;
  onTouchStart: React.TouchEventHandler<HTMLElement>;
};

const NOOP_HANDLERS: PrefetchHandlers = {
  onPointerEnter: () => undefined,
  onFocus: () => undefined,
  onTouchStart: () => undefined,
};

export function usePrefetchLink(href: string | null | undefined): PrefetchHandlers {
  return React.useMemo(() => {
    if (!href) {
      return NOOP_HANDLERS;
    }
    const handle = () => {
      prefetchUrl(href);
    };
    return {
      onPointerEnter: handle,
      onFocus: handle,
      onTouchStart: handle,
    };
  }, [href]);
}

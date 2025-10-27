import React from 'react';
import clsx from 'clsx';
import type { HomeResponse, HomeFallbackEntry } from '@shared/types/homePublic';
import { HomeBlocks } from '@features/public/home';

type PreviewPayloadRendererProps = React.HTMLAttributes<HTMLDivElement> & {
  payload: HomeResponse;
};

function resolveFallbackKey(entry: HomeFallbackEntry, index: number): string {
  if (entry && typeof entry === 'object') {
    const record = entry as Record<string, unknown>;
    const id = record.id ?? record.block_id ?? record.blockId;
    if (typeof id === 'string' && id.trim().length > 0) {
      return id;
    }
    if (typeof id === 'number' && Number.isFinite(id)) {
      return `fallback-${id}`;
    }
  }
  return `fallback-${index}`;
}

function formatFallbackEntry(entry: HomeFallbackEntry): string {
  if (!entry || typeof entry !== 'object') {
    return 'Не удалось сформировать блок';
  }
  const record = entry as Record<string, unknown>;
  const reason = record.reason ?? record.code ?? record.message;
  if (typeof reason === 'string' && reason.trim().length > 0) {
    return reason;
  }
  return 'Не удалось сформировать блок';
}

function formatFallbackId(entry: HomeFallbackEntry, index: number): string {
  if (!entry || typeof entry !== 'object') {
    return `#${index + 1}`;
  }
  const record = entry as Record<string, unknown>;
  const candidate = record.id ?? record.block_id ?? record.code;
  if (typeof candidate === 'string') {
    const trimmed = candidate.trim();
    if (trimmed.length > 0) {
      return trimmed;
    }
  }
  if (typeof candidate === 'number' && Number.isFinite(candidate)) {
    return String(candidate);
  }
  return `#${index + 1}`;
}

export function PreviewPayloadRenderer({ payload, className, ...rest }: PreviewPayloadRendererProps): React.ReactElement {
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) return undefined;
    const handleClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      if (!target) return;
      const anchor = target.closest('a');
      if (anchor) {
        event.preventDefault();
        anchor.blur();
      }
    };
    container.addEventListener('click', handleClick);
    return () => {
      container.removeEventListener('click', handleClick);
    };
  }, []);

  const fallbacks = React.useMemo(() => {
    if (!Array.isArray(payload.fallbacks)) {
      return [];
    }
    return payload.fallbacks.filter((entry) => entry != null);
  }, [payload.fallbacks]);

  return (
    <div
      ref={containerRef}
      {...rest}
      className={clsx(
        'preview-payload-frame h-full overflow-y-auto rounded-3xl border border-gray-200 bg-white text-gray-900 shadow-lg dark:border-dark-600 dark:bg-dark-900 dark:text-dark-50',
        className,
      )}
    >
      <main
        data-preview-root
        className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 py-10 lg:px-8"
      >
        <HomeBlocks blocks={payload.blocks ?? []} />
      </main>
      {fallbacks.length ? (
        <aside className="border-t border-amber-200 bg-amber-50 px-6 py-4 text-xs text-amber-700 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200">
          <p className="font-semibold uppercase tracking-[0.2em]">Fallback блоки</p>
          <ul className="mt-2 space-y-1">
            {fallbacks.map((entry, index) => (
              <li key={resolveFallbackKey(entry, index)} className="flex items-center justify-between gap-2">
                <span className="font-mono text-[11px] text-amber-600 dark:text-amber-300">{formatFallbackId(entry, index)}</span>
                <span className="text-right text-amber-700 dark:text-amber-200">
                  {formatFallbackEntry(entry)}
                </span>
              </li>
            ))}
          </ul>
        </aside>
      ) : null}
    </div>
  );
}

export default PreviewPayloadRenderer;

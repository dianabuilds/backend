import React from 'react';
import { Badge, Button, Card, Spinner } from '@ui';
import { AlertTriangle, ExternalLink } from '@icons';
import { extractErrorMessage } from '@shared/utils/errors';
import type { ValidationSummary } from '../home/validation';
import type {
  PreviewFetchResult,
  PreviewLayoutContent,
  PreviewMetaSnapshot,
  PreviewRenderData,
} from './previewTypes';
import { PreviewPayloadRenderer } from './PreviewPayloadRenderer';

type PreviewStatus = 'idle' | 'loading' | 'ready' | 'error';

type PreviewMetaState = {
  version: number | null;
  updatedAt: string | null;
  publishedAt: string | null;
  generatedAt: string | null;
};

export type PreviewErrorContext = {
  slug: string;
  dirty: boolean;
  saving: boolean;
  lastSavedAt: string | null;
  layout: string | null;
  summary: ValidationSummary;
};

export type BlockPreviewPanelProps = {
  loading: boolean;
  slug: string;
  dirty: boolean;
  saving: boolean;
  lastSavedAt: string | null;
  validation: ValidationSummary;
  revalidate: () => ValidationSummary;
  fetchPreview: (options: { layout?: string; signal: AbortSignal }) => Promise<PreviewFetchResult>;
  locale: string;
  title?: string;
  description?: string;
  openWindowLabel?: string;
  refreshLabel?: string;
  className?: string;
  cardPadding?: 'none' | 'sm' | 'md' | 'lg';
  initialLayout?: string;
  onError?: (error: unknown, context: PreviewErrorContext) => void;
  testIdPrefix?: string;
};

type ViewportPreset = {
  frame: string;
  wrapper: string;
  inner: string;
};

const DEFAULT_VIEWPORT: ViewportPreset = {
  frame: 'h-[720px] w-full',
  wrapper: 'w-full',
  inner: 'w-full',
};

const VIEWPORT_PRESETS: Record<string, ViewportPreset> = {
  desktop: DEFAULT_VIEWPORT,
  tablet: {
    frame: 'h-[1024px] w-[834px]',
    wrapper: 'w-full overflow-x-auto pb-2',
    inner: 'mx-auto',
  },
  mobile: {
    frame: 'h-[812px] w-[390px]',
    wrapper: 'w-full overflow-x-auto pb-2',
    inner: 'mx-auto',
  },
};

const DEFAULT_TITLE = 'Превью страницы';
const DEFAULT_DESCRIPTION =
  'Сформируйте предпросмотр текущего черновика. Перед открытием убедитесь, что конфигурация валидна.';
const DEFAULT_OPEN_LABEL = 'Открыть окно';
const DEFAULT_REFRESH_LABEL = 'Обновить';
const DEFAULT_TEST_ID_PREFIX = 'preview';

function escapeHtml(value: unknown): string {
  if (value == null) {
    return '';
  }
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function buildPreviewHtml(renderData: PreviewRenderData, locale: string, slug: string): string {
  const title = renderData.title ?? 'Страница';
  const blocksHtml = renderData.blocks
    .map((block, index) => {
      const items = block.items.length
        ? `<ul>${block.items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`
        : '<p class="empty">Нет данных для отображения</p>';
      const heading = block.title ?? `Блок ${index + 1}`;
      return `
      <section class="block">
        <header>
          <span class="index">#${index + 1}</span>
          <div class="meta">
            <h3>${escapeHtml(heading)}</h3>
            <span class="tag">${escapeHtml(block.type)}</span>
          </div>
        </header>
        <div class="items">${items}</div>
      </section>
    `;
    })
    .join('');

  const fallbacks = renderData.fallbacks.length
    ? `<aside class="fallbacks"><h4>Fallback блоки</h4><ul>${renderData.fallbacks
        .map(
          (fb) =>
            `<li><span class="tag">${escapeHtml(fb.id)}</span><span>${escapeHtml(fb.reason)}</span></li>`,
        )
        .join('')}</ul></aside>`
    : '';

  const metaRows = [
    renderData.version != null
      ? `<div><span class="label">Версия:</span><span>${escapeHtml(renderData.version)}</span></div>`
      : '',
    renderData.updatedAt
      ? `<div><span class="label">Обновлено:</span><span>${escapeHtml(renderData.updatedAt)}</span></div>`
      : '',
    renderData.generatedAt
      ? `<div><span class="label">Сгенерировано:</span><span>${escapeHtml(renderData.generatedAt)}</span></div>`
      : '',
  ]
    .filter(Boolean)
    .join('');

  return `<!DOCTYPE html>
  <html lang="${escapeHtml(locale)}">
    <head>
      <meta charset="utf-8" />
      <title>Preview · ${escapeHtml(slug)} · ${escapeHtml(title)}</title>
      <style>
        * { box-sizing: border-box; }
        body { font-family: 'Inter', system-ui, -apple-system, sans-serif; margin: 0; padding: 24px; background: #f9fafb; color: #111827; }
        .page { max-width: 960px; margin: 0 auto; display: flex; flex-direction: column; gap: 24px; }
        header.page-header { display: flex; flex-direction: column; gap: 8px; }
        header.page-header h1 { margin: 0; font-size: 24px; }
        header.page-header .meta { display: flex; gap: 16px; font-size: 13px; color: #4b5563; flex-wrap: wrap; }
        header.page-header .meta div { display: flex; gap: 4px; }
        header.page-header .tag { background: #eef2ff; color: #3730a3; padding: 2px 8px; border-radius: 999px; font-size: 12px; }
        .blocks { display: flex; flex-direction: column; gap: 16px; }
        .block { background: white; border-radius: 12px; border: 1px solid #e5e7eb; padding: 20px; box-shadow: 0 10px 30px -20px rgba(15,23,42,.25); }
        .block header { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; }
        .block header .index { font-weight: 700; color: #6366f1; }
        .block header .meta { display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; }
        .block header h3 { margin: 0; font-size: 16px; }
        .block header .tag { padding: 2px 8px; font-size: 11px; border-radius: 999px; border: 1px solid #c7d2fe; background: #eef2ff; color: #3730a3; text-transform: uppercase; letter-spacing: 0.08em; }
        .block .items ul { margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
        .block .items .empty { margin: 0; font-size: 13px; color: #9ca3af; }
        .fallbacks { background: white; border-radius: 12px; border: 1px dashed #fca5a5; padding: 16px; }
        .fallbacks h4 { margin: 0 0 12px 0; font-size: 14px; color: #b91c1c; }
        .fallbacks ul { margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
        .fallbacks .tag { font-size: 11px; padding: 2px 6px; background: #fee2e2; color: #b91c1c; border-radius: 6px; margin-right: 6px; }
      </style>
    </head>
    <body>
      <div class="page">
        <header class="page-header">
          <h1>${escapeHtml(title)}</h1>
          <div class="meta">
            <div><span class="label">Slug:</span><span>${escapeHtml(slug)}</span></div>
            ${metaRows}
          </div>
        </header>
        <main class="blocks">${blocksHtml || '<p class="empty">Нет активных блоков</p>'}</main>
        ${fallbacks}
      </div>
    </body>
  </html>`;
}

function mergeMeta(renderData: PreviewRenderData, meta?: PreviewMetaSnapshot): PreviewMetaState {
  return {
    version: meta?.version ?? renderData.version ?? null,
    updatedAt: meta?.updatedAt ?? renderData.updatedAt ?? null,
    publishedAt: meta?.publishedAt ?? renderData.publishedAt ?? null,
    generatedAt: meta?.generatedAt ?? renderData.generatedAt ?? null,
  };
}

function resolveViewportPreset(layout: string | null): ViewportPreset {
  if (!layout) {
    return DEFAULT_VIEWPORT;
  }
  const normalized = layout.toLowerCase();
  return VIEWPORT_PRESETS[normalized] ?? DEFAULT_VIEWPORT;
}

function resolveErrorMessage(error: unknown): string {
  return extractErrorMessage(error, 'Не удалось загрузить превью.');
}

function parseErrorDetails(error: unknown): string | null {
  const body = (error as { body?: unknown })?.body;
  if (typeof body !== 'string' || !body.trim()) {
    return null;
  }
  try {
    const parsed = JSON.parse(body);
    if (Array.isArray(parsed?.details)) {
      const detailList = (parsed.details as unknown[])
        .map((detail) => (typeof detail === 'string' ? detail : null))
        .filter((detail): detail is string => Boolean(detail));
      return detailList.join(', ');
    }
    if (parsed?.detail && typeof parsed.detail === 'object' && parsed.detail !== null) {
      const detailRecord = parsed.detail as Record<string, unknown>;
      const message =
        (typeof detailRecord.message === 'string' && detailRecord.message.trim()) ||
        (typeof detailRecord.error === 'string' && detailRecord.error.trim());
      if (message) {
        return message;
      }
    }
  } catch {
    return null;
  }
  return null;
}

export function BlockPreviewPanel({
  loading,
  slug,
  dirty,
  saving,
  lastSavedAt,
  validation,
  revalidate,
  fetchPreview,
  locale,
  title = DEFAULT_TITLE,
  description = DEFAULT_DESCRIPTION,
  openWindowLabel = DEFAULT_OPEN_LABEL,
  refreshLabel = DEFAULT_REFRESH_LABEL,
  className = '',
  cardPadding = 'sm',
  initialLayout,
  onError,
  testIdPrefix = DEFAULT_TEST_ID_PREFIX,
}: BlockPreviewPanelProps): React.ReactElement {
  const [status, setStatus] = React.useState<PreviewStatus>('idle');
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [errorDetails, setErrorDetails] = React.useState<string | null>(null);
  const [html, setHtml] = React.useState('');
  const [frameKey, setFrameKey] = React.useState(0);
  const [metaState, setMetaState] = React.useState<PreviewMetaState>({
    version: null,
    updatedAt: null,
    publishedAt: null,
    generatedAt: null,
  });
  const [availableLayouts, setAvailableLayouts] = React.useState<string[]>(
    initialLayout ? [initialLayout] : [],
  );
  const [activeLayout, setActiveLayout] = React.useState<string>(initialLayout ?? 'desktop');

  const layoutsRef = React.useRef<Map<string, PreviewLayoutContent>>(new Map());
  const abortControllerRef = React.useRef<AbortController | null>(null);

  const panelTestId = `${testIdPrefix}-panel`;
  const loadingTestId = `${testIdPrefix}-loading`;
  const errorTestId = `${testIdPrefix}-error`;
  const successTestId = `${testIdPrefix}-success`;
  const orderTestId = `${testIdPrefix}-order`;
  const frameTestId = `${testIdPrefix}-frame`;

  const isConfigValid = validation.valid;

  const resetPreviewState = React.useCallback(() => {
    layoutsRef.current.clear();
    setAvailableLayouts(initialLayout ? [initialLayout] : []);
    setActiveLayout(initialLayout ?? 'desktop');
    setHtml('');
    setMetaState({
      version: null,
      updatedAt: null,
      publishedAt: null,
      generatedAt: null,
    });
    setStatus('idle');
    setErrorMessage(null);
    setErrorDetails(null);
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, [initialLayout]);

  const performPreview = React.useCallback(
    async (layoutKey?: string) => {
      const summary = revalidate();
      if (!summary.valid) {
        const summaryMessage = summary.general.length
          ? summary.general.map((issue) => issue.message).join('; ')
          : 'Проверьте настройки блоков.';
        setStatus('error');
        setErrorMessage('Превью недоступно: исправьте ошибки конфигурации.');
        setErrorDetails(summaryMessage);
        return;
      }

      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      setStatus('loading');
      setErrorMessage(null);
      setErrorDetails(null);

      try {
        const result = await fetchPreview({ layout: layoutKey, signal: controller.signal });
        const entries = Object.entries(result.layouts ?? {});
        if (!entries.length) {
          setStatus('error');
          setErrorMessage('Превью недоступно: нет данных для отображения.');
          setErrorDetails(null);
          return;
        }

        layoutsRef.current = new Map(entries);
        const nextLayout =
          (layoutKey && layoutsRef.current.has(layoutKey) && layoutKey) ||
          (result.defaultLayout && layoutsRef.current.has(result.defaultLayout) && result.defaultLayout) ||
          entries[0][0];

        setAvailableLayouts(entries.map(([key]) => key));
        setActiveLayout(nextLayout);

        const layoutContent = layoutsRef.current.get(nextLayout)!;
        setHtml(buildPreviewHtml(layoutContent.summary, locale, slug));
        setMetaState(mergeMeta(layoutContent.summary, result.meta));
        setStatus('ready');
        setFrameKey((value) => value + 1);
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }
        const message = resolveErrorMessage(error);
        const details = parseErrorDetails(error);
        setStatus('error');
        setErrorMessage(message);
        setErrorDetails(details);
        onError?.(error, {
          slug,
          dirty,
          saving,
          lastSavedAt,
          layout: layoutKey ?? null,
          summary,
        });
      } finally {
        abortControllerRef.current = null;
      }
    },
    [dirty, fetchPreview, lastSavedAt, locale, onError, revalidate, saving, slug],
  );

  const handleRefresh = React.useCallback(() => {
    void performPreview(activeLayout);
  }, [activeLayout, performPreview]);

  const handleLayoutChange = React.useCallback(
    (nextLayout: string) => {
      if (nextLayout === activeLayout) {
        return;
      }
      if (layoutsRef.current.has(nextLayout)) {
        const layoutContent = layoutsRef.current.get(nextLayout)!;
        setActiveLayout(nextLayout);
        setHtml(buildPreviewHtml(layoutContent.summary, locale, slug));
        setMetaState(mergeMeta(layoutContent.summary, undefined));
        setFrameKey((value) => value + 1);
      } else {
        void performPreview(nextLayout);
      }
    },
    [activeLayout, locale, performPreview, slug],
  );

  const handleOpenNewWindow = React.useCallback(() => {
    if (!html) {
      return;
    }
    const previewWindow = window.open('', `${testIdPrefix}-window`);
    if (!previewWindow) {
      return;
    }
    previewWindow.document.open();
    previewWindow.document.write(html);
    previewWindow.document.close();
  }, [html, testIdPrefix]);

  React.useEffect(() => {
    resetPreviewState();
  }, [fetchPreview, slug, resetPreviewState]);

  React.useEffect(() => {
    if (!loading && status === 'idle') {
      void performPreview();
    }
  }, [loading, performPreview, status]);

  React.useEffect(
    () => () => {
      abortControllerRef.current?.abort();
    },
    [],
  );

  const currentLayoutContent = layoutsRef.current.get(activeLayout) ?? null;
  const currentRenderData = currentLayoutContent?.summary ?? null;
  const blocksSummary = currentRenderData?.blocks ?? [];
  const viewportPreset = resolveViewportPreset(activeLayout);

  return (
    <Card
      padding={cardPadding}
      className={`space-y-4 bg-white/95 shadow-sm ${className}`.trim()}
      data-testid={panelTestId}
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-dark-50">{title}</h3>
          <p className="text-xs text-gray-500 dark:text-dark-200">
            Slug:{' '}
            <span className="font-mono text-gray-700 dark:text-dark-100">{slug}</span>
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {!isConfigValid ? <Badge color="warning">Исправьте ошибки</Badge> : null}
          {availableLayouts.length > 0 ? (
            <div className="inline-flex items-center gap-1 rounded-xl border border-gray-200 bg-gray-50 p-1 dark:border-dark-600 dark:bg-dark-800/60">
              {availableLayouts.map((layoutKey) => {
                const active = layoutKey === activeLayout;
                return (
                  <button
                    key={layoutKey}
                    type="button"
                    onClick={() => handleLayoutChange(layoutKey)}
                    className={`rounded-lg px-3 py-1 text-xs font-semibold transition ${
                      active
                        ? 'bg-white text-primary-700 shadow-sm dark:bg-dark-900'
                        : 'text-gray-600 hover:text-gray-800 dark:text-dark-200 dark:hover:text-dark-50'
                    }`}
                  >
                    {layoutKey}
                  </button>
                );
              })}
            </div>
          ) : null}
          <Button
            size="xs"
            variant="ghost"
            color="neutral"
            onClick={handleOpenNewWindow}
            disabled={!html || status !== 'ready'}
            className="flex items-center gap-1"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            {openWindowLabel}
          </Button>
          <Button
            size="sm"
            onClick={handleRefresh}
            disabled={status === 'loading' || !isConfigValid}
          >
            {status === 'loading' ? 'Загрузка…' : refreshLabel}
          </Button>
        </div>
      </div>

      <p className="text-xs text-gray-500 dark:text-dark-200">{description}</p>

      {status === 'loading' ? (
        <div
          className="flex min-h-[320px] items-center justify-center"
          data-testid={loadingTestId}
        >
          <Spinner />
        </div>
      ) : null}

      {status === 'error' ? (
        <div
          className="flex flex-col gap-3 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-100"
          data-testid={errorTestId}
        >
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4" />
            <div>
              <p className="font-semibold">{errorMessage}</p>
              {errorDetails ? (
                <p className="mt-1 whitespace-pre-line text-xs text-rose-600 dark:text-rose-200">
                  {errorDetails}
                </p>
              ) : null}
            </div>
          </div>
          <div>
            <Button size="sm" variant="ghost" onClick={handleRefresh}>
              Попробовать снова
            </Button>
          </div>
        </div>
      ) : null}

      {status === 'ready' ? (
        <div className="space-y-3" data-testid={successTestId}>
          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 dark:text-dark-200">
            {metaState.version != null ? (
              <span>
                Версия:{' '}
                <span className="font-semibold text-gray-700 dark:text-dark-100">
                  {metaState.version}
                </span>
              </span>
            ) : null}
            {metaState.updatedAt ? (
              <span>
                Обновлено:{' '}
                <span className="font-semibold text-gray-700 dark:text-dark-100">
                  {metaState.updatedAt}
                </span>
              </span>
            ) : null}
            {metaState.generatedAt ? (
              <span>
                Превью от:{' '}
                <span className="font-semibold text-gray-700 dark:text-dark-100">
                  {metaState.generatedAt}
                </span>
              </span>
            ) : null}
            {metaState.publishedAt ? (
              <span>
                Публикация:{' '}
                <span className="font-semibold text-gray-700 dark:text-dark-100">
                  {metaState.publishedAt}
                </span>
              </span>
            ) : null}
          </div>
          {blocksSummary.length ? (
            <div
              className="flex flex-wrap gap-2 text-xs"
              data-testid={orderTestId}
            >
              {blocksSummary.map((block, index) => (
                <span
                  key={block.id}
                  className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 font-mono text-[11px] text-gray-600 dark:border-dark-600 dark:bg-dark-800 dark:text-dark-100"
                >
                  #{index + 1} · {block.id} · {block.type}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500 dark:text-dark-200">
              Активные блоки отсутствуют.
            </p>
          )}
          <div className={viewportPreset.wrapper}>
            <div className={viewportPreset.inner}>
              {currentLayoutContent?.payload ? (
                <PreviewPayloadRenderer
                  key={frameKey}
                  payload={currentLayoutContent.payload}
                  className={`${viewportPreset.frame} block max-w-full`}
                  data-testid={frameTestId}
                />
              ) : (
                <iframe
                  key={frameKey}
                  title="Предпросмотр страницы"
                  sandbox="allow-same-origin"
                  srcDoc={html}
                  className={`${viewportPreset.frame} block max-w-full rounded-3xl border border-gray-200 bg-white shadow-lg dark:border-dark-600 dark:bg-dark-900`}
                  data-testid={frameTestId}
                />
              )}
            </div>
          </div>
        </div>
      ) : null}
    </Card>
  );
}

export default BlockPreviewPanel;

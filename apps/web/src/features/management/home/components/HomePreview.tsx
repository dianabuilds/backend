import React from 'react';
import { Button, Card, Spinner, Badge } from '@ui';
import { AlertTriangle } from '@icons';
import { previewHome } from '@shared/api/home';
import { extractErrorMessage } from '@shared/utils/errors';
import { getLocale } from '@shared/i18n/locale';
import { reportFeatureError } from '@shared/utils/sentry';
import { useHomeEditorContext } from '../HomeEditorContext';
import { buildHomeConfigPayload } from '../utils/payload';

type PreviewBlockSummary = {
  id: string;
  type: string;
  title?: string;
  items: string[];
};

type PreviewRenderData = {
  version: number | null;
  updatedAt: string | null;
  publishedAt: string | null;
  generatedAt: string | null;
  title: string | null;
  blocks: PreviewBlockSummary[];
  fallbacks: Array<{ id: string; reason: string }>;
};

type PreviewState = {
  status: 'idle' | 'loading' | 'ready' | 'error';
  message: string | null;
  details: string | null;
  renderData: PreviewRenderData | null;
  html: string;
  updatedAt: string | null;
};

const INITIAL_STATE: PreviewState = {
  status: 'idle',
  message: null,
  details: null,
  renderData: null,
  html: '',
  updatedAt: null,
};

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

function normalizeString(value: unknown): string | null {
  if (typeof value === 'string') {
    const trimmed = value.trim();
    return trimmed.length ? trimmed : null;
  }
  if (typeof value === 'number' && Number.isFinite(value)) {
    return String(value);
  }
  return null;
}

function resolveItemLabel(item: unknown): string | null {
  if (item == null) return null;
  if (typeof item === 'string' || typeof item === 'number') {
    return String(item);
  }
  if (typeof item === 'object') {
    const record = item as Record<string, unknown>;
    const candidate = normalizeString(record.title)
      ?? normalizeString(record.name)
      ?? normalizeString(record.slug)
      ?? normalizeString(record.id);
    if (candidate) {
      return candidate;
    }
  }
  return null;
}

function parsePreviewBlocks(payload: Record<string, unknown>): PreviewBlockSummary[] {
  const rawBlocks = Array.isArray(payload.blocks) ? payload.blocks : [];
  return rawBlocks.map((entry, index) => {
    if (typeof entry !== 'object' || entry === null) {
      return {
        id: `block-${index + 1}`,
        type: 'unknown',
        items: [],
      };
    }
    const record = entry as Record<string, unknown>;
    const id = normalizeString(record.id) ?? `block-${index + 1}`;
    const type = normalizeString(record.type) ?? 'unknown';
    const title = normalizeString(record.title) ?? undefined;
    const rawItems = Array.isArray(record.items) ? record.items : [];
    const items: string[] = [];
    for (const rawItem of rawItems) {
      const label = resolveItemLabel(rawItem);
      if (label) {
        items.push(label);
      }
      if (items.length >= 6) {
        break;
      }
    }
    return {
      id,
      type,
      title,
      items,
    };
  });
}

function parseFallbacks(payload: Record<string, unknown>): Array<{ id: string; reason: string }> {
  const fallbacks = Array.isArray(payload.fallbacks) ? payload.fallbacks : [];
  const result: Array<{ id: string; reason: string }> = [];
  fallbacks.forEach((entry) => {
    if (typeof entry !== 'object' || entry === null) {
      return;
    }
    const record = entry as Record<string, unknown>;
    const id = normalizeString(record.id) ?? 'unknown';
    const reason = normalizeString(record.reason) ?? 'unknown';
    result.push({ id, reason });
  });
  return result;
}

function extractPreviewData(payload: Record<string, unknown>): PreviewRenderData {
  const blocks = parsePreviewBlocks(payload);
  const fallbacks = parseFallbacks(payload);
  const meta = typeof payload.meta === 'object' && payload.meta !== null ? (payload.meta as Record<string, unknown>) : {};
  return {
    version: typeof payload.version === 'number' ? payload.version : null,
    updatedAt: normalizeString(payload.updated_at),
    publishedAt: normalizeString(payload.published_at),
    generatedAt: normalizeString(payload.generated_at),
    title: normalizeString(meta.title) ?? null,
    blocks,
    fallbacks,
  };
}

function buildPreviewHtml(renderData: PreviewRenderData, locale: string, slug: string): string {
  const title = renderData.title ?? 'Главная страница';
  const blocksHtml = renderData.blocks.map((block, index) => {
    const items = block.items.length
      ? `<ul>${block.items.map((item: string) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`
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
  }).join('');

  const fallbacks = renderData.fallbacks.length
    ? `<aside class="fallbacks"><h4>Fallback блоки</h4><ul>${renderData.fallbacks.map((fb) => `<li><span class="tag">${escapeHtml(fb.id)}</span><span>${escapeHtml(fb.reason)}</span></li>`).join('')}</ul></aside>`
    : '';

  const metaRows = [
    renderData.version != null ? `<div><span class="label">Версия:</span><span>${escapeHtml(renderData.version)}</span></div>` : '',
    renderData.updatedAt ? `<div><span class="label">Обновлено:</span><span>${escapeHtml(renderData.updatedAt)}</span></div>` : '',
    renderData.generatedAt ? `<div><span class="label">Сгенерировано:</span><span>${escapeHtml(renderData.generatedAt)}</span></div>` : '',
  ].filter(Boolean).join('');

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

function parseErrorDetails(error: unknown): string | null {
  const body = (error as any)?.body;
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
      const message = normalizeString(detailRecord.message) ?? normalizeString(detailRecord.error);
      if (message) return message;
    }
  } catch {
    return null;
  }
  return null;
}

export function HomePreview(): React.ReactElement {
  const { data, slug, validation, revalidate, loading, dirty, saving, lastSavedAt } = useHomeEditorContext();
  const [state, setState] = React.useState<PreviewState>(INITIAL_STATE);
  const [frameKey, setFrameKey] = React.useState(0);
  const abortController = React.useRef<AbortController | null>(null);
  const locale = React.useMemo(() => getLocale(), []);

  const isBusy = state.status === 'loading';
  const isConfigValid = validation.valid;

  const performPreview = React.useCallback(async () => {
    if (abortController.current) {
      abortController.current.abort();
      abortController.current = null;
    }

    const summary = revalidate();
    if (!summary.valid) {
      const summaryMessage = summary.general.length
        ? summary.general.map((error) => error.message).join('; ')
        : 'Проверьте настройки блоков.';
      setState((prev) => ({
        ...prev,
        status: 'error',
        message: 'Превью недоступно: исправьте ошибки конфигурации.',
        details: summaryMessage,
      }));
      return;
    }

    const controller = new AbortController();
    abortController.current = controller;

    setState((prev) => ({
      ...prev,
      status: 'loading',
      message: null,
      details: null,
    }));

    const payload = buildHomeConfigPayload(slug, data);

    try {
      const response = await previewHome(payload, {
        signal: controller.signal,
        headers: { 'Accept-Language': locale },
      });
      const renderData = extractPreviewData(response.payload);
      const html = buildPreviewHtml(renderData, locale, slug);
      setState({
        status: 'ready',
        message: null,
        details: null,
        renderData,
        html,
        updatedAt: new Date().toISOString(),
      });
      setFrameKey((value) => value + 1);
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }
      const message = extractErrorMessage(error, 'Не удалось загрузить превью.');
      const details = parseErrorDetails(error);
      setState((prev) => ({
        ...prev,
        status: 'error',
        message,
        details,
      }));
      const blockErrorsCount = Object.values(summary.blocks).reduce((acc, errors) => acc + errors.length, 0);
      reportFeatureError(error, 'home-preview', {
        slug,
        dirty,
        saving,
        lastSavedAt,
        validationErrors: summary.general.length,
        blockErrors: blockErrorsCount,
        message,
        details,
      });
    } finally {
      abortController.current = null;
    }
  }, [data, dirty, lastSavedAt, locale, revalidate, saving, slug]);

  React.useEffect(() => {
    if (!loading && state.status === 'idle') {
      void performPreview();
    }
    return () => {
      abortController.current?.abort();
    };
  }, [loading, performPreview, state.status]);

  const blocksSummary = state.renderData?.blocks ?? [];
  const previewInfo = state.renderData;

  return (
    <Card padding="sm" className="space-y-4" data-testid="home-preview-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-gray-900">Превью главной</h3>
          <p className="text-xs text-gray-500">Slug: <span className="font-mono text-gray-700">{slug}</span></p>
        </div>
        <div className="flex items-center gap-2">
          {!isConfigValid ? (
            <Badge color="warning">Исправьте ошибки</Badge>
          ) : null}
          <Button size="sm" onClick={() => void performPreview()} disabled={isBusy || !isConfigValid}>
            {isBusy ? 'Загрузка…' : 'Обновить превью'}
          </Button>
        </div>
      </div>

      {state.status === 'loading' ? (
        <div className="flex min-h-[320px] items-center justify-center" data-testid="home-preview-loading">
          <Spinner />
        </div>
      ) : null}

      {state.status === 'error' ? (
        <div className="flex flex-col gap-3 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700" data-testid="home-preview-error">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4" />
            <div>
              <p className="font-semibold">{state.message}</p>
              {state.details ? (<p className="mt-1 whitespace-pre-line text-xs text-rose-600">{state.details}</p>) : null}
            </div>
          </div>
          <div>
            <Button size="sm" variant="ghost" onClick={() => void performPreview()}>
              Попробовать снова
            </Button>
          </div>
        </div>
      ) : null}

      {state.status === 'ready' ? (
        <div className="space-y-3" data-testid="home-preview-success">
          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500">
            {previewInfo?.version != null ? <span>Версия: <span className="font-semibold text-gray-700">{previewInfo.version}</span></span> : null}
            {previewInfo?.updatedAt ? <span>Обновлено: <span className="font-semibold text-gray-700">{previewInfo.updatedAt}</span></span> : null}
            {state.updatedAt ? <span>Превью от: <span className="font-semibold text-gray-700">{new Date(state.updatedAt).toLocaleString()}</span></span> : null}
          </div>
          {blocksSummary.length ? (
            <div className="flex flex-wrap gap-2 text-xs" data-testid="home-preview-order">
              {blocksSummary.map((block, index) => (
                <span key={block.id} className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 font-mono text-[11px] text-gray-600">
                  #{index + 1} · {block.id} · {block.type}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-500">Активные блоки отсутствуют.</p>
          )}
          <iframe
            key={frameKey}
            title="Предпросмотр главной страницы"
            sandbox="allow-same-origin"
            srcDoc={state.html}
            className="h-[640px] w-full rounded-lg border border-gray-200 bg-white"
            data-testid="home-preview-frame"
          />
        </div>
      ) : null}
    </Card>
  );
}

export default HomePreview;


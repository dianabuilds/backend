import type { RenderResult } from './types.js';

type ClientEntryAssets = {
  src: string;
  css?: string[];
};

type RenderDocumentOptions = {
  resolveClientEntry?: (entry: string) => ClientEntryAssets | null;
};

function serializeInitialData(data: unknown): string {
  const json = JSON.stringify(data ?? {});
  return json.replace(/</g, '\u003c');
}

export async function renderDocument(
  template: string,
  result: RenderResult,
  options: RenderDocumentOptions = {},
): Promise<{
  html: string;
  status: number;
  headers: Record<string, string>;
}> {
  const documentHtml = applyTemplate(template, result, options);
  const status = result.status ?? 200;
  const headers = result.headers ? { ...result.headers } : {};
  if (!Object.keys(headers).some((key) => key.toLowerCase() === 'content-type')) {
    headers['Content-Type'] = 'text/html; charset=utf-8';
  }
  return { html: documentHtml, status, headers };
}

export function applyTemplate(
  template: string,
  result: RenderResult,
  options: RenderDocumentOptions = {},
): string {
  let documentHtml = template.replace('<!--app-html-->', result.html ?? '');
  const initialScript = `<script>window.__INITIAL_DATA__ = ${serializeInitialData(result.initialData)};</script>`;
  documentHtml = documentHtml.replace('<!--initial-data-->', initialScript);

  if (result.head?.headTags) {
    documentHtml = documentHtml.replace('</head>', `${result.head.headTags}</head>`);
  }
  if (result.head?.htmlAttributes) {
    documentHtml = documentHtml.replace('<html>', `<html ${result.head.htmlAttributes}>`);
  }
  if (result.head?.bodyAttributes) {
    documentHtml = documentHtml.replace('<body>', `<body ${result.head.bodyAttributes}>`);
  }

  if (result.entryClient && options.resolveClientEntry) {
    const assets = options.resolveClientEntry(result.entryClient);
    if (assets) {
      documentHtml = stripModuleScripts(documentHtml);
      documentHtml = stripStylesheets(documentHtml);
      if (assets.css?.length) {
        const stylesMarkup = assets.css
          .map((href) => `<link rel="stylesheet" href="${href}" crossorigin>`)
          .join('');
        documentHtml = documentHtml.replace('</head>', `${stylesMarkup}</head>`);
      }
      const scriptTag = `<script type="module" src="${assets.src}" crossorigin></script>`;
      documentHtml = injectBeforeClosingBody(documentHtml, scriptTag);
    }
  }

  return documentHtml;
}

function stripModuleScripts(html: string): string {
  return html.replace(/<script\b[^>]*type="module"[^>]*><\/script>\s*/gi, '');
}

function stripStylesheets(html: string): string {
  return html.replace(/<link\b[^>]*rel="stylesheet"[^>]*>\s*/gi, '');
}

function injectBeforeClosingBody(html: string, markup: string): string {
  if (html.includes('</body>')) {
    return html.replace('</body>', `${markup}</body>`);
  }
  return `${html}${markup}`;
}



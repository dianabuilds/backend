import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { readFile } from 'node:fs/promises';
import express, { type Express } from 'express';
import compression from 'compression';
import sirv from 'sirv';
import type { RenderFunction } from './types.js';
import { renderDocument } from './html.js';

type ViteManifest = Record<string, {
  file: string;
  css?: string[];
  assets?: string[];
}>;

export type CreateServerOptions = {
  root?: string;
  mode?: 'development' | 'production' | 'test';
  template?: string;
  render?: RenderFunction;
};

const DEFAULT_TEMPLATE_PATH = 'index.html';

function toAbsolute(root: string, ...segments: string[]): string {
  return path.resolve(root, ...segments);
}

export async function createSsrServer(options: CreateServerOptions = {}): Promise<{
  app: Express;
  close: () => Promise<void>;
}> {
  const root = options.root ?? process.cwd();
  const mode = options.mode ?? (process.env.NODE_ENV as CreateServerOptions['mode']) ?? 'development';
  const app = express();

  let vite: import('vite').ViteDevServer | null = null;
  let baseTemplate = options.template ?? null;
  let manifest: ViteManifest | null = null;
  const fixedRender = options.render;

  if (mode === 'development') {
    const viteModule = await import('vite');
    vite = await viteModule.createServer({
      root,
      server: { middlewareMode: true },
      appType: 'custom',
    });
    app.use(vite.middlewares);
  } else if (mode === 'production') {
    app.use(compression());
    const distClient = toAbsolute(root, 'dist', 'client');
    app.use(sirv(distClient));
    if (!baseTemplate) {
      baseTemplate = await readFile(path.resolve(distClient, 'index.html'), 'utf-8');
    }
    try {
      const manifestPath = path.resolve(distClient, 'manifest.json');
      const manifestContent = await readFile(manifestPath, 'utf-8');
      manifest = JSON.parse(manifestContent) as ViteManifest;
    } catch (error) {
      console.warn('[ssr] unable to load manifest.json', error);
      manifest = null;
    }
  } else {
    if (!baseTemplate) {
      baseTemplate = await readFile(toAbsolute(root, DEFAULT_TEMPLATE_PATH), 'utf-8');
    }
  }

  async function resolveTemplate(url: string): Promise<string> {
    let template = baseTemplate ?? (await readFile(toAbsolute(root, DEFAULT_TEMPLATE_PATH), 'utf-8'));
    if (vite) {
      template = await vite.transformIndexHtml(url, template);
    }
    return template;
  }

  async function resolveRenderer(_url: string): Promise<RenderFunction> {
    void _url;
    if (fixedRender) {
      return fixedRender;
    }
    if (vite) {
      const mod = await vite.ssrLoadModule('/src/entry-server.tsx');
      return mod.render as RenderFunction;
    }
    const entryPath = toAbsolute(root, 'dist', 'server', 'entry-server.js');
    const mod = await import(pathToFileURL(entryPath).href);
    return (mod.render ?? mod.default) as RenderFunction;
  }

  function resolveClientEntryAssets(entry: string): { src: string; css?: string[] } | null {
    if (vite) {
      const normalized = entry.startsWith('/') ? entry : entry.startsWith('src/') ? `/${entry}` : `/src/${entry}`;
      return { src: normalized };
    }
    if (!manifest) {
      return null;
    }
    const record = manifest[entry] ?? manifest[`/${entry}`];
    if (!record) {
      return null;
    }
    return {
      src: `/${record.file}`,
      css: record.css?.map((href) => `/${href}`),
    };
  }

  app.use(async (req, res) => {
    try {
      const url = req.originalUrl;
      const template = await resolveTemplate(url);
      const render = await resolveRenderer(url);
      const result = await render(new URL(url, 'http://localhost').toString());

      if (!result) {
        res.status(200).set('Content-Type', 'text/html; charset=utf-8').send(template);
        return;
      }

      const document = await renderDocument(template, result, {
        resolveClientEntry: resolveClientEntryAssets,
      });

      res.status(document.status);
      res.set(document.headers);
      res.send(document.html);
    } catch (error) {
      if (vite) {
        vite.ssrFixStacktrace(error as Error);
      }
      console.error('[ssr] render error', error);
      res.status(500).set('Content-Type', 'text/plain').end('Internal Server Error');
    }
  });

  return {
    app,
    close: async () => {
      if (vite) {
        await vite.close();
      }
    },
  };
}






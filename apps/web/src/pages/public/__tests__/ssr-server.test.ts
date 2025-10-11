/* @vitest-environment node */

import React from 'react';
import express from 'express';
import { describe, it, expect, beforeAll, beforeEach, afterEach, afterAll, vi } from 'vitest';
import request from 'supertest';

import type { HomeResponse } from '@shared/types/homePublic';
import type { DevBlogListResponse, DevBlogDetailResponse } from '@shared/types/devBlog';
import type { RenderFunction } from '../../../../server/types';

const originalWindow = globalThis.window;
const originalDocument = globalThis.document;
const originalNavigator = globalThis.navigator;

const createdWindow = originalWindow === undefined;
const createdDocument = originalDocument === undefined;
const createdNavigator = originalNavigator === undefined;

if (createdWindow) {
  (globalThis as any).window = {};
}
if (createdDocument) {
  (globalThis as any).document = {};
}
if (createdNavigator) {
  (globalThis as any).navigator = { userAgent: 'node' };
}

if (typeof (globalThis.document as any).createElement !== 'function') {
  (globalThis.document as any).createElement = () => ({ style: {} });
}
if (!(globalThis.document as any).body) {
  (globalThis.document as any).body = {
    appendChild: () => void 0,
    removeChild: () => void 0,
  };
}

const sampleHome: HomeResponse = {
  slug: 'main',
  version: 1,
  updatedAt: '2025-10-10T10:00:00Z',
  publishedAt: '2025-10-10T10:00:00Z',
  generatedAt: '2025-10-10T10:00:00Z',
  blocks: [
    {
      id: 'hero-1',
      type: 'hero',
      enabled: true,
      title: 'Hero SSR',
      slots: { headline: 'SSR headline' },
      layout: null,
      items: [],
      dataSource: null,
    },
  ],
  meta: {},
  fallbacks: [],
};

const sampleList: DevBlogListResponse = {
  items: [
    {
      id: 1,
      slug: 'first-post',
      title: 'Первый пост',
      summary: 'Краткое описание',
      coverUrl: null,
      publishAt: '2025-10-10T10:00:00Z',
      updatedAt: '2025-10-10T10:00:00Z',
      author: { id: '1', name: 'Автор' },
    },
  ],
  total: 1,
  hasNext: false,
};

const samplePost: DevBlogDetailResponse = {
  post: {
    ...sampleList.items[0],
    content: '<p>Контент</p>',
    status: 'published',
    isPublic: true,
    tags: ['dev-blog'],
  },
  prev: null,
  next: null,
};

const fetchPublicHomeMock = vi.fn(async () => ({ data: sampleHome, status: 200, etag: 'etag-ssr' }));
const fetchDevBlogListMock = vi.fn(async () => ({ data: sampleList, status: 200 }));
const fetchDevBlogPostMock = vi.fn(async () => ({ data: samplePost, status: 200 }));

vi.mock('react-apexcharts', () => ({
  __esModule: true,
  default: vi.fn(() => null),
}), { virtual: true });

vi.mock('apexcharts', () => ({
  __esModule: true,
  default: {},
}), { virtual: true });

vi.mock('@shared/ui/charts/ApexChart', () => ({
  __esModule: true,
  default: () => null,
}));

vi.mock('@shared/ui/ToastProvider', () => ({
  __esModule: true,
  ToastProvider: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
}));

vi.mock('@shared/api/publicHome', () => ({
  fetchPublicHome: fetchPublicHomeMock,
}));

vi.mock('@shared/api/devBlog', () => ({
  fetchDevBlogList: fetchDevBlogListMock,
  fetchDevBlogPost: fetchDevBlogPostMock,
}));

const entryModulePromise = import('../../../entry-server.tsx');
const htmlModulePromise = import('../../../../server/html');

const template = '<!doctype html><html><body><div id="root"><!--app-html--></div><!--initial-data--></body></html>';

function createTestApp(
  renderDocumentFn: (template: string, render: RenderFunction, url: string) => Promise<{
    html: string;
    status: number;
    headers: Record<string, string>;
  }>,
  renderer: RenderFunction,
): express.Express {
  const app = express();
  app.use(async (req, res) => {
    const document = await renderDocumentFn(template, renderer, new URL(req.originalUrl, 'http://localhost').toString());
    res.status(document.status);
    for (const [key, value] of Object.entries(document.headers)) {
      res.set(key, value);
    }
    res.send(document.html);
  });
  return app;
}

describe('SSR server responses', () => {
  let render: RenderFunction;
  let renderDocument: (template: string, render: RenderFunction, url: string) => Promise<{
    html: string;
    status: number;
    headers: Record<string, string>;
  }>;

  beforeAll(async () => {
    ({ render } = await entryModulePromise);
    ({ renderDocument } = await htmlModulePromise);
  });

  afterAll(() => {
    if (createdWindow) {
      delete (globalThis as any).window;
    } else {
      (globalThis as any).window = originalWindow;
    }

    if (createdDocument) {
      delete (globalThis as any).document;
    } else {
      (globalThis as any).document = originalDocument;
    }

    if (createdNavigator) {
      delete (globalThis as any).navigator;
    }
  });

  beforeEach(() => {
    fetchPublicHomeMock.mockReset();
    fetchDevBlogListMock.mockReset();
    fetchDevBlogPostMock.mockReset();

    fetchPublicHomeMock.mockResolvedValue({ data: sampleHome, status: 200, etag: 'etag-ssr' });
    fetchDevBlogListMock.mockResolvedValue({ data: sampleList, status: 200 });
    fetchDevBlogPostMock.mockResolvedValue({ data: samplePost, status: 200 });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('возвращает HTML для домашней страницы', async () => {
    const app = createTestApp(renderDocument, render);
    const res = await request(app).get('/');

    expect(fetchPublicHomeMock).toHaveBeenCalledTimes(1);
    expect(res.status).toBe(200);
    expect(res.text).toContain('SSR headline');
    expect(res.text).toContain('window.__INITIAL_DATA__');
  });

  it('возвращает HTML для списка дев-блога', async () => {
    const app = createTestApp(renderDocument, render);
    const res = await request(app).get('/dev-blog');

    expect(fetchDevBlogListMock).toHaveBeenCalledTimes(1);
    expect(res.status).toBe(200);
    expect(res.text).toContain('Первый пост');
    expect(res.text).toContain('window.__INITIAL_DATA__');
  });

  it('возвращает HTML для страницы поста', async () => {
    const app = createTestApp(renderDocument, render);
    const res = await request(app).get('/dev-blog/first-post');

    expect(fetchDevBlogPostMock).toHaveBeenCalledWith('first-post');
    expect(res.status).toBe(200);
    expect(res.text).toContain('Контент');
  });

  it('возвращает статус 500 при ошибке загрузки главной', async () => {
    fetchPublicHomeMock.mockResolvedValueOnce({ data: null, status: 500, error: 'boom', etag: null });

    const app = createTestApp(renderDocument, render);
    const res = await request(app).get('/');

    expect(res.status).toBe(500);
    expect(res.text).toContain('window.__INITIAL_DATA__ = {};');
  });

  it('возвращает статус 404 для отсутствующей записи дев-блога', async () => {
    fetchDevBlogPostMock.mockResolvedValueOnce({ data: null, status: 404, error: 'not found' });

    const app = createTestApp(renderDocument, render);
    const res = await request(app).get('/dev-blog/missing');

    expect(res.status).toBe(404);
    expect(res.text).toContain('window.__INITIAL_DATA__ = {};');
  });
});



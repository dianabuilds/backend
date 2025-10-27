import React from 'react';
import type { FilledContext } from 'react-helmet-async';
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { AppShell } from './AppShell';
import { AppPublicRoutes } from './public/AppPublic';
import type { InitialDataMap } from '@shared/ssr/InitialDataContext';
import { mergeInitialData } from '@shared/ssr/InitialDataContext';
import { fetchPublicHome } from '@shared/api/publicHome';
import { fetchDevBlogList, fetchDevBlogPost } from '@shared/api/devBlog';
import { buildHomeCacheKey, HOME_DEFAULT_SLUG } from './pages/public/HomePage.shared';
import { buildDevBlogListKey, DEV_BLOG_PAGE_SIZE } from './pages/public/DevBlogListPage.shared';
import { buildDevBlogPostKey } from './pages/public/DevBlogPostPage.shared';

export type RenderResult = {
  html: string;
  status: number;
  headers: Record<string, string>;
  initialData: InitialDataMap;
  head?: {
    headTags?: string;
    htmlAttributes?: string;
    bodyAttributes?: string;
  };
  entryClient?: string;
};

const PUBLIC_ROUTE_MATCHERS: Array<(pathname: string) => boolean> = [
  (pathname) => pathname === '/' || pathname === '',
  (pathname) => pathname === '/dev-blog' || pathname.startsWith('/dev-blog/'),
  (pathname) => /^\/n\/[^/]+$/u.test(pathname),
];

function isPublicPathname(pathname: string): boolean {
  return PUBLIC_ROUTE_MATCHERS.some((matcher) => matcher(pathname));
}

async function loadInitialData(url: URL): Promise<{ data: InitialDataMap; status: number }> {
  let initialData: InitialDataMap = {};
  let status = 200;
  const pathname = url.pathname.replace(/\/+$/u, '') || '/';

  if (pathname === '/' || pathname === '') {
    const slug = url.searchParams.get('slug')?.trim() || HOME_DEFAULT_SLUG;
    const { data, status: apiStatus } = await fetchPublicHome(slug === HOME_DEFAULT_SLUG ? undefined : slug);
    status = apiStatus;
    if (data) {
      initialData = mergeInitialData(initialData, { [buildHomeCacheKey(slug)]: data });
    }
  } else if (pathname === '/dev-blog') {
    const pageParam = Number(url.searchParams.get('page') || '1');
    const page = Number.isFinite(pageParam) && pageParam > 0 ? Math.floor(pageParam) : 1;
    const tags = url.searchParams
      .getAll('tag')
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0);
    const from = url.searchParams.get('from')?.trim() || undefined;
    const to = url.searchParams.get('to')?.trim() || undefined;
    const { data, status: apiStatus } = await fetchDevBlogList({
      page,
      limit: DEV_BLOG_PAGE_SIZE,
      tags,
      publishedFrom: from,
      publishedTo: to,
    });
    status = apiStatus;
    if (data) {
      initialData = mergeInitialData(initialData, {
        [buildDevBlogListKey(page, { tags, from, to })]: data,
      });
    }
  } else if (pathname.startsWith('/dev-blog/')) {
    const slug = pathname.replace('/dev-blog/', '');
    if (slug) {
      const { data, status: apiStatus } = await fetchDevBlogPost(slug);
      status = apiStatus;
      if (data) {
        const key = buildDevBlogPostKey(slug);
        if (key) {
          initialData = mergeInitialData(initialData, { [key]: data });
        }
      }
    } else {
      status = 400;
    }
  }

  return { data: initialData, status };
}

export async function render(url: string): Promise<RenderResult | null> {
  const parsedUrl = new URL(url, 'http://localhost');
  const pathname = parsedUrl.pathname.replace(/\/+$/u, '') || '/';

  if (!isPublicPathname(pathname)) {
    return null;
  }

  const { data: initialData, status } = await loadInitialData(parsedUrl);
  const helmetContext = {} as FilledContext;
  const app = (
    <AppShell initialData={initialData} helmetContext={helmetContext}>
      <StaticRouter location={parsedUrl.pathname + parsedUrl.search}>
        <AppPublicRoutes />
      </StaticRouter>
    </AppShell>
  );

  let html: string;
  try {
    html = renderToString(app);
  } catch (error) {
    console.error('[ssr] render crash', { url: parsedUrl.toString(), error });
    throw error;
  }
  if (process.env.NODE_ENV === 'development') {
    console.log('[ssr] render success', {
      url: parsedUrl.toString(),
      htmlLength: html.length,
      status,
      hasData: Boolean(Object.keys(initialData ?? {}).length),
    });
  }
  const helmet = helmetContext.helmet;
  const head = helmet
    ? {
        headTags: [
          helmet.title.toString(),
          helmet.meta.toString(),
          helmet.link.toString(),
          helmet.script.toString(),
          helmet.noscript.toString(),
        ]
          .filter(Boolean)
          .join(''),
        htmlAttributes: helmet.htmlAttributes.toString(),
        bodyAttributes: helmet.bodyAttributes.toString(),
      }
    : undefined;

  return {
    html,
    status,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
    },
    initialData,
    head,
    entryClient: 'src/public-entry.tsx',
  };
}

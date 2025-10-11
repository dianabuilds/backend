/* @vitest-environment node */
import { describe, it, expect, vi } from 'vitest';
vi.mock('react-apexcharts', () => ({ default: () => null }));
vi.mock('apexcharts', () => ({}));
import { renderToString } from 'react-dom/server';
import { StaticRouter } from 'react-router-dom/server';
import { AppShell } from '../../../AppShell';
import { AppPublicRoutes } from '../../../public/AppPublic';
import type { InitialDataMap } from '@shared/ssr/InitialDataContext';
import { buildHomeCacheKey } from '../HomePage.shared';
import { buildDevBlogListKey } from '../DevBlogListPage.shared';
import { buildDevBlogPostKey } from '../DevBlogPostPage.shared';

describe('SSR snapshots', () => {
  it('renders home page blocks from cached data', () => {
    const initialData: InitialDataMap = {
      [buildHomeCacheKey('main')]: {
        slug: 'main',
        version: 1,
        updatedAt: '2025-10-10T10:00:00Z',
        publishedAt: '2025-10-10T10:00:00Z',
        generatedAt: '2025-10-10T10:00:00Z',
        blocks: [
          {
            id: 'hero-1',
            type: 'hero',
            title: 'Hero block',
            enabled: true,
            slots: { headline: 'SSR Hero' },
            layout: null,
            items: [],
            dataSource: null,
          },
        ],
        meta: {},
        fallbacks: [],
      },
    };

    const html = renderToString(
      <AppShell initialData={initialData}>
        <StaticRouter location="/">
          <AppPublicRoutes />
        </StaticRouter>
      </AppShell>,
    );

    expect(html).toContain('SSR Hero');
  });

  it('renders dev blog list from cached data', () => {
    const initialData: InitialDataMap = {
      [buildDevBlogListKey(1, { tags: [], from: undefined, to: undefined })]: {
        items: [
          {
            id: 1,
            slug: 'first-post',
            title: 'First Post',
            summary: 'Short summary for SSR tests.',
            coverUrl: null,
            publishAt: '2025-10-10T10:00:00Z',
            updatedAt: '2025-10-10T10:00:00Z',
            author: { id: '42', name: 'Team' },
            tags: ['updates'],
          },
        ],
        total: 1,
        hasNext: false,
        availableTags: ['updates'],
        dateRange: { start: '2025-10-10T10:00:00Z', end: '2025-10-10T10:00:00Z' },
        appliedTags: [],
      },
    };

    const html = renderToString(
      <AppShell initialData={initialData}>
        <StaticRouter location="/dev-blog">
          <AppPublicRoutes />
        </StaticRouter>
      </AppShell>,
    );

    expect(html).toContain('First Post');
  });

  it('renders dev blog post from cached data', () => {
    const key = buildDevBlogPostKey('first-post');
    if (!key) throw new Error('key not generated');
    const initialData: InitialDataMap = {
      [key]: {
        post: {
          id: 1,
          slug: 'first-post',
          title: 'First Post',
          summary: 'Short summary for SSR tests.',
          coverUrl: null,
          publishAt: '2025-10-10T10:00:00Z',
          updatedAt: '2025-10-10T10:00:00Z',
          author: { id: '42', name: 'Team' },
          content: '<p>Post body</p>',
          status: 'published',
          isPublic: true,
          tags: ['updates'],
        },
        prev: null,
        next: null,
      },
    };

    const html = renderToString(
      <AppShell initialData={initialData}>
        <StaticRouter location="/dev-blog/first-post">
          <AppPublicRoutes />
        </StaticRouter>
      </AppShell>,
    );

    expect(html).toContain('First Post');
    expect(html).toContain('Post body');
  });
});


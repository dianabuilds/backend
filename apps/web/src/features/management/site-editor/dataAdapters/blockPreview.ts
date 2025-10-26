import { managementSiteEditorApi } from '@shared/api/management';
import type { SiteBlockPreviewResponse, SiteBlockPreviewItem } from '@shared/api/management/siteEditor';
import type { HomeBlockType } from '../../home/types';

export type BlockPreviewItem = {
  title: string;
  subtitle?: string | null;
  href?: string | null;
  badge?: string | null;
};

export type BlockPreviewData = {
  items: BlockPreviewItem[];
  locale: string;
  fetchedAt: string;
  source: 'live' | 'mock' | 'fallback' | 'error';
  meta?: Record<string, unknown>;
};

type PreviewFetchOptions = {
  locale: string;
  useLive?: boolean;
};

type PreviewCacheKey = string;

type MockLoader = () => Promise<{ items?: BlockPreviewItem[]; meta?: Record<string, unknown> }>;

const MOCK_LOADERS: Record<string, Record<string, MockLoader>> = {
  hero: {
    ru: () => import('../mocks/hero/ru.json').then((mod) => mod.default),
    en: () => import('../mocks/hero/en.json').then((mod) => mod.default),
  },
  dev_blog_list: {
    ru: () => import('../mocks/dev_blog_list/ru.json').then((mod) => mod.default),
    en: () => import('../mocks/dev_blog_list/en.json').then((mod) => mod.default),
  },
  quests_carousel: {
    ru: () => import('../mocks/quests_carousel/ru.json').then((mod) => mod.default),
    en: () => import('../mocks/quests_carousel/en.json').then((mod) => mod.default),
  },
  nodes_carousel: {
    ru: () => import('../mocks/nodes_carousel/ru.json').then((mod) => mod.default),
    en: () => import('../mocks/nodes_carousel/en.json').then((mod) => mod.default),
  },
  popular_carousel: {
    ru: () => import('../mocks/popular_carousel/ru.json').then((mod) => mod.default),
    en: () => import('../mocks/popular_carousel/en.json').then((mod) => mod.default),
  },
  editorial_picks: {
    ru: () => import('../mocks/editorial_picks/ru.json').then((mod) => mod.default),
    en: () => import('../mocks/editorial_picks/en.json').then((mod) => mod.default),
  },
  recommendations: {
    ru: () => import('../mocks/recommendations/ru.json').then((mod) => mod.default),
    en: () => import('../mocks/recommendations/en.json').then((mod) => mod.default),
  },
  custom_carousel: {
    ru: () => import('../mocks/custom_carousel/ru.json').then((mod) => mod.default),
    en: () => import('../mocks/custom_carousel/en.json').then((mod) => mod.default),
  },
};

const CACHE = new Map<PreviewCacheKey, Promise<BlockPreviewData>>();
const DEFAULT_LOCALE = 'ru';

function cacheKey(block: string, locale: string): PreviewCacheKey {
  return `${block}:${locale}`;
}

function sanitizeLocale(locale: string | undefined): string {
  const trimmed = locale?.trim().toLowerCase();
  if (!trimmed) {
    return DEFAULT_LOCALE;
  }
  if (trimmed.startsWith('en')) {
    return 'en';
  }
  if (trimmed.startsWith('ru')) {
    return 'ru';
  }
  return DEFAULT_LOCALE;
}

function mapServerItem(item: SiteBlockPreviewItem): BlockPreviewItem | null {
  if (!item || typeof item.title !== 'string' || !item.title.trim()) {
    return null;
  }
  return {
    title: item.title,
    subtitle: item.subtitle ?? null,
    href: item.href ?? null,
    badge: item.badge ?? null,
  };
}

function mapServerResponse(response: SiteBlockPreviewResponse, fallbackLocale: string): BlockPreviewData {
  const locale = sanitizeLocale(response.locale) || fallbackLocale;
  const items = (response.items ?? [])
    .map((entry) => mapServerItem(entry))
    .filter((entry): entry is BlockPreviewItem => Boolean(entry));
  const fetchedAt = response.fetched_at ?? response.fetchedAt ?? new Date().toISOString();
  const sourceRaw = response.source ?? (items.length ? 'live' : 'mock');
  const source = sourceRaw === 'live' || sourceRaw === 'mock' || sourceRaw === 'fallback' ? sourceRaw : 'live';
  const meta = response.meta ?? {};
  return {
    items,
    locale,
    fetchedAt,
    source,
    meta,
  };
}

async function loadMock(block: string, locale: string): Promise<BlockPreviewData | null> {
  const loaders = MOCK_LOADERS[block];
  if (!loaders) {
    return null;
  }
  const loader = loaders[locale] ?? loaders[DEFAULT_LOCALE];
  if (!loader) {
    return null;
  }
  try {
    const mock = await loader();
    const items = (mock.items ?? []).map((item) => ({
      title: item.title,
      subtitle: item.subtitle ?? null,
      href: item.href ?? null,
      badge: item.badge ?? null,
    }));
    return {
      items,
      locale,
      fetchedAt: new Date().toISOString(),
      source: 'mock',
      meta: { ...(mock.meta ?? {}), block, mockLocale: locale },
    };
  } catch (error) {
    console.warn('[site-editor] failed to load preview mock', { block, locale, error });
    return null;
  }
}

async function fetchServerPreview(block: string, locale: string): Promise<BlockPreviewData | null> {
  try {
    const response = await managementSiteEditorApi.previewSiteBlock(block, { locale });
    return mapServerResponse(response, locale);
  } catch (error) {
    console.warn('[site-editor] server preview failed', { block, locale, error });
    return null;
  }
}

async function resolvePreview(block: string, locale: string, useLive: boolean): Promise<BlockPreviewData> {
  const normalizedLocale = sanitizeLocale(locale);
  if (useLive) {
    const server = await fetchServerPreview(block, normalizedLocale);
    if (server) {
      if (server.items.length > 0) {
        return server;
      }
      if (server.source !== 'live') {
        return server;
      }
      const mock = await loadMock(block, normalizedLocale);
      if (mock) {
        return { ...mock, meta: { ...(mock.meta ?? {}), fallback: 'mock', serverMeta: server.meta } };
      }
      return server;
    }
  }

  const mock = await loadMock(block, normalizedLocale);
  if (mock) {
    return mock;
  }
  return {
    items: [],
    locale: normalizedLocale,
    fetchedAt: new Date().toISOString(),
    source: 'error',
    meta: { reason: 'preview_not_available', block },
  };
}

export function getBlockPreview(block: HomeBlockType | string, options: PreviewFetchOptions): Promise<BlockPreviewData> {
  const locale = sanitizeLocale(options.locale);
  const key = cacheKey(block, locale);
  const useLive = options.useLive ?? true;
  const cached = CACHE.get(key);
  if (cached) {
    return cached;
  }
  const promise = resolvePreview(block, locale, useLive)
    .then((result) => ({ ...result, locale }))
    .catch((error) => {
      CACHE.delete(key);
      throw error;
    });
  CACHE.set(key, promise);
  return promise;
}

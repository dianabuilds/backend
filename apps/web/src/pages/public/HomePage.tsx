import React from 'react';
import { Helmet } from 'react-helmet-async';
import { useLocation, useSearchParams } from 'react-router-dom';
import { fetchPublicHome } from '@shared/api/publicHome';
import type { HomeResponse } from '@shared/types/homePublic';
import { useInitialData } from '@shared/ssr/InitialDataContext';
import { useLocale, type Locale } from '@shared/i18n/locale';
import { resolveSiteOrigin, buildCanonicalUrl, pickLocalizedString, pickString, extractAlternateLinks, ensureAbsoluteUrl } from '@shared/seo';
import { rumEvent } from '@shared/rum';
import { reportFeatureError } from '@shared/utils/sentry';
import { HomeUnavailable, HOME_FALLBACK_DEFAULT_MESSAGE } from './components/HomeUnavailable';
import { HomeBlocks } from '@features/public/home';
import { HomeBlocksBoundary } from './components/HomeBlocksBoundary';
import { HOME_DEFAULT_SLUG, buildHomeCacheKey } from './HomePage.shared';

const DEFAULT_ERROR_MESSAGE = HOME_FALLBACK_DEFAULT_MESSAGE;

const HOME_DEFAULT_TITLE: Record<Locale, string> = {
  ru: 'Главная — Caves World',
  en: 'Caves World — interactive worlds curated by editors',
};

const HOME_DEFAULT_DESCRIPTION: Record<Locale, string> = {
  ru: 'Истории, подборки и квесты Caves на одной странице. Платформа с редакторскими блоками и свежими материалами.',
  en: 'Curated blocks, stories, and quests from the Caves team gathered on the homepage.',
};

const OG_LOCALE_MAP: Record<Locale, string> = {
  ru: 'ru_RU',
  en: 'en_US',
};

const SITE_NAME = 'Caves World';

const HOME_CRITICAL_CSS = `
main[data-home-root] {
  margin-left: auto;
  margin-right: auto;
  max-width: 72rem;
  padding: 3rem 1rem 5rem;
}
@media (min-width: 1024px) {
  main[data-home-root] {
    padding-left: 0;
    padding-right: 0;
  }
}
main[data-home-root] > header {
  margin-bottom: 3rem;
  text-align: center;
}
main[data-home-root] > header [data-kicker] {
  font-size: 0.75rem;
  letter-spacing: 0.3em;
  font-weight: 600;
  text-transform: uppercase;
  color: #4338ca;
}
main[data-home-root] > header h1 {
  margin: 0;
  font-size: 2.25rem;
  line-height: 2.5rem;
  font-weight: 600;
  color: #111827;
}
@media (min-width: 1024px) {
  main[data-home-root] > header h1 {
    font-size: 3rem;
    line-height: 1.1;
  }
}
main[data-home-root] > header [data-description] {
  margin-left: auto;
  margin-right: auto;
  max-width: 32rem;
  font-size: 0.875rem;
  color: #4b5563;
}
body.dark main[data-home-root] > header h1 {
  color: #ffffff;
}
body.dark main[data-home-root] > header [data-description] {
  color: #d1d5db;
}
`

const BlocksFallback = (): React.ReactElement => (
  <div className="space-y-6">
    <div className="h-40 rounded-3xl border border-gray-200 bg-gray-100 dark:border-dark-500 dark:bg-dark-700" />
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 3 }).map((_, index) => (
        <div
          key={index}
          className="h-48 rounded-xl border border-gray-200 bg-gray-100 dark:border-dark-500 dark:bg-dark-700"
        />
      ))}
    </div>
  </div>
);

type HomeMeta = {
  title: string;
  description?: string;
  canonical: string;
  ogTitle: string;
  ogDescription?: string;
  ogType: string;
  ogImage?: string;
  ogSiteName: string;
  ogLocale: string;
  twitterCard: string;
  keywords?: string;
  robots?: string;
  alternates: Array<{ hreflang: string; href: string }>;
};

function resolveHomeMeta(
  meta: Record<string, unknown> | undefined,
  locale: Locale,
  fullPath: string,
): HomeMeta {
  const fallbackLocale: Locale = locale === 'ru' ? 'en' : 'ru';
  const metaRecord = meta ?? {};
  const origin = resolveSiteOrigin(metaRecord);
  const defaultTitle = HOME_DEFAULT_TITLE[locale] ?? HOME_DEFAULT_TITLE.ru;
  const defaultDescription = HOME_DEFAULT_DESCRIPTION[locale] ?? HOME_DEFAULT_DESCRIPTION.ru;
  const title = pickLocalizedString(metaRecord, 'title', locale, fallbackLocale) ?? defaultTitle;
  const description = pickLocalizedString(metaRecord, 'description', locale, fallbackLocale) ?? defaultDescription;
  const canonicalCandidate =
    pickLocalizedString(metaRecord, 'canonical', locale, fallbackLocale) ??
    pickString(metaRecord, 'canonical', 'canonicalUrl', 'canonical_url', 'url', 'path');
  const canonical = buildCanonicalUrl(canonicalCandidate ?? fullPath, origin);
  const ogSource =
    (metaRecord.og && typeof metaRecord.og === 'object' ? (metaRecord.og as Record<string, unknown>) : undefined) ??
    (metaRecord.openGraph && typeof metaRecord.openGraph === 'object'
      ? (metaRecord.openGraph as Record<string, unknown>)
      : undefined);
  const ogTitle = pickLocalizedString(ogSource, 'title', locale, fallbackLocale) ?? title;
  const ogDescription = pickLocalizedString(ogSource, 'description', locale, fallbackLocale) ?? description;
  const ogType =
    pickLocalizedString(ogSource, 'type', locale, fallbackLocale) ??
    pickString(ogSource, 'type', 'ogType', 'og_type') ??
    pickLocalizedString(metaRecord, 'type', locale, fallbackLocale) ??
    pickString(metaRecord, 'type', 'ogType', 'og_type') ??
    'website';
  const ogImageRaw =
    pickLocalizedString(ogSource, 'image', locale, fallbackLocale) ??
    pickLocalizedString(metaRecord, 'image', locale, fallbackLocale) ??
    pickLocalizedString(metaRecord, 'ogImage', locale, fallbackLocale) ??
    pickString(ogSource, 'image', 'imageUrl', 'image_url', 'ogImage', 'og_image', 'og:image') ??
    pickString(metaRecord, 'image', 'imageUrl', 'image_url', 'ogImage', 'og_image', 'og:image');
  const ogImage = ensureAbsoluteUrl(ogImageRaw, origin);
  const keywords =
    pickLocalizedString(metaRecord, 'keywords', locale, fallbackLocale) ??
    pickString(metaRecord, 'keywords');
  const robots =
    pickLocalizedString(metaRecord, 'robots', locale, fallbackLocale) ??
    pickString(metaRecord, 'robots', 'robotsContent');
  const twitterSource =
    (metaRecord.twitter && typeof metaRecord.twitter === 'object'
      ? (metaRecord.twitter as Record<string, unknown>)
      : undefined) ??
    (metaRecord.twitterCard && typeof metaRecord.twitterCard === 'object'
      ? (metaRecord.twitterCard as Record<string, unknown>)
      : undefined);
  const twitterCard =
    pickLocalizedString(twitterSource, 'card', locale, fallbackLocale) ??
    pickLocalizedString(twitterSource, 'type', locale, fallbackLocale) ??
    pickString(twitterSource, 'card', 'type') ??
    'summary_large_image';
  const siteName =
    pickLocalizedString(metaRecord, 'siteName', locale, fallbackLocale) ??
    pickLocalizedString(ogSource, 'siteName', locale, fallbackLocale) ??
    pickString(metaRecord, 'siteName', 'site_name') ??
    pickString(ogSource, 'siteName', 'site_name') ??
    SITE_NAME;
  const alternatesList = extractAlternateLinks(metaRecord, origin);
  const alternatesMap = new Map<string, { hreflang: string; href: string }>();
  for (const item of alternatesList) {
    const key = item.hreflang.toLowerCase();
    if (!alternatesMap.has(key)) {
      alternatesMap.set(key, { hreflang: item.hreflang, href: item.href });
    }
  }
  const localeKey = locale.toLowerCase();
  if (!alternatesMap.has(localeKey)) {
    alternatesMap.set(localeKey, { hreflang: locale, href: canonical });
  }
  if (!alternatesMap.has('x-default')) {
    alternatesMap.set('x-default', { hreflang: 'x-default', href: canonical });
  }
  return {
    title,
    description,
    canonical,
    ogTitle,
    ogDescription,
    ogType,
    ogImage,
    ogSiteName: siteName,
    ogLocale: OG_LOCALE_MAP[locale] ?? OG_LOCALE_MAP.ru,
    twitterCard,
    keywords,
    robots,
    alternates: Array.from(alternatesMap.values()),
  };
}

type ReloadAttemptsMap = Record<string, number>;

type HomeState = {
  loading: boolean;
  error: string | null;
  data: HomeResponse | null;
  etag: string | null;
  status: number | null;
  source: 'cache' | 'network' | null;
};

type LoadRun = {
  slug: string;
  attempt: number;
  startAt: number;
  status: 'idle' | 'success' | 'error';
};

function createInitialState(initial: HomeResponse | undefined): HomeState {
  if (initial) {
    return {
      loading: false,
      error: null,
      data: initial,
      etag: initial.etag ?? null,
      status: 200,
      source: 'cache',
    };
  }
  return {
    loading: true,
    error: null,
    data: null,
    etag: null,
    status: null,
    source: null,
  };
}

function resolveSlug(params: URLSearchParams): string {
  const raw = params.get('slug');
  if (!raw) return HOME_DEFAULT_SLUG;
  const normalized = raw.trim();
  return normalized.length ? normalized : HOME_DEFAULT_SLUG;
}

function getNow(): number {
  if (typeof performance !== 'undefined' && typeof performance.now === 'function') {
    return performance.now();
  }
  return Date.now();
}

export default function HomePage(): React.ReactElement {
  const locale = useLocale();
  const location = useLocation();
  const [params] = useSearchParams();
  const slug = resolveSlug(params);
  const cacheKey = React.useMemo(() => buildHomeCacheKey(slug), [slug]);
  const cached = useInitialData<HomeResponse>(cacheKey);

  const [reloadAttempts, setReloadAttempts] = React.useState<ReloadAttemptsMap>({});
  const attempt = reloadAttempts[slug] ?? 0;

  const [state, setState] = React.useState<HomeState>(() => createInitialState(cached));
  const { loading, error, data, etag, status, source } = state;

  const currentData = data ?? cached ?? null;
  const metaRecord = React.useMemo(() => {
    if (currentData?.meta && typeof currentData.meta === 'object' && !Array.isArray(currentData.meta)) {
      return currentData.meta as Record<string, unknown>;
    }
    return undefined;
  }, [currentData]);
  const homeMeta = React.useMemo(
    () => resolveHomeMeta(metaRecord, locale, `${location.pathname}${location.search}`),
    [metaRecord, locale, location.pathname, location.search],
  );

  const latestSuccessRef = React.useRef<{ slug: string; data: HomeResponse } | null>(
    cached ? { slug, data: cached } : null,
  );
  const previousSlugRef = React.useRef<string>(slug);
  const loadRunRef = React.useRef<LoadRun>({ slug, attempt, startAt: getNow(), status: 'idle' });

  React.useEffect(() => {
    loadRunRef.current = { slug, attempt, startAt: getNow(), status: 'idle' };
    const lastSuccess =
      latestSuccessRef.current && latestSuccessRef.current.slug === slug
        ? latestSuccessRef.current.data
        : null;
    const baseline = lastSuccess ?? (cached && attempt === 0 ? cached : null);

    rumEvent('home.load_start', {
      slug,
      retry: attempt > 0,
      hasCachedData: Boolean(baseline),
      configVersion: baseline?.version ?? null,
      etag: baseline?.etag ?? null,
    });

    if (cached && attempt === 0) {
      setState({
        loading: false,
        error: null,
        data: cached,
        etag: cached.etag ?? null,
        status: 200,
        source: 'cache',
      });
      previousSlugRef.current = slug;
      if (!latestSuccessRef.current || latestSuccessRef.current.slug !== slug) {
        latestSuccessRef.current = { slug, data: cached };
      }
      return;
    }

    setState((prev) => {
      const sameSlug = previousSlugRef.current === slug;
      const keepData = sameSlug && attempt > 0 && prev.data != null;
      return {
        loading: true,
        error: null,
        data: keepData ? prev.data : null,
        etag: keepData ? prev.etag : null,
        status: keepData ? prev.status : null,
        source: keepData ? prev.source : null,
      };
    });

    let active = true;

    (async () => {
      try {
        const { data: result, status: responseStatus, error: fetchError, etag: responseEtag } =
          await fetchPublicHome(slug === HOME_DEFAULT_SLUG ? undefined : slug);
        if (!active) return;

        if (fetchError || !result) {
          const message = fetchError ?? DEFAULT_ERROR_MESSAGE;
          setState({
            loading: false,
            error: message,
            data: null,
            etag: responseEtag ?? null,
            status: responseStatus,
            source: null,
          });

          const last = latestSuccessRef.current && latestSuccessRef.current.slug === slug
            ? latestSuccessRef.current.data
            : baseline;
          const errorForSentry = fetchError ? new Error(fetchError) : new Error(message);
          reportFeatureError(errorForSentry, 'home-public', {
            slug,
            status: responseStatus,
            configVersion: last?.version ?? null,
            etag: responseEtag ?? last?.etag ?? null,
            retry: attempt > 0,
            message,
          });
          return;
        }

        const nextData: HomeResponse = { ...result, etag: result.etag ?? responseEtag ?? null };
        setState({
          loading: false,
          error: null,
          data: nextData,
          etag: nextData.etag ?? null,
          status: responseStatus,
          source: 'network',
        });
        latestSuccessRef.current = { slug, data: nextData };
      } catch (error) {
        if (!active) return;
        const statusCode = typeof (error as any)?.status === 'number' ? (error as any).status : null;
        const message =
          error instanceof Error && error.message ? error.message : DEFAULT_ERROR_MESSAGE;
        setState({
          loading: false,
          error: message,
          data: null,
          etag: null,
          status: statusCode,
          source: null,
        });
        const last = latestSuccessRef.current && latestSuccessRef.current.slug === slug
          ? latestSuccessRef.current.data
          : baseline;
        reportFeatureError(error, 'home-public', {
          slug,
          status: statusCode ?? undefined,
          configVersion: last?.version ?? null,
          etag: last?.etag ?? null,
          retry: attempt > 0,
          message,
        });
      } finally {
        if (active) {
          previousSlugRef.current = slug;
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [slug, attempt, cached]);

  React.useEffect(() => {
    if (data) {
      latestSuccessRef.current = { slug, data };
    }
  }, [data, slug]);

  const handleReload = React.useCallback(() => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    setReloadAttempts((prev) => {
      const current = prev[slug] ?? 0;
      return { ...prev, [slug]: current + 1 };
    });
  }, [slug]);

  React.useEffect(() => {
    const run = loadRunRef.current;
    if (run.slug !== slug || run.attempt !== attempt) return;
    if (loading) return;

    const duration = Math.round(Math.max(0, getNow() - run.startAt));

    if (error) {
      if (run.status === 'error') return;
      run.status = 'error';
      const last = latestSuccessRef.current && latestSuccessRef.current.slug === slug
        ? latestSuccessRef.current.data
        : null;
      rumEvent('home.load_error', {
        slug,
        status,
        message: error,
        configVersion: last?.version ?? null,
        etag: etag ?? last?.etag ?? null,
        durationMs: duration,
        retry: attempt > 0,
      });
      return;
    }

    if (data) {
      if (run.status === 'success') return;
      run.status = 'success';
      rumEvent('home.load_success', {
        slug,
        configVersion: data.version,
        etag: data.etag ?? etag ?? null,
        blocks: data.blocks.length,
        fallbacks: data.fallbacks.length,
        renderTimeMs: duration,
        source,
        retry: attempt > 0,
      });
    }
  }, [loading, error, data, slug, attempt, etag, status, source]);

  return (
    <main data-home-root className="mx-auto max-w-6xl px-4 pb-20 pt-12 lg:px-0">
      <Helmet>
        <title>{homeMeta.title}</title>
        {homeMeta.description && <meta name="description" content={homeMeta.description} />}
        <link rel="canonical" href={homeMeta.canonical} />
        <meta property="og:type" content={homeMeta.ogType} />
        <meta property="og:title" content={homeMeta.ogTitle} />
        {homeMeta.ogDescription && <meta property="og:description" content={homeMeta.ogDescription} />}
        <meta property="og:url" content={homeMeta.canonical} />
        <meta property="og:locale" content={homeMeta.ogLocale} />
        <meta property="og:site_name" content={homeMeta.ogSiteName} />
        {homeMeta.ogImage && <meta property="og:image" content={homeMeta.ogImage} />}
        <meta name="twitter:card" content={homeMeta.twitterCard} />
        <meta name="twitter:title" content={homeMeta.ogTitle} />
        {homeMeta.ogDescription && <meta name="twitter:description" content={homeMeta.ogDescription} />}
        {homeMeta.ogImage && <meta name="twitter:image" content={homeMeta.ogImage} />}
        {homeMeta.keywords && <meta name="keywords" content={homeMeta.keywords} />}
        {homeMeta.robots && <meta name="robots" content={homeMeta.robots} />}
        <style id="home-critical-css">{HOME_CRITICAL_CSS}</style>
        {homeMeta.alternates.map((item) => (
          <link key={item.hreflang} rel="alternate" hrefLang={item.hreflang} href={item.href} />
        ))}
      </Helmet>
      <header className="mb-12 space-y-4 text-center">
        <p data-kicker className="text-xs font-semibold uppercase tracking-[0.3em] text-primary-600 dark:text-primary-300">Caves World</p>
        <h1 className="text-4xl font-semibold text-gray-900 dark:text-white">Интерактивные миры, собранные редакцией</h1>
        <p data-description className="mx-auto max-w-2xl text-sm text-gray-600 dark:text-dark-100">
          Главная страница формируется динамически на основе блоков, которые настраивает контент-команда. Материалы загружаются до первого рендера.
        </p>
      </header>

      {loading && !data && <BlocksFallback />}

      {!loading && error && <HomeUnavailable message={error} onRetry={handleReload} />}

      {!error && data && (
        <div className="space-y-10">
          <HomeBlocksBoundary
            slug={slug}
            configVersion={data.version}
            etag={data.etag ?? etag ?? null}
            onRetry={handleReload}
            resetKey={`${slug}:${data.version ?? 'na'}:${attempt}`}
          >
            <HomeBlocks blocks={data.blocks} />
          </HomeBlocksBoundary>

          {data.fallbacks.length > 0 && (
            <section className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800 dark:border-amber-500/50 dark:bg-amber-900/40 dark:text-amber-100">
              <h2 className="mb-2 text-base font-semibold">Использованы запасные источники</h2>
              <p className="text-sm">
                Некоторые блоки отображаются с резервными данными, так как основная выдача временно недоступна.
              </p>
            </section>
          )}
        </div>
      )}
    </main>
  );
}




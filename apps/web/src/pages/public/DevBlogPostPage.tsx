import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Link, useLocation, useParams } from 'react-router-dom';
import { buildDevBlogPostKey } from './DevBlogPostPage.shared';
import dayjs from 'dayjs';
import 'dayjs/locale/en';
import 'dayjs/locale/ru';
import { Button, Card, Skeleton, Tag, CopyButton } from '@ui';
import { Link2, Send } from '@icons';
import { sanitizeHtml } from '@shared/utils/sanitize';
import { fetchDevBlogPost } from '@shared/api/devBlog';
import type { DevBlogDetailResponse, DevBlogSummary } from '@shared/types/devBlog';
import { useInitialData } from '@shared/ssr/InitialDataContext';
import { usePrefetchLink } from '@shared/hooks/usePrefetchLink';
import { resolveSiteOrigin, buildCanonicalUrl, ensureAbsoluteUrl } from '@shared/seo';
import { useLocale } from '@shared/i18n/locale';
import type { Locale } from '@shared/i18n/locale';

const POST_DATE_FORMAT: Record<Locale, string> = {
  en: 'MMMM D, YYYY, HH:mm',
  ru: 'D MMMM YYYY, HH:mm',
};

const HEADER_KICKER: Record<Locale, string> = {
  en: 'Dev Blog',
  ru: 'Dev Blog',
};

const BACK_LABEL: Record<Locale, string> = {
  en: 'Back to blog',
  ru: 'РќР°Р·Р°Рґ Рє Р±Р»РѕРіСѓ',
};

const AUTHOR_LABEL: Record<Locale, string> = {
  en: 'Author',
  ru: 'РђРІС‚РѕСЂ',
};

const SHARE_TITLE: Record<Locale, string> = {
  en: 'Share this post',
  ru: 'РџРѕРґРµР»РёС‚СЊСЃСЏ РїРѕСЃС‚РѕРј',
};

const SHARE_PRIMARY: Record<Locale, string> = {
  en: 'Share',
  ru: 'РџРѕРґРµР»РёС‚СЊСЃСЏ',
};

const SHARE_COPY: Record<Locale, string> = {
  en: 'Copy link',
  ru: 'РЎРєРѕРїРёСЂРѕРІР°С‚СЊ СЃСЃС‹Р»РєСѓ',
};

const SHARE_COPIED: Record<Locale, string> = {
  en: 'Link copied',
  ru: 'РЎСЃС‹Р»РєР° СЃРєРѕРїРёСЂРѕРІР°РЅР°',
};

const PREVIOUS_POST: Record<Locale, string> = {
  en: 'Previous post',
  ru: 'РџСЂРµРґС‹РґСѓС‰РёР№ РїРѕСЃС‚',
};

const NEXT_POST: Record<Locale, string> = {
  en: 'Next post',
  ru: 'РЎР»РµРґСѓСЋС‰РёР№ РїРѕСЃС‚',
};

const NO_ADJACENT: Record<Locale, string> = {
  en: 'No other posts yet.',
  ru: 'Р”СЂСѓРіРёС… РїРѕСЃС‚РѕРІ РїРѕРєР° РЅРµС‚.',
};

const FALLBACK_ERROR: Record<Locale, string> = {
  en: 'Failed to load the post.',
  ru: 'РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РїРѕСЃС‚.',
};

const FALLBACK_MISSING: Record<Locale, string> = {
  en: 'Post slug is missing.',
  ru: 'РћС‚СЃСѓС‚СЃС‚РІСѓРµС‚ РёРґРµРЅС‚РёС„РёРєР°С‚РѕСЂ РїРѕСЃС‚Р°.',
};

const SHARE_DESCRIPTION: Record<Locale, string> = {
  en: 'Stories, research, and platform updates from the Caves team.',
  ru: 'РСЃС‚РѕСЂРёРё, РёСЃСЃР»РµРґРѕРІР°РЅРёСЏ Рё РѕР±РЅРѕРІР»РµРЅРёСЏ РїР»Р°С‚С„РѕСЂРјС‹ РѕС‚ РєРѕРјР°РЅРґС‹ Caves.',
};

const OG_LOCALE_MAP: Record<Locale, string> = {
  ru: 'ru_RU',
  en: 'en_US',
};

const SITE_NAME = 'Caves World';
const TWITTER_CARD = 'summary_large_image';

const UNTITLED_POST: Record<Locale, string> = {
  en: 'Untitled',
  ru: 'Р‘РµР· РЅР°Р·РІР°РЅРёСЏ',
};

type PostState = {
  loading: boolean;
  error: string | null;
  data: DevBlogDetailResponse | null;
};

function createInitialState(initial: DevBlogDetailResponse | undefined): PostState {
  if (initial) {
    return { loading: false, error: null, data: initial };
  }
  return { loading: true, error: null, data: null };
}

function formatDate(value: string | null | undefined, locale: Locale): string | null {
  if (!value) return null;
  const parsed = dayjs(value);
  if (!parsed.isValid()) return null;
  return parsed.locale(locale).format(POST_DATE_FORMAT[locale] ?? POST_DATE_FORMAT.en);
}

function pick(map: Record<Locale, string>, locale: Locale): string {
  return map[locale] ?? map.ru;
}

export default function DevBlogPostPage(): React.ReactElement {
  const locale = useLocale();
  const location = useLocation();
  const { slug } = useParams();
  const cacheKey = React.useMemo(() => buildDevBlogPostKey(slug ?? undefined), [slug]);
  const cached = useInitialData<DevBlogDetailResponse>(cacheKey ?? '');
  const [state, setState] = React.useState<PostState>(() => createInitialState(cached));
  const { loading, error, data } = state;

  React.useEffect(() => {
    if (!slug) {
      setState({ loading: false, error: pick(FALLBACK_MISSING, locale), data: null });
      return;
    }
    if (cached) {
      setState({ loading: false, error: null, data: cached });
      return;
    }
    let active = true;
    setState({ loading: true, error: null, data: null });
    (async () => {
      const { data: result, error: err } = await fetchDevBlogPost(slug);
      if (!active) return;
      if (err || !result) {
        setState({ loading: false, error: err ?? pick(FALLBACK_ERROR, locale), data: null });
      } else {
        setState({ loading: false, error: null, data: result });
      }
    })();
    return () => {
      active = false;
    };
  }, [slug, cached, locale]);

  const post = data?.post ?? cached?.post ?? null;
  const sanitized = React.useMemo(() => sanitizeHtml(post?.content ?? ''), [post?.content]);
  const origin = React.useMemo(() => resolveSiteOrigin(), []);
  const canonicalUrl = React.useMemo(
    () => buildCanonicalUrl(`${location.pathname}${location.search}`, origin),
    [location.pathname, location.search, origin],
  );
  const ogImage = ensureAbsoluteUrl(post?.coverUrl ?? undefined, origin);
  const alternates = React.useMemo(
    () => [
      { hreflang: locale, href: canonicalUrl },
      { hreflang: 'x-default', href: canonicalUrl },
    ],
    [canonicalUrl, locale],
  );
  const ogLocale = OG_LOCALE_MAP[locale] ?? OG_LOCALE_MAP.ru;
  const listPrefetch = usePrefetchLink('/dev-blog');
  const heroImage = ogImage ?? post?.coverUrl ?? null;
  const metaDescription = post?.summary?.trim() || pick(SHARE_DESCRIPTION, locale);
  const title = post?.title?.trim() || pick(UNTITLED_POST, locale);
  const jsonLd = React.useMemo(() => {
    if (!post) return null;
    const payload: Record<string, unknown> = {
      '@context': 'https://schema.org',
      '@type': 'BlogPosting',
      headline: title,
      description: metaDescription,
      mainEntityOfPage: canonicalUrl,
    };
    if (post.publishAt) payload.datePublished = post.publishAt;
    if (post.updatedAt) payload.dateModified = post.updatedAt;
    if (ogImage) payload.image = [ogImage];
    if (post.author?.name) {
      payload.author = { '@type': 'Person', name: post.author.name };
    }
    return payload;
  }, [post, title, metaDescription, canonicalUrl, ogImage]);

  const formattedPublishAt = formatDate(post?.publishAt, locale);
  const formattedUpdatedAt = post?.updatedAt ? formatDate(post.updatedAt, locale) : null;
  const authorName = post?.author?.name || (post?.author?.id ? `#${post.author.id}` : null);
  const shareSupported = typeof navigator !== 'undefined' && typeof (navigator as any).share === 'function';

  return (
    <main className="mx-auto max-w-3xl px-4 pb-20 pt-12 lg:px-0">
      <Helmet>
        <title>{title}</title>
        <meta name="description" content={metaDescription} />
        <link rel="canonical" href={canonicalUrl} />
        <meta property="og:type" content="article" />
        <meta property="og:title" content={title} />
        <meta property="og:description" content={metaDescription} />
        <meta property="og:url" content={canonicalUrl} />
        <meta property="og:locale" content={ogLocale} />
        <meta property="og:site_name" content={SITE_NAME} />
        {ogImage && <meta property="og:image" content={ogImage} />}
        <meta name="twitter:card" content={TWITTER_CARD} />
        <meta name="twitter:title" content={title} />
        <meta name="twitter:description" content={metaDescription} />
        {ogImage && <meta name="twitter:image" content={ogImage} />}
        {alternates.map((item) => (
          <link key={item.hreflang} rel="alternate" hrefLang={item.hreflang} href={item.href} />
        ))}
        {jsonLd && (
          <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
        )}
      </Helmet>

      {loading && <DevBlogPostSkeleton />}

      {!loading && error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-700 dark:bg-red-900/40 dark:text-red-200">
          {error}
        </div>
      )}

      {!loading && !error && post && (
        <article className="space-y-10">
          <nav className="text-sm text-gray-500 dark:text-dark-200">
            <Link to="/dev-blog" className="hover:text-primary-600" {...listPrefetch}>
              {pick(BACK_LABEL, locale)}
            </Link>
          </nav>

          <header className="space-y-4">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-primary-600 dark:text-primary-300">
              {pick(HEADER_KICKER, locale)}
            </p>
            <h1 className="text-4xl font-semibold text-gray-900 dark:text-white">{title}</h1>
            <div className="flex flex-wrap gap-3 text-sm text-gray-500 dark:text-dark-200">
              {formattedPublishAt && <span>{formattedPublishAt}</span>}
              {formattedUpdatedAt && formattedUpdatedAt !== formattedPublishAt && (
                <span>вЂў {formattedUpdatedAt}</span>
              )}
              {authorName && (
                <span>
                  вЂў {pick(AUTHOR_LABEL, locale)}: <span className="font-medium text-gray-700 dark:text-dark-50">{authorName}</span>
                </span>
              )}
            </div>
            {Array.isArray(post.tags) && post.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {post.tags.map((tag: string) => (
                  <Tag key={tag} color="primary">
                    #{tag}
                  </Tag>
                ))}
              </div>
            )}
          </header>

          {heroImage && (
            <figure className="overflow-hidden rounded-2xl">
              <img
                src={heroImage}
                alt={post?.title ?? ''}
                loading="eager"
                decoding="async"
                fetchPriority="high"
                className="w-full object-cover"
              />
            </figure>
          )}

          <SharePanel
            locale={locale}
            canonicalUrl={canonicalUrl}
            shareSupported={shareSupported}
            title={title}
            description={metaDescription}
          />

          <div className="prose max-w-none dark:prose-invert" dangerouslySetInnerHTML={{ __html: sanitized }} />

          <footer className="space-y-6 border-t border-gray-200 pt-6 dark:border-dark-600">
            <h2 className="text-sm font-semibold uppercase tracking-[0.3em] text-gray-500 dark:text-dark-200">
              {pick(PREVIOUS_POST, locale)} / {pick(NEXT_POST, locale)}
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              {data?.prev ? (
                <AdjacentCard label={pick(PREVIOUS_POST, locale)} item={data.prev} locale={locale} />
              ) : (
                <PlaceholderCard text={pick(NO_ADJACENT, locale)} />
              )}
              {data?.next ? (
                <AdjacentCard label={pick(NEXT_POST, locale)} item={data.next} locale={locale} />
              ) : (
                <PlaceholderCard text={pick(NO_ADJACENT, locale)} />
              )}
            </div>
          </footer>
        </article>
      )}
    </main>
  );
}

type SharePanelProps = {
  locale: Locale;
  canonicalUrl: string;
  shareSupported: boolean;
  title: string;
  description: string;
};

function SharePanel({ locale, canonicalUrl, shareSupported, title, description }: SharePanelProps): React.ReactElement {
  const handleNativeShare = React.useCallback(async () => {
    if (typeof navigator === 'undefined') return;
    const nav = navigator as Navigator & { share?: (data: { title?: string; text?: string; url?: string }) => Promise<void> };
    if (typeof nav.share !== 'function') return;
    try {
      await nav.share({ title, text: description, url: canonicalUrl });
    } catch {
      // ignore user cancellation
    }
  }, [title, description, canonicalUrl]);

  return (
    <section className="rounded-2xl border border-gray-200 bg-white/70 p-5 shadow-sm dark:border-dark-600 dark:bg-dark-800/60">
      <p className="mb-3 text-xs font-semibold uppercase tracking-[0.3em] text-gray-500 dark:text-dark-200">
        {pick(SHARE_TITLE, locale)}
      </p>
      <div className="flex flex-wrap gap-3">
        {shareSupported && (
          <Button
            variant="outlined"
            color="neutral"
            onClick={handleNativeShare}
            className="flex items-center gap-2"
          >
            <Send className="h-4 w-4" />
            {pick(SHARE_PRIMARY, locale)}
          </Button>
        )}
        <CopyButton value={canonicalUrl}>
          {({ copy, copied }) => (
            <Button
              variant="ghost"
              color="neutral"
              onClick={copy}
              className="flex items-center gap-2"
            >
              <Link2 className="h-4 w-4" />
              {copied ? pick(SHARE_COPIED, locale) : pick(SHARE_COPY, locale)}
            </Button>
          )}
        </CopyButton>
      </div>
    </section>
  );
}

type AdjacentCardProps = {
  label: string;
  item: DevBlogSummary;
  locale: Locale;
};

function AdjacentCard({ label, item, locale }: AdjacentCardProps): React.ReactElement {
  const href = `/dev-blog/${encodeURIComponent(item.slug)}`;
  const prefetchHandlers = usePrefetchLink(href);
  const formatted = formatDate(item.publishAt, locale);
  return (
    <Card className="flex flex-col gap-2 border border-gray-200 p-4 transition-shadow hover:shadow-md dark:border-dark-600">
      <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-200">{label}</p>
      <Link to={href} className="text-lg font-semibold text-gray-900 hover:text-primary-600 dark:text-white" {...prefetchHandlers}>
        {item.title ?? (UNTITLED_POST[locale] ?? UNTITLED_POST.ru)}
      </Link>
      {formatted && <p className="text-xs text-gray-500 dark:text-dark-200">{formatted}</p>}
    </Card>
  );
}

type PlaceholderCardProps = {
  text: string;
};

function PlaceholderCard({ text }: PlaceholderCardProps): React.ReactElement {
  return (
    <Card className="border border-dashed border-gray-300 p-4 text-sm text-gray-500 dark:border-dark-500 dark:text-dark-200">
      {text}
    </Card>
  );
}

function DevBlogPostSkeleton(): React.ReactElement {
  return (
    <div className="space-y-6">
      <Skeleton className="h-6 w-32 rounded" />
      <Skeleton className="h-12 w-full rounded" />
      <Skeleton className="h-5 w-48 rounded" />
      <Skeleton className="h-80 w-full rounded-2xl" />
      <div className="space-y-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-4 w-full rounded" />
        ))}
      </div>
    </div>
  );
}




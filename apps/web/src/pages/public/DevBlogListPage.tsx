import React from 'react';
import { Helmet } from 'react-helmet-async';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import dayjs from 'dayjs';
import 'dayjs/locale/en';
import 'dayjs/locale/ru';
import { Button, Card, Skeleton, Tag, Input } from '@ui';
import { DEV_BLOG_PAGE_SIZE, buildDevBlogListKey, type DevBlogListKeyFilters } from './DevBlogListPage.shared';
import { fetchDevBlogList } from '@shared/api/devBlog';
import type { DevBlogListResponse, DevBlogSummary } from '@shared/types/devBlog';
import { useInitialData } from '@shared/ssr/InitialDataContext';
import { resolveSiteOrigin, buildCanonicalUrl, ensureAbsoluteUrl } from '@shared/seo';
import { usePrefetchLink } from '@shared/hooks/usePrefetchLink';
import { useLocale } from '@shared/i18n/locale';
import type { Locale } from '@shared/i18n/locale';


const DATE_FORMAT: Record<Locale, string> = {
  en: 'MMMM D, YYYY',
  ru: 'D MMMM YYYY',
};

const HEADER_TITLE: Record<Locale, string> = {
  en: 'Developer blog: news and updates',
  ru: 'Р”РµРІ-Р±Р»РѕРі: РЅРѕРІРѕСЃС‚Рё Рё РѕР±РЅРѕРІР»РµРЅРёСЏ',
};

const HEADER_SUBTITLE: Record<Locale, string> = {
  en: 'Follow milestones, release notes, and behind-the-scenes updates from the Caves team.',
  ru: 'РЎР»РµРґРёС‚Рµ Р·Р° РІР°Р¶РЅС‹РјРё СЂРµР»РёР·Р°РјРё, Р·Р°РјРµС‚РєР°РјРё Рё Р±СЌРєСЃС‚РµР№РґР¶РµРј РєРѕРјР°РЅРґС‹ Caves.',
};

const FILTERS_TITLE: Record<Locale, string> = {
  en: 'Filters',
  ru: 'Р¤РёР»СЊС‚СЂС‹',
};

const TAGS_LABEL: Record<Locale, string> = {
  en: 'Tags',
  ru: 'РўРµРіРё',
};

const NO_TAGS_HINT: Record<Locale, string> = {
  en: 'Tags will appear once more posts are published.',
  ru: 'РўРµРіРё РїРѕСЏРІСЏС‚СЃСЏ, РєРѕРіРґР° РїРѕСЏРІСЏС‚СЃСЏ РЅРѕРІС‹Рµ РїСѓР±Р»РёРєР°С†РёРё.',
};

const DATE_FROM_LABEL: Record<Locale, string> = {
  en: 'From date',
  ru: 'РЎ РґР°С‚С‹',
};

const DATE_TO_LABEL: Record<Locale, string> = {
  en: 'To date',
  ru: 'РџРѕ РґР°С‚Сѓ',
};

const RESET_FILTERS_LABEL: Record<Locale, string> = {
  en: 'Reset filters',
  ru: 'РЎР±СЂРѕСЃРёС‚СЊ С„РёР»СЊС‚СЂС‹',
};

const PAGINATION_PREV: Record<Locale, string> = {
  en: 'Previous',
  ru: 'РќР°Р·Р°Рґ',
};

const PAGINATION_NEXT: Record<Locale, string> = {
  en: 'Next',
  ru: 'Р’РїРµСЂС‘Рґ',
};

const PAGINATION_INFO: Record<Locale, string> = {
  en: 'Page {{page}} of {{total}}',
  ru: 'РЎС‚СЂР°РЅРёС†Р° {{page}} РёР· {{total}}',
};

const ERROR_PREFIX: Record<Locale, string> = {
  en: 'Failed to load posts:',
  ru: 'РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ РїРѕСЃС‚С‹:',
};

const EMPTY_STATE: Record<Locale, string> = {
  en: 'No posts match the selected filters. Try adjusting the filters or come back later.',
  ru: 'РџРѕ РІС‹Р±СЂР°РЅРЅС‹Рј С„РёР»СЊС‚СЂР°Рј РїРѕСЃС‚РѕРІ РЅРµ РЅР°Р№РґРµРЅРѕ. РџРѕРїСЂРѕР±СѓР№С‚Рµ РёР·РјРµРЅРёС‚СЊ С„РёР»СЊС‚СЂС‹ РёР»Рё Р·Р°РіР»СЏРЅРёС‚Рµ РїРѕР·Р¶Рµ.',
};

const READ_MORE: Record<Locale, string> = {
  en: 'Read more',
  ru: 'Р§РёС‚Р°С‚СЊ РґР°Р»РµРµ',
};

const UNTITLED_POST: Record<Locale, string> = {
  en: 'Untitled',
  ru: 'Р‘РµР· РЅР°Р·РІР°РЅРёСЏ',
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

type ListState = {
  loading: boolean;
  error: string | null;
  data: DevBlogListResponse | null;
};

function createInitialState(initialData: DevBlogListResponse | undefined): ListState {
  if (initialData) {
    return { loading: false, error: null, data: initialData };
  }
  return { loading: true, error: null, data: null };
}


function formatDate(value: string | null | undefined, locale: Locale): string | null {
  if (!value) return null;
  const parsed = dayjs(value);
  if (!parsed.isValid()) return null;
  return parsed.locale(locale).format(DATE_FORMAT[locale] ?? DATE_FORMAT.en);
}

function applyTemplate(template: Record<Locale, string>, locale: Locale, vars: Record<string, string>): string {
  const raw = template[locale] ?? template.ru;
  return raw.replace(/{{\s*(\w+)\s*}}/g, (_match, key) => vars[key] ?? '');
}

export default function DevBlogListPage(): React.ReactElement {
  const locale = useLocale();
  const location = useLocation();
  const [params, setParams] = useSearchParams();

  const pageParam = Number(params.get('page') || '1');
  const page = Number.isFinite(pageParam) && pageParam > 0 ? Math.floor(pageParam) : 1;

  const selectedTags = React.useMemo(() => {
    const raw = params
      .getAll('tag')
      .map((tag) => tag.trim())
      .filter((tag) => tag.length > 0);
    return Array.from(new Set(raw));
  }, [params]);
  const fromParam = params.get('from')?.trim() || undefined;
  const toParam = params.get('to')?.trim() || undefined;

  const filters = React.useMemo<DevBlogListKeyFilters>(
    () => ({ tags: selectedTags, from: fromParam, to: toParam }),
    [selectedTags, fromParam, toParam],
  );

  const cacheKey = React.useMemo(() => buildDevBlogListKey(page, filters), [page, filters]);
  const cached = useInitialData<DevBlogListResponse>(cacheKey);
  const [state, setState] = React.useState<ListState>(() => createInitialState(cached));
  const { loading, error, data } = state;
  const origin = React.useMemo(() => resolveSiteOrigin(), []);
  const canonical = React.useMemo(
    () => buildCanonicalUrl(`${location.pathname}${location.search}`, origin),
    [location.pathname, location.search, origin],
  );
  const ogImage = React.useMemo(() => {
    const cover = data?.items?.find((item) => item.coverUrl)?.coverUrl ?? undefined;
    return ensureAbsoluteUrl(cover ?? undefined, origin);
  }, [data, origin]);
  const alternates = React.useMemo(
    () => [
      { hreflang: locale, href: canonical },
      { hreflang: 'x-default', href: canonical },
    ],
    [canonical, locale],
  );
  const ogLocale = OG_LOCALE_MAP[locale] ?? OG_LOCALE_MAP.ru;


  React.useEffect(() => {
    let active = true;
    if (cached) {
      setState({ loading: false, error: null, data: cached });
      return () => {
        active = false;
      };
    }
    setState((prev) => ({ ...prev, loading: true, error: null }));
    (async () => {
      const { data: result, error: err } = await fetchDevBlogList({
        page,
        limit: DEV_BLOG_PAGE_SIZE,
        tags: filters.tags,
        publishedFrom: filters.from,
        publishedTo: filters.to,
      });
      if (!active) return;
      if (err) {
        setState({ loading: false, error: err, data: null });
      } else {
        setState({ loading: false, error: null, data: result });
      }
    })();
    return () => {
      active = false;
    };
  }, [page, filters, cached]);

  const handleNavigate = React.useCallback(
    (nextPage: number) => {
      const target = nextPage < 1 ? 1 : nextPage;
      const next = new URLSearchParams(params);
      if (target === 1) {
        next.delete('page');
      } else {
        next.set('page', String(target));
      }
      setParams(next, { replace: true });
    },
    [params, setParams],
  );

  const handleTagToggle = React.useCallback(
    (tag: string) => {
      const normalized = tag.trim();
      if (!normalized) return;
      const next = new URLSearchParams(params);
      const existing = new Set(
        next
          .getAll('tag')
          .map((value) => value.trim())
          .filter((value) => value.length > 0),
      );
      if (existing.has(normalized)) {
        existing.delete(normalized);
      } else {
        existing.add(normalized);
      }
      next.delete('tag');
      Array.from(existing)
        .sort()
        .forEach((value) => next.append('tag', value));
      next.delete('page');
      setParams(next, { replace: true });
    },
    [params, setParams],
  );

  const handleDateChange = React.useCallback(
    (field: 'from' | 'to', value: string) => {
      const next = new URLSearchParams(params);
      if (value) {
        next.set(field === 'from' ? 'from' : 'to', value);
      } else {
        next.delete(field === 'from' ? 'from' : 'to');
      }
      next.delete('page');
      setParams(next, { replace: true });
    },
    [params, setParams],
  );

  const handleResetFilters = React.useCallback(() => {
    if (filters.tags.length === 0 && !filters.from && !filters.to) {
      return;
    }
    const next = new URLSearchParams(params);
    next.delete('tag');
    next.delete('from');
    next.delete('to');
    next.delete('page');
    setParams(next, { replace: true });
  }, [filters, params, setParams]);

  const availableTags = React.useMemo<string[]>(() => data?.availableTags ?? [], [data?.availableTags]);
  const totalPages = data ? Math.max(1, Math.ceil(data.total / DEV_BLOG_PAGE_SIZE)) : 1;
  const headTitle = filters.tags.length
    ? `${HEADER_TITLE[locale] ?? HEADER_TITLE.ru} вЂ” ${filters.tags.map((tag) => `#${tag}`).join(', ')}`
    : HEADER_TITLE[locale] ?? HEADER_TITLE.ru;
  const metaDescription = SHARE_DESCRIPTION[locale] ?? SHARE_DESCRIPTION.ru;
  const isEmpty = !loading && !error && data != null && data.items.length === 0;

  return (
    <main className="mx-auto max-w-5xl px-4 pb-16 pt-12 lg:px-0">
      <Helmet>
        <title>{headTitle}</title>
        <meta name="description" content={metaDescription} />
        <link rel="canonical" href={canonical} />
        <meta property="og:type" content="website" />
        <meta property="og:title" content={headTitle} />
        <meta property="og:description" content={metaDescription} />
        <meta property="og:url" content={canonical} />
        <meta property="og:locale" content={ogLocale} />
        <meta property="og:site_name" content={SITE_NAME} />
        {ogImage && <meta property="og:image" content={ogImage} />}
        <meta name="twitter:card" content={TWITTER_CARD} />
        <meta name="twitter:title" content={headTitle} />
        <meta name="twitter:description" content={metaDescription} />
        {ogImage && <meta name="twitter:image" content={ogImage} />}
        {alternates.map((item) => (
          <link key={item.hreflang} rel="alternate" hrefLang={item.hreflang} href={item.href} />
        ))}
      </Helmet>

      <header className="mb-12 space-y-3 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-primary-600 dark:text-primary-300">Dev Blog</p>
        <h1 className="text-4xl font-semibold text-gray-900 dark:text-white">{HEADER_TITLE[locale] ?? HEADER_TITLE.ru}</h1>
        <p className="text-sm text-gray-600 dark:text-dark-100">{HEADER_SUBTITLE[locale] ?? HEADER_SUBTITLE.ru}</p>
      </header>

      <section className="mb-10 space-y-4 rounded-2xl border border-gray-200 bg-white/70 p-6 shadow-sm dark:border-dark-600 dark:bg-dark-800/60">
        <h2 className="text-xs font-semibold uppercase tracking-[0.3em] text-gray-500 dark:text-dark-200">{FILTERS_TITLE[locale] ?? FILTERS_TITLE.ru}</h2>
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-[12rem] flex-1">
            <p className="text-sm font-medium text-gray-700 dark:text-dark-100">{TAGS_LABEL[locale] ?? TAGS_LABEL.ru}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {availableTags.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-dark-300">{NO_TAGS_HINT[locale] ?? NO_TAGS_HINT.ru}</p>
              ) : (
                availableTags.map((tag) => {
                  const active = filters.tags.includes(tag);
                  return (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => handleTagToggle(tag)}
                      className="transition hover:-translate-y-[1px] focus:outline-none"
                    >
                      <Tag color={active ? 'primary' : 'gray'} className="cursor-pointer">
                        #{tag}
                      </Tag>
                    </button>
                  );
                })
              )}
            </div>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <Input
              type="date"
              label={DATE_FROM_LABEL[locale] ?? DATE_FROM_LABEL.ru}
              value={filters.from ?? ''}
              onChange={(event) => handleDateChange('from', event.target.value)}
            />
            <Input
              type="date"
              label={DATE_TO_LABEL[locale] ?? DATE_TO_LABEL.ru}
              value={filters.to ?? ''}
              min={filters.from ?? undefined}
              onChange={(event) => handleDateChange('to', event.target.value)}
            />
            <Button
              variant="ghost"
              color="neutral"
              onClick={handleResetFilters}
              disabled={filters.tags.length === 0 && !filters.from && !filters.to}
            >
              {RESET_FILTERS_LABEL[locale] ?? RESET_FILTERS_LABEL.ru}
            </Button>
          </div>
        </div>
      </section>

      {loading && <DevBlogListSkeleton />}

      {!loading && error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-sm text-red-700 dark:border-red-700 dark:bg-red-900/40 dark:text-red-200">
          {(ERROR_PREFIX[locale] ?? ERROR_PREFIX.ru) + ' ' + error}
        </div>
      )}

      {isEmpty && (
        <div className="rounded-xl border border-gray-200 bg-white/80 p-8 text-center text-sm text-gray-600 dark:border-dark-600 dark:bg-dark-800/60 dark:text-dark-100">
          {EMPTY_STATE[locale] ?? EMPTY_STATE.ru}
        </div>
      )}

      {!loading && !error && data && data.items.length > 0 && (
        <div className="space-y-10">
          <div className="grid gap-6 md:grid-cols-2">
            {data.items.map((item) => (
              <DevBlogListCard key={`${item.slug}-${item.id ?? ''}`} item={item} locale={locale} />
            ))}
          </div>

          <div className="flex flex-col gap-4 rounded-xl border border-gray-200 p-4 text-sm text-gray-600 dark:border-dark-600 dark:text-dark-200 sm:flex-row sm:items-center sm:justify-between">
            <Button variant="outlined" color="neutral" disabled={page <= 1} onClick={() => handleNavigate(page - 1)}>
              {PAGINATION_PREV[locale] ?? PAGINATION_PREV.ru}
            </Button>
            <p>
              {applyTemplate(PAGINATION_INFO, locale, {
                page: String(page),
                total: String(totalPages),
              })}
            </p>
            <Button variant="outlined" color="neutral" disabled={!data.hasNext} onClick={() => handleNavigate(page + 1)}>
              {PAGINATION_NEXT[locale] ?? PAGINATION_NEXT.ru}
            </Button>
          </div>
        </div>
      )}
    </main>
  );
}

type DevBlogListCardProps = {
  item: DevBlogSummary;
  locale: Locale;
};

function DevBlogListCard({ item, locale }: DevBlogListCardProps): React.ReactElement {
  const href = `/dev-blog/${encodeURIComponent(item.slug)}`;
  const prefetchHandlers = usePrefetchLink(href);
  const formattedDate = formatDate(item.publishAt, locale);
  const tags = Array.isArray(item.tags) ? item.tags : [];
  return (
    <Card className="flex h-full flex-col overflow-hidden border border-gray-200 shadow-sm transition-shadow hover:shadow-md dark:border-dark-600">
      {item.coverUrl && (
        <Link to={href} className="block" {...prefetchHandlers}>
          <img
            src={item.coverUrl}
            alt={item.title ?? ''}
            loading="lazy"
            decoding="async"
            className="h-48 w-full object-cover"
          />
        </Link>
      )}
      <div className="flex flex-1 flex-col gap-4 p-6">
        <div className="space-y-2">
          <Link to={href} className="text-xl font-semibold text-gray-900 hover:text-primary-600 dark:text-white" {...prefetchHandlers}>
            {item.title ?? (UNTITLED_POST[locale] ?? UNTITLED_POST.ru)}
          </Link>
          {formattedDate && <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-200">{formattedDate}</p>}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <Tag key={tag} color="gray">
                  #{tag}
                </Tag>
              ))}
            </div>
          )}
        </div>
        {item.summary && <p className="flex-1 text-sm text-gray-600 dark:text-dark-100">{item.summary}</p>}
        <div className="mt-auto text-sm font-medium text-primary-600 hover:text-primary-500">
          <Link to={href} {...prefetchHandlers}>{READ_MORE[locale] ?? READ_MORE.ru}</Link>
        </div>
      </div>
    </Card>
  );
}

function DevBlogListSkeleton(): React.ReactElement {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {Array.from({ length: 4 }).map((_, idx) => (
        <Skeleton key={idx} className="h-64 rounded-xl" />
      ))}
    </div>
  );
}







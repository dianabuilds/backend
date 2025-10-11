import React from 'react';
import { Link } from 'react-router-dom';
import type { HomeBlockItem } from '@shared/types/homePublic';
import { usePrefetchLink } from '@shared/hooks/usePrefetchLink';
import { Card } from '@ui';
import type { HomeBlockComponentProps } from './types';
import { formatDate, getItems, resolveLimit } from './blockUtils';

const DEFAULT_DEV_BLOG_LIMIT = 3;

type DevBlogCardProps = {
  item: HomeBlockItem;
};

function DevBlogCard({ item }: DevBlogCardProps): React.ReactElement {
  const slug = typeof item.slug === 'string' ? item.slug : null;
  const href = slug ? `/dev-blog/${encodeURIComponent(slug)}` : '#';
  const prefetchHref = slug ? href : null;
  const prefetchHandlers = usePrefetchLink(prefetchHref);
  const formattedDate = formatDate(item.publishAt);

  return (
    <Card className="flex h-full flex-col overflow-hidden border border-gray-200 shadow-sm transition-shadow hover:shadow-md dark:border-dark-600">
      {item.coverUrl && (
        <Link to={href} className="block" {...prefetchHandlers}>
          <img
            src={item.coverUrl}
            alt={item.title ?? ''}
            loading="lazy"
            decoding="async"
            className="h-40 w-full object-cover"
          />
        </Link>
      )}
      <div className="flex flex-1 flex-col gap-3 p-5">
        <div className="space-y-2">
          <Link to={href} className="text-lg font-semibold text-gray-900 hover:text-primary-600 dark:text-white" {...prefetchHandlers}>
            {item.title ?? 'Без названия'}
          </Link>
          {formattedDate && <p className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-200">{formattedDate}</p>}
        </div>
        {item.summary && <p className="flex-1 text-sm text-gray-600 dark:text-dark-100">{item.summary}</p>}
        <div className="mt-auto text-sm text-primary-600 hover:text-primary-500">
          <Link to={href} {...prefetchHandlers}>читать далее</Link>
        </div>
      </div>
    </Card>
  );
}

export default function DevBlogListBlock({ block }: HomeBlockComponentProps): React.ReactElement {
  const items = getItems(block);
  const limit = resolveLimit(block, items.length || DEFAULT_DEV_BLOG_LIMIT);
  const visibleItems = items.slice(0, limit);
  const listPrefetch = usePrefetchLink('/dev-blog');

  return (
    <section>
      <header className="mb-6 flex items-end justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary-600 dark:text-primary-300">Dev Blog</p>
          <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">{block.title ?? 'Новости разработки'}</h2>
        </div>
        <Link to="/dev-blog" className="text-sm font-medium text-primary-600 hover:text-primary-500" {...listPrefetch}>
          все записи
        </Link>
      </header>
      {visibleItems.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500 dark:border-dark-500 dark:text-dark-200">
          Пока нет записей для отображения.
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {visibleItems.map((item) => (
            <DevBlogCard key={`${block.id}-${item.slug ?? item.id ?? Math.random()}`} item={item} />
          ))}
        </div>
      )}
    </section>
  );
}

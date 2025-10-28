import React from 'react';
import { Link } from 'react-router-dom';
import type { HomeBlockItem } from '@shared/types/homePublic';
import { usePrefetchLink } from '@shared/hooks/usePrefetchLink';
import { Card } from '@ui';
import type { HomeBlockComponentProps } from './types';
import { getItems, readStringSlot } from './blockUtils';

type ItemsGridCardProps = {
  blockType: string;
  item: HomeBlockItem;
};

function ItemsGridCard({ blockType, item }: ItemsGridCardProps): React.ReactElement {
  const href = typeof item.slug === 'string' ? `/n/${encodeURIComponent(String(item.slug))}` : null;
  const prefetchHandlers = usePrefetchLink(href);

  return (
    <Card className="flex flex-col gap-2 border border-gray-200 p-4 dark:border-dark-600">
      <p className="text-sm uppercase tracking-wide text-gray-500 dark:text-dark-200">{blockType}</p>
      <p className="text-lg font-semibold text-gray-900 dark:text-white">{item.title ?? 'Без названия'}</p>
      {item.summary && <p className="text-sm text-gray-600 dark:text-dark-100">{item.summary}</p>}
      {href && (
        <Link to={href} className="text-sm font-medium text-primary-600 hover:text-primary-500" {...prefetchHandlers}>
          перейти
        </Link>
      )}
    </Card>
  );
}

export default function ItemsGridBlock({ block }: HomeBlockComponentProps): React.ReactElement {
  const items = getItems(block);
  const title = block.title ?? block.type;
  const description = readStringSlot(block.slots ?? null, 'description');

  return (
    <section>
      <header className="mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h2>
        {description && <p className="text-sm text-gray-500 dark:text-dark-200">{description}</p>}
      </header>
      {items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 p-6 text-center text-sm text-gray-500 dark:border-dark-500 dark:text-dark-200">
          Для этого раздела пока нет материалов.
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((item) => (
            <ItemsGridCard key={`${block.id}-${item.slug ?? item.id ?? Math.random()}`} blockType={block.type} item={item} />
          ))}
        </div>
      )}
    </section>
  );
}

import React from 'react';
import { rumEvent } from '@shared/rum';
import HeroBlock from './blocks/HeroBlock';
import { BlockPlaceholder } from './blocks/BlockPlaceholder';
import type { HomeBlockComponentProps } from './blocks/types';

export type BlockRendererProps = HomeBlockComponentProps;

type BlockComponent = React.ComponentType<HomeBlockComponentProps>;
type LazyBlockComponent = React.LazyExoticComponent<BlockComponent>;
type BlockComponentLike = BlockComponent | LazyBlockComponent;

type BlockRegistry = Record<string, BlockComponentLike>;

function lazyBlock(loader: () => Promise<{ default: BlockComponent }>): LazyBlockComponent {
  return React.lazy(loader);
}

const DevBlogListBlockLazy = lazyBlock(() => import('./blocks/DevBlogListBlock'));
const ItemsGridBlockLazy = lazyBlock(() => import('./blocks/ItemsGridBlock'));

const BLOCK_REGISTRY: BlockRegistry = {
  hero: HeroBlock,
  dev_blog_list: DevBlogListBlockLazy,
  quests_carousel: ItemsGridBlockLazy,
  nodes_carousel: ItemsGridBlockLazy,
  popular_carousel: ItemsGridBlockLazy,
  editorial_picks: ItemsGridBlockLazy,
  recommendations: ItemsGridBlockLazy,
  custom_carousel: ItemsGridBlockLazy,
};

function UnknownBlock({ block }: HomeBlockComponentProps): React.ReactElement {
  return (
    <section className="rounded-xl border border-dashed border-gray-300 p-6 text-sm text-gray-500 dark:border-dark-500 dark:text-dark-200">
      Блок типа <span className="font-mono">{block.type}</span> пока не поддерживается на клиенте.
    </section>
  );
}

export function BlockRenderer({ block, position }: BlockRendererProps): React.ReactElement | null {
  const Component = BLOCK_REGISTRY[block.type] ?? UnknownBlock;
  const trackedKeyRef = React.useRef<string | null>(null);

  React.useEffect(() => {
    if (block.enabled === false) return;
    const trackKey = `${block.id}:${position}`;
    if (trackedKeyRef.current === trackKey) return;
    trackedKeyRef.current = trackKey;
    rumEvent('home.block_rendered', {
      type: block.type,
      position,
    });
  }, [block.id, block.type, block.enabled, position]);

  if (block.enabled === false) {
    return null;
  }

  return (
    <React.Suspense fallback={<BlockPlaceholder block={block} />}>
      <Component block={block} position={position} />
    </React.Suspense>
  );
}

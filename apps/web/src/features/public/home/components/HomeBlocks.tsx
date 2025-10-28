import React from 'react';
import type { HomeBlockPayload } from '@shared/types/homePublic';
import { Skeleton } from '@ui';
import { BlockRenderer } from './BlockRenderer';

type HomeBlocksProps = {
  blocks: HomeBlockPayload[];
};

export function HomeBlocks({ blocks }: HomeBlocksProps): React.ReactElement {
  const visibleBlocks = React.useMemo(() => blocks.filter((block) => block && block.enabled !== false), [blocks]);

  if (!visibleBlocks.length) {
    return (
      <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500 dark:border-dark-500 dark:text-dark-200">
        Конфигурация не содержит активных блоков.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-12">
      {visibleBlocks.map((block, index) => (
        <BlockRenderer key={block.id} block={block} position={index + 1} />
      ))}
    </div>
  );
}

export function HomeBlocksSkeleton(): React.ReactElement {
  return (
    <div className="flex flex-col gap-12">
      <Skeleton className="h-64 rounded-3xl" />
      <div className="space-y-4">
        <Skeleton className="h-6 w-48 rounded" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-48 rounded-xl" />
          ))}
        </div>
      </div>
    </div>
  );
}

export { BlockRenderer };

import React from 'react';
import type { HomeBlockPayload } from '@shared/types/homePublic';

type BlockPlaceholderProps = {
  block: HomeBlockPayload;
};

export function BlockPlaceholder({ block }: BlockPlaceholderProps): React.ReactElement {
  const title = typeof block.title === 'string' && block.title.trim().length > 0 ? block.title : block.type;

  return (
    <section className="rounded-3xl border border-gray-200 bg-white/70 p-8 text-sm text-gray-500 dark:border-dark-600 dark:bg-dark-800/70 dark:text-dark-200">
      <div className="space-y-2">
        <p className="text-base font-medium text-gray-700 dark:text-dark-100">{title}</p>
        <p className="text-xs text-gray-500 dark:text-dark-300">Загружаем содержимое блока...</p>
      </div>
    </section>
  );
}

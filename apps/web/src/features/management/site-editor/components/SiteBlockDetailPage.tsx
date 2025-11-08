import React from 'react';
import { Link } from 'react-router-dom';
import { Button, Card } from '@ui';
import type { SiteBlock } from '@shared/types/management';
import SiteBlockDetailPanel from './SiteBlockDetailPanel';

type Props = {
  blockId?: string;
};

export default function SiteBlockDetailPage({
  blockId: propBlockId,
}: Props): React.ReactElement {
  const [currentBlock, setCurrentBlock] = React.useState<SiteBlock | null>(null);

  const blockId = propBlockId ?? null;

  if (!blockId) {
    return (
      <Card className="border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-400/50 dark:bg-rose-500/10 dark:text-rose-100">
        Не указан идентификатор блока. Вернитесь в библиотеку и повторите попытку.
      </Card>
    );
  }

  return (
    <div className="space-y-4 pb-12">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Button as={Link} to="/management/site-editor?tab=blocks" variant="ghost" size="sm">
              ← К библиотеке
            </Button>
            <span className="text-xs text-gray-500 dark:text-dark-300">ID: {blockId}</span>
          </div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
            {currentBlock?.title || 'Блок'}
          </h1>
          <p className="text-sm text-gray-500 dark:text-dark-200">
            Настройте данные, локали и публикацию выбранного блока.
          </p>
        </div>
      </div>

      <SiteBlockDetailPanel
        blockId={blockId}
        onBlockMutated={(block) => {
          setCurrentBlock(block);
        }}
      />
    </div>
  );
}

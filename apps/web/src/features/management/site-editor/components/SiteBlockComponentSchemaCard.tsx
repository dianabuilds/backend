import React from 'react';
import { Badge, Card, Button } from '@ui';
import type { SiteBlock } from '@shared/types/management';

type Props = {
  block: SiteBlock;
  onViewSchema?: () => void;
  loading?: boolean;
  error?: string | null;
};

export function SiteBlockComponentSchemaCard({
  block,
  onViewSchema,
  loading,
  error,
}: Props): React.ReactElement | null {
  const schemaRef = block.component_schema;
  if (!schemaRef) {
    return null;
  }
  return (
    <Card className="flex h-full flex-col justify-between border border-gray-200/80 bg-white/95 p-4 shadow-sm">
      <div className="space-y-3">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-gray-400">Компонент</div>
          <div className="flex items-center gap-2">
            <span className="text-base font-semibold text-gray-900">{schemaRef.key}</span>
            <Badge color="neutral" variant="soft">
              v{schemaRef.version}
            </Badge>
          </div>
        </div>
        <p className="text-sm text-gray-600">
          Настройки и форма редактирования строятся по JSON Schema компонента. Изменения в библиотеке автоматически
          подтягиваются после обновления версии.
        </p>
        {error ? (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-100">
            {error}
          </div>
        ) : null}
      </div>
      <div className="flex items-center gap-2">
        <Button
          as="a"
          href={schemaRef.schema_url}
          target="_blank"
          rel="noopener noreferrer"
          size="sm"
          variant="ghost"
          color="neutral"
        >
          Открыть JSON
        </Button>
        {onViewSchema ? (
          <Button size="sm" variant="filled" color="primary" onClick={onViewSchema} disabled={loading}>
            {loading ? 'Загружаем…' : 'Показать в UI'}
          </Button>
        ) : null}
      </div>
    </Card>
  );
}

export default SiteBlockComponentSchemaCard;

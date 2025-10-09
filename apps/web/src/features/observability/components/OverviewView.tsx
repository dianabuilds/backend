import React from 'react';
import { Card, PageHeader } from '@ui';

export function ObservabilityOverview(): React.ReactElement {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Observability Overview"
        description="Глобальный обзор метрик будет восстановлен после переноса на новые хуки данных."
      />
      <Card className="p-6 text-sm text-gray-500 dark:text-gray-300">
        TODO: интегрировать общий observability API и визуализации.
      </Card>
    </div>
  );
}



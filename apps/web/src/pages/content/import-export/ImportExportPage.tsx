import React from 'react';
import { ContentLayout } from '../ContentLayout';
import { Card, Button } from '@ui';

export default function ImportExportPage() {
  return (
    <ContentLayout context="ops">
      <Card className="p-4 space-y-4">
        <h2 className="text-base font-medium text-gray-800 dark:text-dark-100">Импорт / Экспорт</h2>
        <p className="text-sm text-gray-500">Загрузите CSV/JSON для импорта нод, квестов и миров. Экспорт формирует архив JSON.</p>
        <div className="flex gap-2">
          <Button>Импорт CSV</Button>
          <Button variant="outlined">Импорт JSON</Button>
          <Button variant="outlined">Экспорт</Button>
        </div>
        <div className="rounded-md border border-gray-200 bg-gray-50 p-3 text-xs text-gray-600 dark:border-dark-600 dark:bg-dark-800">
          Форматы:
          <ul className="list-disc pl-5">
            <li>nodes.csv — id,title,world,status,updatedAt</li>
            <li>quests.csv — id,title,world,difficulty,status,updatedAt</li>
            <li>worlds.csv — id,name</li>
          </ul>
        </div>
      </Card>
    </ContentLayout>
  );
}

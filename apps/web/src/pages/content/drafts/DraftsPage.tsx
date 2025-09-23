import React from 'react';
import { ContentLayout } from '../ContentLayout';
import { Card } from '../../../shared/ui';
import { apiGet } from '../../../shared/api/client';

type Draft = { id: string; type: 'Нода'|'Квест'; title: string; world: string; updatedAt: string };

const mock: Draft[] = [
  { id: '1', type: 'Нода', title: 'Новая локация', world: 'Мир A', updatedAt: 'сегодня' },
  { id: '2', type: 'Квест', title: 'Собрать артефакт', world: 'Мир B', updatedAt: 'вчера' },
];

export default function DraftsPage() {
  const [items, setItems] = React.useState<Draft[]>(mock);

  React.useEffect(() => {
    (async () => {
      try {
        const data = await apiGet('/v1/content/drafts?limit=50');
        if (Array.isArray(data?.items)) setItems(data.items);
      } catch {}
    })();
  }, []);

  return (
    <ContentLayout context="ops">
      <Card className="p-4">
        <div className="text-sm text-gray-500">Всего: {items.length}</div>
        <div className="mt-4 overflow-x-auto">
          <table className="table is-hoverable is-zebra min-w-[640px]">
            <thead>
              <tr>
                <th className="text-left">ID</th>
                <th className="text-left">Тип</th>
                <th className="text-left">Название</th>
                <th className="text-left">Мир</th>
                <th className="text-left">Обновлено</th>
              </tr>
            </thead>
            <tbody>
              {items.map((d) => (
                <tr key={d.id}>
                  <td className="py-2">{d.id}</td>
                  <td className="py-2">{d.type}</td>
                  <td className="py-2">{d.title}</td>
                  <td className="py-2">{d.world}</td>
                  <td className="py-2">{d.updatedAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </ContentLayout>
  );
}

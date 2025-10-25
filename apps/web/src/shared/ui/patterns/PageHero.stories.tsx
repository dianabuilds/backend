import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { PageHero, type PageHeroMetric } from './PageHero';
import { Button } from '@ui/primitives/Button';

const meta: Meta<typeof PageHero> = {
  title: 'Patterns/PageHero',
  component: PageHero,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;

type Story = StoryObj<typeof PageHero>;

const metrics: PageHeroMetric[] = [
  {
    label: 'Активные узлы',
    value: '124',
    trend: '+12% неделя к неделе',
    accent: 'positive',
  },
  {
    label: 'На проверке',
    value: '32',
    trend: '4 нарушения SLA',
    accent: 'warning',
  },
  {
    label: 'Средний ответ',
    value: '2 мин 41 с',
    helper: 'Целевое значение — 3 минуты',
  },
  {
    label: 'Выручка за день',
    value: '?1.8M',
    trend: '+6.4%',
    accent: 'positive',
  },
];

const contentMetrics: PageHeroMetric[] = [
  {
    id: 'content-drafts',
    label: 'Drafts',
    value: '312',
    helper: 'Nodes + quests awaiting review',
  },
  {
    id: 'content-published',
    label: 'Published',
    value: '1 248',
    helper: 'Live objects across hubs',
  },
  {
    id: 'content-links',
    label: 'Avg links',
    value: '3.4',
    helper: 'Per content object',
  },
  {
    id: 'content-queued',
    label: 'Queued broadcasts',
    value: '28',
    helper: '8 scheduled / 20 sending',
  },
];

export const Default: Story = {
  args: {
    title: 'Сводка по узлам',
    description:
      'Следите за основными метриками выпуска контента, проверяйте состояние узлов и запускайте рутинные действия из одного места.',
    eyebrow: 'Operations',
    breadcrumbs: [
      { label: 'Dashboard', to: '/' },
      { label: 'Nodes' },
    ],
    actions: (
      <>
        <Button variant="ghost">Экспорт</Button>
        <Button>Создать узел</Button>
      </>
    ),
    filters: (
      <>
        <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-600 shadow-sm dark:border-dark-700 dark:bg-dark-800 dark:text-gray-100">
          Регион: EMEA
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-600 shadow-sm dark:border-dark-700 dark:bg-dark-800 dark:text-gray-100">
          Статус: Все
        </div>
      </>
    ),
    metrics,
  },
};

export const Metrics: Story = {
  args: {
    ...Default.args,
    variant: 'metrics',
    align: 'start',
    actions: (
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="ghost" size="sm">
          Обновить
        </Button>
        <Button size="sm">Настроить панели</Button>
      </div>
    ),
  },
};

export const ContentHub: Story = {
  args: {
    title: 'Content intelligence',
    description: 'Unify authoring signals for nodes, quests, and notifications. Keep the pipeline healthy from a single hub.',
    variant: 'metrics',
    metrics: contentMetrics,
    actions: (
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm">New node</Button>
        <Button size="sm" variant="outlined">
          Import / Export
        </Button>
        <Button size="sm" variant="ghost">
          Broadcast update
        </Button>
      </div>
    ),
    filters: (
      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" variant="ghost">
          Drafts
        </Button>
        <Button size="sm" variant="ghost">
          Published
        </Button>
        <Button size="sm" variant="ghost">
          Notifications
        </Button>
      </div>
    ),
  },
};

export const Compact: Story = {
  args: {
    title: 'Очередь модерации',
    description: 'Вся входящая нагрузка по жалобам и автофлагам собрана в одном месте.',
    variant: 'compact',
    align: 'start',
    actions: <Button size="sm">Назначить оператора</Button>,
    metrics: metrics.slice(0, 2),
  },
};

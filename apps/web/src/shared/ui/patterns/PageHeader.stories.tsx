import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { PageHeader } from './PageHeader';
import { Button } from '@ui';

const meta: Meta<typeof PageHeader> = {
  title: 'Patterns/PageHeader',
  component: PageHeader,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;

type Story = StoryObj<typeof PageHeader>;

export const Highlight: Story = {
  args: {
    title: 'Управление платформой',
    description: 'Настройка тарифов, интеграций и сервисных компонент. Из этого раздела начинается ежедневная работа администраторов.',
    kicker: 'Control center',
    breadcrumbs: [
      { label: 'Dashboard', to: '/' },
      { label: 'Platform' },
    ],
    actions: (
      <div className="flex items-center gap-2">
        <Button variant="ghost">Экспорт</Button>
        <Button>Добавить запись</Button>
      </div>
    ),
    stats: [
      { label: 'Активные интеграции', value: '18', hint: 'из 22 доступных' },
      { label: 'Ошибки за сутки', value: '3', hint: 'разрешено 5' },
    ],
  },
};

export const Radiant: Story = {
  args: {
    ...Highlight.args,
    pattern: 'radiant',
    title: 'Observability',
    description: 'Мониторинг производительности API и клиентских приложений.',
    stats: [
      { label: 'Время отклика', value: '142 мс' },
      { label: 'Ошибки 5xx', value: '0.3%' },
      { label: 'LLM запросы', value: '12 480' },
    ],
  },
};


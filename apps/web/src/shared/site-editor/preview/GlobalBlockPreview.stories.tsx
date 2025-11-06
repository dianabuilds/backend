import type { Meta, StoryObj } from '@storybook/react';
import { GlobalBlockPreview } from './GlobalBlockPreview';

const meta: Meta<typeof GlobalBlockPreview> = {
  title: 'Site Editor/Preview/GlobalBlockPreview',
  component: GlobalBlockPreview,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;

type Story = StoryObj<typeof GlobalBlockPreview>;

const sampleItems = [
  {
    id: 'analytics',
    title: 'Отчёт по аналитике',
    subtitle: 'Пользовательское поведение и основные метрики',
    href: '/analytics/report',
    provider: 'Metabase',
    score: 0.87,
  },
  {
    id: 'support',
    title: 'Центр поддержки',
    subtitle: 'Онлайн-чат и база знаний',
    href: '/help',
    provider: 'Zendesk',
    score: 0.72,
  },
];

export const Default: Story = {
  args: {
    items: sampleItems,
    source: 'preview/v1',
    fetchedAt: new Date().toISOString(),
  },
};

export const EmptyState: Story = {
  args: {
    items: [],
    source: 'preview/v1',
    fetchedAt: new Date().toISOString(),
  },
};

export const WithCustomEmptyMessage: Story = {
  args: {
    items: [],
    source: 'preview/cache',
    fetchedAt: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    emptyMessage: 'Предпросмотр ещё не готов — обновите данные или проверьте источники.',
  },
};

import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { MemoryRouter } from 'react-router-dom';
import { HomeBlocks } from './HomeBlocks';
import type { HomeBlockItem, HomeBlockPayload } from '@shared/types/homePublic';

const meta: Meta<typeof HomeBlocks> = {
  title: 'Pages/Public/HomeBlocks',
  component: HomeBlocks,
  parameters: {
    layout: 'fullscreen',
  },
  decorators: [
    (Story) => (
      <MemoryRouter>
        <div className="mx-auto max-w-6xl p-8">
          <Story />
        </div>
      </MemoryRouter>
    ),
  ],
};

export default meta;

type Story = StoryObj<typeof HomeBlocks>;

const devBlogItems: HomeBlockItem[] = [
  {
    id: 'dev-1',
    slug: 'editor-refresh',
    title: 'Новая версия редактора',
    summary: 'Рассказываем про свежие улучшения редактора статей и предпросмотров.',
    coverUrl: 'https://picsum.photos/seed/editor/640/360',
    publishAt: '2025-10-01T10:00:00Z',
  },
  {
    id: 'dev-2',
    slug: 'api-metrics',
    title: 'Метрики API: что изменилось',
    summary: 'Поделились деталями новой системы мониторинга API и метрик доступности.',
    coverUrl: 'https://picsum.photos/seed/api/640/360',
    publishAt: '2025-10-05T12:00:00Z',
  },
  {
    id: 'dev-3',
    slug: 'components-kit',
    title: 'Обновление дизайн-системы',
    summary: 'Представили свежие компоненты и токены для платформенных продуктов.',
    coverUrl: 'https://picsum.photos/seed/design/640/360',
    publishAt: '2025-10-07T14:30:00Z',
  },
];

const carouselItems: HomeBlockItem[] = [
  {
    id: 'quest-1',
    slug: 'labyrinth',
    title: 'Лабиринты света',
    summary: 'Серия коротких квестов о работе со световыми узлами.',
  },
  {
    id: 'quest-2',
    slug: 'echoes',
    title: 'Эхо уходящих звуков',
    summary: 'Исследуем акустические эффекты и создаём аудиальные сцены.',
  },
  {
    id: 'quest-3',
    slug: 'forge',
    title: 'Кузница идей',
    summary: 'Пошаговый разбор конструктора для собственных миров.',
  },
];

function createHeroBlock(): HomeBlockPayload {
  return {
    id: 'hero-block',
    type: 'hero',
    title: 'Главный блок',
    enabled: true,
    slots: {
      headline: 'Создаём новые миры вместе',
      subheadline: 'Редакция собирает лучшие истории недели и делится планами на будущие обновления.',
      cta: { label: 'Перейти к квестам', href: '/quests' },
      media: 'https://picsum.photos/seed/hero/960/540',
    },
    layout: null,
    items: [],
    dataSource: null,
  };
}

function createDevBlogBlock(): HomeBlockPayload {
  return {
    id: 'dev-blog-block',
    type: 'dev_blog_list',
    title: 'Dev Blog',
    enabled: true,
    slots: null,
    layout: null,
    items: devBlogItems,
    dataSource: {
      mode: 'auto',
      entity: 'dev_blog',
      filter: { limit: 3 },
      items: null,
    },
  };
}

function createCarouselBlock(type: HomeBlockPayload['type']): HomeBlockPayload {
  return {
    id: `${type}-block`,
    type,
    title: 'Выбор редакции',
    enabled: true,
    slots: { description: 'Подборка материалов, которые стоит пройти в первую очередь.' },
    layout: null,
    items: carouselItems,
    dataSource: {
      mode: 'manual',
      entity: 'quest',
      items: ['quest-1', 'quest-2', 'quest-3'],
      filter: null,
    },
  };
}

export const Hero: Story = {
  args: {
    blocks: [createHeroBlock()],
  },
};

export const DevBlogList: Story = {
  args: {
    blocks: [createDevBlogBlock()],
  },
};

export const MixedLayout: Story = {
  args: {
    blocks: [createHeroBlock(), createDevBlogBlock(), createCarouselBlock('editorial_picks')],
  },
};

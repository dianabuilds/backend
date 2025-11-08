import type { HomeBlock, HomeBlockType } from './types';

export type BlockDefinition = {
  type: HomeBlockType;
  label: string;
  description: string;
  create: (input: { id: string; existing: HomeBlock[] }) => HomeBlock;
};

const DEFINITIONS: BlockDefinition[] = [
  {
    type: 'hero',
    label: 'Hero-блок',
    description: 'Большой первый экран с заголовком и CTA.',
    create: ({ id }) => ({
      id,
      type: 'hero',
      enabled: true,
      title: 'Hero',
      slots: {
        headline: 'Заголовок для hero',
        subheadline: 'Краткое описание главного предложения.',
        cta: { label: 'Подробнее', href: '/' },
        media: null,
      },
      layout: { variant: 'full' },
      source: 'manual',
    }),
  },
  {
    type: 'dev_blog_list',
    label: 'Dev Blog',
    description: 'Список последних постов дев-блога.',
    create: ({ id }) => ({
      id,
      type: 'dev_blog_list',
      enabled: true,
      title: 'Dev Blog',
      dataSource: {
        mode: 'auto',
        entity: 'dev_blog',
        filter: {
          limit: 6,
          order: 'publish_at_desc',
        },
      },
      slots: {
        headline: 'Dev Blog',
      },
    }),
  },
  {
    type: 'quests_carousel',
    label: 'Квесты',
    description: 'Карусель избранных квестов.',
    create: ({ id }) => ({
      id,
      type: 'quests_carousel',
      enabled: true,
      title: 'Квесты',
      dataSource: {
        mode: 'auto',
        entity: 'quest',
        filter: {
          limit: 12,
          order: 'rating_desc',
        },
      },
    }),
  },
  {
    type: 'nodes_carousel',
    label: 'Ноды',
    description: 'Подборка рекомендованных нод.',
    create: ({ id }) => ({
      id,
      type: 'nodes_carousel',
      enabled: true,
      title: 'Ноды',
      dataSource: {
        mode: 'auto',
        entity: 'node',
        filter: {
          limit: 12,
          order: 'updated_at_desc',
        },
      },
    }),
  },
  {
    type: 'popular_carousel',
    label: 'Популярное',
    description: 'Самые просматриваемые квесты и ноды.',
    create: ({ id }) => ({
      id,
      type: 'popular_carousel',
      enabled: true,
      title: 'Популярное',
      dataSource: {
        mode: 'auto',
        entity: 'node',
        filter: {
          limit: 10,
          order: 'views_desc',
        },
      },
    }),
  },
  {
    type: 'editorial_picks',
    label: 'Выбор редакции',
    description: 'Ручной список материалов от редакции.',
    create: ({ id }) => ({
      id,
      type: 'editorial_picks',
      enabled: true,
      title: 'Выбор редакции',
      slots: {
        headline: 'Выбор редакции',
        description: 'Материалы, подобранные командой.',
      },
      dataSource: {
        mode: 'manual',
        entity: 'node',
        items: [],
      },
    }),
  },
  {
    type: 'recommendations',
    label: 'Рекомендации',
    description: 'Автоматические рекомендации по интересам.',
    create: ({ id }) => ({
      id,
      type: 'recommendations',
      enabled: true,
      title: 'Рекомендации',
      dataSource: {
        mode: 'auto',
        entity: 'node',
        filter: {
          limit: 8,
          order: 'personalized_desc',
        },
      },
    }),
  },
  {
    type: 'custom_carousel',
    label: 'Кастомная карусель',
    description: 'Ручной список карточек с произвольным контентом.',
    create: ({ id }) => ({
      id,
      type: 'custom_carousel',
      enabled: true,
      title: 'Промо-блок',
      dataSource: {
        mode: 'manual',
        entity: 'custom',
        items: [],
      },
      slots: {
        layout: 'carousel',
      },
    }),
  },
];

const DEFINITION_MAP = new Map<HomeBlockType, BlockDefinition>(DEFINITIONS.map((definition) => [definition.type, definition]));

function nextBlockId(type: HomeBlockType, existing: HomeBlock[]): string {
  const prefix = type.replace(/_/g, '-');
  let counter = 1;
  let candidate = `${prefix}-${counter}`;
  const ids = new Set(existing.map((block) => block.id));
  while (ids.has(candidate)) {
    counter += 1;
    candidate = `${prefix}-${counter}`;
  }
  return candidate;
}

export function generateBlockId(type: HomeBlockType, existing: HomeBlock[]): string {
  return nextBlockId(type, existing);
}

export function createBlockInstance(type: HomeBlockType, existing: HomeBlock[]): HomeBlock {
  const id = nextBlockId(type, existing);
  const definition = DEFINITION_MAP.get(type);
  if (!definition) {
    return {
      id,
      type,
      enabled: true,
    };
  }
  return definition.create({ id, existing });
}

export function getBlockDefinition(type: HomeBlockType): BlockDefinition | undefined {
  return DEFINITION_MAP.get(type);
}

export function listBlockDefinitions(): BlockDefinition[] {
  return DEFINITIONS.slice();
}

export function getBlockLabel(type: HomeBlockType): string {
  return DEFINITION_MAP.get(type)?.label ?? type;
}

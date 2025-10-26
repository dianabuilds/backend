import { listBlockDefinitions } from '../home/blockDefinitions';
import type { HomeBlockType } from '../home/types';

const definitions = listBlockDefinitions();
const definitionMap = new Map(definitions.map((definition) => [definition.type, definition]));

function baseLabel(type: HomeBlockType, fallback: string): string {
  return definitionMap.get(type)?.label ?? fallback;
}

function baseDescription(type: HomeBlockType, fallback: string): string {
  return definitionMap.get(type)?.description ?? fallback;
}

export type BlockCategory =
  | 'hero'
  | 'content'
  | 'catalog'
  | 'promo'
  | 'personalization'
  | 'global'
  | 'metrics';

export type BlockSourceMode = 'manual' | 'auto' | 'mixed';

export type BlockLocale = 'ru' | 'en';

export type BlockSurface =
  | 'home'
  | 'landing'
  | 'promo'
  | 'dev-blog'
  | 'collection'
  | 'article'
  | 'help'
  | 'global';

export type BlockPreviewKind =
  | 'hero'
  | 'list'
  | 'carousel'
  | 'custom'
  | 'personalized'
  | 'header'
  | 'footer'
  | 'faq'
  | 'promo'
  | 'metrics';

export type BlockStatus = 'available' | 'design' | 'research';

type SharedMetadata = {
  id: string;
  label: string;
  description: string;
  category: BlockCategory;
  sources: BlockSourceMode[];
  surfaces: BlockSurface[];
  owners: string[];
  locales: BlockLocale[];
  documentationUrl?: string;
  keywords?: string[];
  preview: BlockPreviewKind;
  statusNote?: string;
};

type AvailableBlockMetadata = SharedMetadata & {
  status: 'available';
  type: HomeBlockType;
};

type UpcomingBlockMetadata = SharedMetadata & {
  status: Exclude<BlockStatus, 'available'>;
};

export type SiteBlockLibraryEntry = AvailableBlockMetadata | UpcomingBlockMetadata;

const DOC_LIBRARY_URL = '/docs/site-editor-block-library';

export const SITE_BLOCK_LIBRARY: SiteBlockLibraryEntry[] = [
  {
    id: 'hero',
    type: 'hero',
    status: 'available',
    label: baseLabel('hero', 'Hero-блок'),
    description: baseDescription('hero', 'Большой первый экран с заголовком и CTA.'),
    category: 'hero',
    sources: ['manual'],
    surfaces: ['home', 'landing', 'promo'],
    owners: ['Маркетинг'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#hero`,
    keywords: ['первый экран', 'cta', 'hero'],
    preview: 'hero',
  },
  {
    id: 'dev_blog_list',
    type: 'dev_blog_list',
    status: 'available',
    label: baseLabel('dev_blog_list', 'Dev Blog'),
    description: baseDescription('dev_blog_list', 'Список последних постов дев-блога.'),
    category: 'content',
    sources: ['auto'],
    surfaces: ['home', 'dev-blog'],
    owners: ['DevRel', 'Контент'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#dev_blog_list`,
    keywords: ['контент', 'dev blog'],
    preview: 'list',
  },
  {
    id: 'quests_carousel',
    type: 'quests_carousel',
    status: 'available',
    label: baseLabel('quests_carousel', 'Квесты'),
    description: baseDescription('quests_carousel', 'Карусель избранных квестов.'),
    category: 'catalog',
    sources: ['auto'],
    surfaces: ['home', 'landing', 'promo'],
    owners: ['Продакт Quests'],
    locales: ['ru'],
    documentationUrl: `${DOC_LIBRARY_URL}#quests_carousel`,
    keywords: ['квесты', 'каталог'],
    preview: 'carousel',
  },
  {
    id: 'nodes_carousel',
    type: 'nodes_carousel',
    status: 'available',
    label: baseLabel('nodes_carousel', 'Ноды'),
    description: baseDescription('nodes_carousel', 'Подборка рекомендованных нод.'),
    category: 'catalog',
    sources: ['auto'],
    surfaces: ['home', 'landing', 'promo', 'collection'],
    owners: ['Продакт Nodes'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#nodes_carousel`,
    keywords: ['ноды', 'каталог'],
    preview: 'carousel',
  },
  {
    id: 'popular_carousel',
    type: 'popular_carousel',
    status: 'available',
    label: baseLabel('popular_carousel', 'Популярное'),
    description: baseDescription('popular_carousel', 'Самые просматриваемые квесты и ноды.'),
    category: 'catalog',
    sources: ['auto'],
    surfaces: ['home', 'landing'],
    owners: ['Маркетинг'],
    locales: ['ru'],
    documentationUrl: `${DOC_LIBRARY_URL}#popular_carousel`,
    keywords: ['просмотры', 'каталог'],
    preview: 'carousel',
  },
  {
    id: 'editorial_picks',
    type: 'editorial_picks',
    status: 'available',
    label: baseLabel('editorial_picks', 'Выбор редакции'),
    description: baseDescription('editorial_picks', 'Ручной список материалов от редакции.'),
    category: 'content',
    sources: ['manual'],
    surfaces: ['home', 'landing', 'promo'],
    owners: ['Редакция контента'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#editorial_picks`,
    keywords: ['подборка', 'контент'],
    preview: 'list',
  },
  {
    id: 'recommendations',
    type: 'recommendations',
    status: 'available',
    label: baseLabel('recommendations', 'Рекомендации'),
    description: baseDescription('recommendations', 'Автоматические рекомендации по интересам.'),
    category: 'personalization',
    sources: ['auto'],
    surfaces: ['home', 'landing', 'promo'],
    owners: ['Data/ML'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#recommendations`,
    keywords: ['персонализация', 'рекомендации'],
    preview: 'personalized',
    statusNote: 'Требует адаптера рекомендаций',
  },
  {
    id: 'custom_carousel',
    type: 'custom_carousel',
    status: 'available',
    label: baseLabel('custom_carousel', 'Кастомная карусель'),
    description: baseDescription('custom_carousel', 'Ручной список карточек с произвольным контентом.'),
    category: 'promo',
    sources: ['manual'],
    surfaces: ['landing', 'promo'],
    owners: ['Маркетинг'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#custom_carousel`,
    keywords: ['промо', 'ручной'],
    preview: 'custom',
  },
  {
    id: 'global_header',
    status: 'design',
    label: 'Глобальный хедер',
    description: 'Единая навигация по публичному сайту с локализованными ссылками и CTA.',
    category: 'global',
    sources: ['manual'],
    surfaces: ['global'],
    owners: ['Маркетинг', 'Продукт'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#global_header`,
    keywords: ['навигация', 'header'],
    preview: 'header',
    statusNote: 'Дизайн и API в разработке',
  },
  {
    id: 'global_footer',
    status: 'design',
    label: 'Глобальный футер',
    description: 'Контакты, юридическая информация и ссылки на разделы для всех страниц.',
    category: 'global',
    sources: ['manual'],
    surfaces: ['global'],
    owners: ['Маркетинг'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#global_footer`,
    keywords: ['footer', 'глобальный блок'],
    preview: 'footer',
    statusNote: 'Дизайн и контент в работе',
  },
  {
    id: 'faq_list',
    status: 'research',
    label: 'FAQ / Справка',
    description: 'Список вопросов и ответов для справки и лендингов поддержки.',
    category: 'content',
    sources: ['manual', 'auto'],
    surfaces: ['help', 'landing'],
    owners: ['Саппорт', 'Контент'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#faq_list`,
    keywords: ['faq', 'справка'],
    preview: 'faq',
    statusNote: 'Уточняем структуру данных',
  },
  {
    id: 'promo_banner',
    status: 'research',
    label: 'Промо-баннер',
    description: 'Одноэкранный баннер с медиа, описанием и расписанием показа.',
    category: 'promo',
    sources: ['manual'],
    surfaces: ['landing', 'promo'],
    owners: ['Маркетинг'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#promo_banner`,
    keywords: ['баннер', 'промо'],
    preview: 'promo',
    statusNote: 'Требуется проработка расписания и таргетинга',
  },
  {
    id: 'related_posts',
    status: 'research',
    label: 'Связанные материалы',
    description: 'Блок «Читайте также» для статей и блога с авто и ручной подборкой.',
    category: 'content',
    sources: ['auto', 'manual'],
    surfaces: ['article', 'dev-blog'],
    owners: ['DevRel', 'Контент'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#related_posts`,
    keywords: ['related', 'контент'],
    preview: 'list',
    statusNote: 'Зависит от API нод и тегов',
  },
  {
    id: 'metrics_highlight',
    status: 'research',
    label: 'Метрические карточки',
    description: 'Плашка KPI или статистики для главной и кампанийных лендингов.',
    category: 'metrics',
    sources: ['manual', 'auto'],
    surfaces: ['home', 'landing', 'promo'],
    owners: ['Продакт', 'Аналитика'],
    locales: ['ru', 'en'],
    documentationUrl: `${DOC_LIBRARY_URL}#metrics_highlight`,
    keywords: ['метрики', 'статистика'],
    preview: 'metrics',
    statusNote: 'Определяем источники данных',
  },
];

export const CATEGORY_LABELS: Record<BlockCategory, string> = {
  hero: 'Hero / первый экран',
  content: 'Контент',
  catalog: 'Каталог',
  promo: 'Промо',
  personalization: 'Персонализация',
  global: 'Глобальные блоки',
  metrics: 'Метрики',
};

export const SOURCE_LABELS: Record<BlockSourceMode, string> = {
  manual: 'Ручной',
  auto: 'Авто',
  mixed: 'Смешанный',
};

export const LOCALE_LABELS: Record<BlockLocale, string> = {
  ru: 'Русский',
  en: 'Английский',
};

export const SURFACE_LABELS: Record<BlockSurface, string> = {
  home: 'Главная /',
  landing: 'Лендинги',
  promo: 'Промо-страницы',
  'dev-blog': 'Dev Blog',
  collection: 'Коллекции',
  article: 'Статьи',
  help: 'Справка',
  global: 'Глобальные блоки',
};

export const STATUS_LABELS: Record<BlockStatus, { label: string; color: 'success' | 'warning' | 'info' }> = {
  available: { label: 'Доступен', color: 'success' },
  design: { label: 'В дизайне', color: 'warning' },
  research: { label: 'Исследуем', color: 'info' },
};


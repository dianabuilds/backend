import type {
  SiteBlockBinding,
  SitePageAttachedBlock,
  SitePageDraft,
  SitePagePreviewResponse,
  SitePageSummary,
} from '@shared/types/management';

type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends Record<string, unknown>
    ? DeepPartial<T[K]>
    : T[K] extends Array<infer U>
      ? Array<DeepPartial<U>>
      : T[K];
};

function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

const BASE_HEADER_BINDING: SiteBlockBinding = {
  block_id: 'block-header',
  key: 'header-nav',
  title: 'Header Navigation',
  section: 'header',
  status: 'published',
  locale: 'ru',
  default_locale: 'ru',
  available_locales: ['ru'],
  requires_publisher: true,
  published_version: 3,
  draft_version: 4,
  review_status: 'none',
  updated_at: '2025-10-25T08:55:00Z',
  updated_by: 'editor@caves.dev',
  has_draft_binding: false,
  last_published_at: '2025-10-20T08:00:00Z',
  position: 0,
  scope: 'shared',
};

const BASE_HEADER_GLOBAL_REF: SitePageAttachedBlock = {
  block_id: 'block-header',
  key: 'header-nav',
  title: 'Header Navigation',
  section: 'header',
  status: 'published',
  review_status: 'none',
  requires_publisher: true,
  published_version: 3,
  draft_version: 4,
  updated_at: '2025-10-25T08:55:00Z',
  updated_by: 'editor@caves.dev',
  locale: 'ru',
  default_locale: 'ru',
  available_locales: ['ru'],
  scope: 'shared',
};

const BASE_HOME_PAGE_SUMMARY: SitePageSummary = {
  id: 'page-home',
  slug: '/',
  type: 'landing',
  status: 'published',
  title: 'Home Landing',
  locale: 'ru',
  owner: 'marketing',
  updated_at: '2025-10-25T09:00:00Z',
  published_version: 12,
  draft_version: 14,
  has_pending_review: false,
  pinned: true,
  bindings: [BASE_HEADER_BINDING],
  shared_bindings: [BASE_HEADER_GLOBAL_REF],
  default_locale: 'ru',
  available_locales: ['ru', 'en'],
  localized_slugs: { ru: 'home', en: 'home-en' },
  locales: [
    { locale: 'ru', slug: 'home', status: 'published', title: 'Home Landing RU' },
    { locale: 'en', slug: 'home-en', status: 'draft', title: 'Home Landing EN' },
  ],
};

const BASE_HOME_PAGE_DRAFT: SitePageDraft = {
  page_id: 'page-home',
  version: 14,
  data: {
    locales: {
      ru: {
        blocks: [
          { id: 'hero-1', type: 'hero', enabled: true, title: 'Hero RU', section: 'hero' },
        ],
      },
      en: {
        blocks: [],
      },
    },
    shared: {
      assignments: {
        header: 'header-nav',
      },
    },
  },
  meta: {
    locales: {
      ru: { title: 'Home Landing RU', slug: 'home', status: 'ready' },
      en: { title: 'Home Landing EN', slug: 'home-en', status: 'draft' },
    },
    shared: {},
  },
  comment: null,
  review_status: 'none',
  bindings: [BASE_HEADER_BINDING],
  locales: {
    ru: {
      data: {
        blocks: [
          { id: 'hero-1', type: 'hero', enabled: true, title: 'Hero RU', section: 'hero' },
        ],
      },
      meta: { title: 'Home Landing RU' },
      status: 'ready',
      slug: 'home',
      title: 'Home Landing RU',
    },
    en: {
      data: { blocks: [] },
      meta: { title: 'Home Landing EN' },
      status: 'draft',
      slug: 'home-en',
      title: 'Home Landing EN',
    },
  },
  updated_at: '2025-10-25T09:40:00Z',
  updated_by: 'editor@caves.dev',
};

const BASE_HOME_PREVIEW_RESPONSE: SitePagePreviewResponse = {
  page: BASE_HOME_PAGE_SUMMARY,
  draft_version: 14,
  published_version: 12,
  requested_version: null,
  version_mismatch: false,
  default_locale: 'ru',
  available_locales: ['ru', 'en'],
  localized_slugs: { ru: 'home', en: 'home-en' },
  bindings: [BASE_HEADER_BINDING],
  shared: {},
  locales: {
    ru: {
      data: {
        blocks: [
          { id: 'hero-1', type: 'hero', enabled: true, title: 'Hero RU', section: 'hero' },
        ],
      },
      meta: { title: 'Home Landing RU' },
    },
    en: {
      data: { blocks: [] },
      meta: { title: 'Home Landing EN' },
    },
  },
  preview: {
    page_id: 'page-home',
    slug: '/',
    locale: 'ru',
    title: 'Home Landing',
    type: 'landing',
    version: 14,
    generated_at: '2025-10-25T09:45:00Z',
    meta: { title: 'Home Landing' },
    payload: {
      version: 14,
      locale: 'ru',
      blocks: [
        {
          id: 'hero-1',
          type: 'hero',
          title: 'Hero RU',
          enabled: true,
          items: [],
          layout: null,
          dataSource: null,
        },
      ],
      fallbacks: [],
      meta: { title: 'Home Landing RU' },
    },
    blocks: [],
    fallbacks: [],
    shared_bindings: {
      'header-nav': {
        id: 'block-header',
        key: 'header-nav',
        title: 'Header Navigation',
        locale: 'ru',
        requires_publisher: true,
        version: 4,
        sections: ['header'],
        available_locales: ['ru'],
        scope: 'shared',
        data: {},
        meta: {},
      },
    },
    block_refs: [
      { block_id: 'block-header', key: 'header-nav', section: 'header' },
    ],
  },
  preview_variants: [],
  layouts: {},
};

export function createHeaderBinding(overrides: DeepPartial<SiteBlockBinding> = {}): SiteBlockBinding {
  return deepClone({ ...BASE_HEADER_BINDING, ...overrides });
}

export function createHomePageSummary(overrides: DeepPartial<SitePageSummary> = {}): SitePageSummary {
  const base = deepClone(BASE_HOME_PAGE_SUMMARY);
  if (overrides.bindings) {
    base.bindings = deepClone(overrides.bindings) as SiteBlockBinding[];
  }
  if (overrides.shared_bindings) {
    base.shared_bindings = deepClone(overrides.shared_bindings);
  }
  return { ...base, ...overrides } as SitePageSummary;
}

export function createHomePageDraft(overrides: DeepPartial<SitePageDraft> = {}): SitePageDraft {
  const base = deepClone(BASE_HOME_PAGE_DRAFT);
  if (overrides.bindings) {
    base.bindings = deepClone(overrides.bindings) as SiteBlockBinding[];
  }
  return { ...base, ...overrides } as SitePageDraft;
}

export function createHomePreviewResponse(
  overrides: DeepPartial<SitePagePreviewResponse> = {},
): SitePagePreviewResponse {
  const base = deepClone(BASE_HOME_PREVIEW_RESPONSE);
  if (overrides.bindings) {
    base.bindings = deepClone(overrides.bindings) as SiteBlockBinding[];
  }
  if (overrides.page) {
    base.page = deepClone(overrides.page) as SitePageSummary;
  }
  return { ...base, ...overrides } as SitePagePreviewResponse;
}

export const HEADER_BINDING_FIXTURE = createHeaderBinding();

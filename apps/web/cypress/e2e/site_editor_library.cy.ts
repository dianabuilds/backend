/// <reference types="cypress" />

type PageSummary = {
  id: string;
  slug: string;
  title: string;
  type: string;
  status: string;
  locale: string;
  owner?: string | null;
  updated_at?: string | null;
  published_version?: number | null;
  draft_version?: number | null;
  has_pending_review?: boolean | null;
  default_locale?: string | null;
  available_locales?: string[] | null;
  localized_slugs?: Record<string, string> | null;
  bindings?: Array<Record<string, unknown>> | null;
};

type PageDraft = {
  page_id: string;
  version: number;
  data: Record<string, unknown>;
  meta: Record<string, unknown>;
  comment?: string | null;
  review_status: string;
  updated_at?: string | null;
  updated_by?: string | null;
  bindings?: Array<Record<string, unknown>>;
};

const PAGE_ID = 'page-home';

const PAGE_SUMMARY: PageSummary = {
  id: PAGE_ID,
  slug: '/',
  title: 'Главная страница',
  type: 'landing',
  status: 'draft',
  locale: 'ru',
  owner: 'marketing',
  updated_at: '2025-10-25T09:00:00Z',
  published_version: 12,
  draft_version: 14,
  has_pending_review: false,
  default_locale: 'ru',
  available_locales: ['ru'],
  localized_slugs: { ru: '' },
  bindings: [],
};

const PAGE_DRAFT: PageDraft = {
  page_id: PAGE_ID,
  version: 14,
  data: { blocks: [], shared: {} },
  meta: {},
  review_status: 'none',
  updated_at: '2025-10-25T09:00:00Z',
  updated_by: 'editor@caves.dev',
  bindings: [],
};

const DRAFT_DIFF = {
  draft_version: PAGE_DRAFT.version,
  published_version: PAGE_SUMMARY.published_version,
  diff: [],
};

const HISTORY_RESPONSE = {
  items: [],
  total: 0,
  limit: 10,
  offset: 0,
};

const AUDIT_RESPONSE = {
  items: [],
  total: 0,
  limit: 20,
  offset: 0,
};

const METRICS_RESPONSE = {
  page_id: PAGE_ID,
  period: '7d',
  range: { start: '2025-10-18T00:00:00Z', end: '2025-10-25T00:00:00Z' },
  status: 'ready',
  metrics: {},
  alerts: [],
};

const SITE_BLOCKS_RESPONSE = {
  items: [
    {
      id: 'block-header',
      key: 'header-template',
      title: 'Хедер',
      section: 'header',
      status: 'published',
      review_status: 'none',
      requires_publisher: true,
      locale: 'ru',
      default_locale: 'ru',
      available_locales: ['ru', 'en'],
      scope: 'shared',
      published_version: 3,
      draft_version: 3,
      usage_count: 5,
      updated_at: '2025-10-25T08:00:00Z',
      updated_by: 'editor@caves.dev',
      meta: { owner: 'Маркетинг', documentation: 'https://docs.example.com/header' },
      data: {},
      extras: {},
    },
  ],
  page: 1,
  page_size: 50,
  total: 1,
};

describe('Site editor library sidebar', () => {
  beforeEach(() => {
    cy.intercept('GET', '/v1/users/me', {
      user: {
        id: 'admin-1',
        email: 'admin@caves.dev',
        roles: ['editor', 'admin'],
      },
    }).as('getCurrentUser');

    cy.intercept('POST', '/v1/metrics/rum', { statusCode: 204, body: {} }).as('rumEvent');
    cy.intercept('GET', `/v1/site/pages/${PAGE_ID}`, {
      statusCode: 200,
      body: PAGE_SUMMARY,
    }).as('getSitePage');
    cy.intercept('GET', `/v1/site/pages/${PAGE_ID}/draft`, {
      statusCode: 200,
      body: PAGE_DRAFT,
    }).as('getSiteDraft');
    cy.intercept('GET', `/v1/site/pages/${PAGE_ID}/draft/diff`, {
      statusCode: 200,
      body: DRAFT_DIFF,
    }).as('getSiteDraftDiff');
    cy.intercept('GET', `/v1/site/pages/${PAGE_ID}/history*`, {
      statusCode: 200,
      body: HISTORY_RESPONSE,
    }).as('getSiteHistory');
    cy.intercept('GET', '/v1/site/audit*', {
      statusCode: 200,
      body: AUDIT_RESPONSE,
    }).as('getSiteAudit');
    cy.intercept('GET', `/v1/site/pages/${PAGE_ID}/metrics*`, {
      statusCode: 200,
      body: METRICS_RESPONSE,
    }).as('getSiteMetrics');
    cy.intercept('GET', /\/v1\/site\/blocks.*/, {
      statusCode: 200,
      body: SITE_BLOCKS_RESPONSE,
    }).as('getSiteBlocks');

    cy.intercept('PUT', `/v1/site/pages/${PAGE_ID}/draft`, (req) => {
      req.reply({
        statusCode: 200,
        body: {
          ...PAGE_DRAFT,
          version: req.body?.version ?? PAGE_DRAFT.version,
          data: req.body?.data ?? PAGE_DRAFT.data,
          meta: req.body?.meta ?? PAGE_DRAFT.meta,
        },
      });
    }).as('saveDraft');

    cy.intercept('POST', `/v1/site/pages/${PAGE_ID}/draft/validate`, {
      statusCode: 200,
      body: { valid: true, data: {}, meta: {} },
    }).as('validateDraft');
  });

  function openPageEditor(): void {
    cy.visit(`/management/site-editor/pages/${PAGE_ID}`);
    cy.wait([
      '@getCurrentUser',
      '@getSitePage',
      '@getSiteDraft',
      '@getSiteDraftDiff',
      '@getSiteHistory',
      '@getSiteAudit',
      '@getSiteMetrics',
      '@rumEvent',
    ]);
  }

  it('adds a hero block from templates tab', () => {
    openPageEditor();

    cy.contains('button', 'Hero-блок').click();

    cy.get('[data-testid="home-block-hero-1"]').should('exist').and('contain', 'Hero');
    cy.wait('@saveDraft').its('request.body.data.blocks').should('have.length', 1);
    cy.wait('@validateDraft');
  });

  it('filters шаблоны по поиску', () => {
    openPageEditor();

    cy.get('input[placeholder="Поиск по названию или описанию"]').as('searchInput');

    cy.get('@searchInput').type('Dev');
    cy.contains('Dev Blog').should('be.visible');
    cy.contains('Hero-блок').should('not.exist');

    cy.get('@searchInput').clear();
    cy.contains('Hero-блок').should('be.visible');
  });

  it('opens full library page from sidebar', () => {
    openPageEditor();

    cy.contains('Открыть полную библиотеку').click();
    cy.location('pathname').should('eq', '/management/site-editor/library');
    cy.wait('@getSiteBlocks');
    cy.contains('Библиотека блоков').should('be.visible');
  });
});

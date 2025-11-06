const pageId = 'page-home';

const blocks = [
  {
    id: 'hero',
    type: 'hero',
    enabled: true,
    title: 'Главный блок',
    slots: {
      headline: 'Главный блок',
      subheadline: 'Промо недели',
    },
    dataSource: { mode: 'manual', entity: 'node', items: ['n-1'] },
  },
  {
    id: 'quests',
    type: 'quests_carousel',
    enabled: true,
    title: 'Квесты недели',
    dataSource: { mode: 'auto', entity: 'quest', filter: { limit: 6, tag: 'weekly' } },
  },
] as const;

const pageResponse = {
  id: pageId,
  slug: 'main',
  title: 'Главная страница',
  type: 'landing',
  status: 'draft',
  locale: 'ru',
  owner: 'marketing',
  updated_at: '2025-10-27T09:00:00Z',
  published_version: 2,
  draft_version: 3,
  has_pending_review: false,
  pinned: true,
  shared_bindings: [],
};

const draftResponse = {
  page_id: pageId,
  version: 3,
  data: { blocks, meta: { title: 'Главная', description: 'Описание' } },
  meta: { title: 'Главная', description: 'Описание' },
  comment: null,
  review_status: 'none',
  updated_at: '2025-10-27T09:05:00Z',
  updated_by: 'admin@caves.dev',
  shared_bindings: [],
};

const previewPayload = {
  slug: 'main',
  version: 3,
  updated_at: '2025-10-27T09:06:00Z',
  generated_at: '2025-10-27T09:06:30Z',
  published_at: null,
  blocks: [
    {
      id: 'hero',
      type: 'hero',
      title: 'Главный блок',
      items: [
        { title: 'Путеводитель по новым пещерам' },
        { title: 'Как собрать идеальную группу исследователей' },
      ],
    },
    {
      id: 'quests',
      type: 'quests_carousel',
      title: 'Квесты недели',
      items: [
        { title: 'Тайна северного грота' },
        { title: 'Охота за лунным кристаллом' },
      ],
    },
  ],
  fallbacks: [],
  meta: { title: 'Главная', preview: { mode: 'site_preview' } },
};

const diffResponse = {
  draft_version: 3,
  published_version: 2,
  diff: [],
};

const historyResponse = {
  items: [],
  total: 0,
  limit: 10,
  offset: 0,
};

const auditResponse = {
  items: [],
  total: 0,
  limit: 10,
  offset: 0,
};

const metricsResponse = {
  page_id: pageId,
  period: '7d',
  range: {
    start: '2025-10-20T00:00:00Z',
    end: '2025-10-27T00:00:00Z',
  },
  status: 'ok',
  source_lag_ms: 0,
  metrics: {},
  alerts: [],
};

describe('Site editor preview rate limit handling', () => {
  beforeEach(() => {
    cy.intercept('GET', '/v1/users/me', {
      user: {
        id: 'admin-1',
        email: 'admin@caves.dev',
        roles: ['admin'],
      },
    }).as('getCurrentUser');

    cy.intercept('GET', `/v1/site/pages/${pageId}`, pageResponse).as('getSitePage');
    cy.intercept('GET', `/v1/site/pages/${pageId}/draft`, draftResponse).as('getSitePageDraft');
    cy.intercept('GET', `/v1/site/pages/${pageId}/draft/diff`, diffResponse).as('getSitePageDiff');
    cy.intercept('GET', `/v1/site/pages/${pageId}/history*`, historyResponse).as('getSitePageHistory');
    cy.intercept('GET', '/v1/site/audit*', auditResponse).as('getSiteAudit');
    cy.intercept('GET', `/v1/site/pages/${pageId}/metrics*`, metricsResponse).as('getSiteMetrics');
    cy.intercept('POST', '/v1/metrics/rum', { statusCode: 204, body: {} }).as('rumEvent');
  });

  it('shows toast on 429 and retries after timeout', () => {
    let previewCalls = 0;

    cy.intercept('POST', `/v1/site/pages/${pageId}/preview`, (req) => {
      previewCalls += 1;
      if (previewCalls === 1) {
        req.reply({
          statusCode: 429,
          headers: { 'Retry-After': '1' },
          body: { detail: 'Превышен лимит запросов' },
        });
      } else {
        req.reply({
          statusCode: 200,
          body: {
            page: pageResponse,
            draft_version: 3,
            published_version: 2,
            requested_version: 3,
            version_mismatch: false,
            layouts: {
              desktop: {
                layout: 'desktop',
                generated_at: '2025-10-27T09:06:30Z',
                data: { blocks },
                meta: { title: 'Главная' },
                payload: previewPayload,
              },
            },
          },
        });
      }
    }).as('previewSitePage');

    cy.visit(`/management/site-editor/pages/${pageId}`);
    cy.wait(['@getCurrentUser', '@getSitePage', '@getSitePageDraft']);

    cy.wait('@previewSitePage').its('response.statusCode').should('eq', 429);
    cy.contains('Не удалось загрузить превью.').should('be.visible');
    cy.contains('Превышен лимит запросов').should('be.visible');
    cy.contains('button', 'Попробовать снова').click();
    cy.wait('@previewSitePage').its('response.statusCode').should('eq', 200);

    cy.get('[data-testid="site-page-preview-success"]').should('be.visible');
    cy.wrap(null).then(() => {
      expect(previewCalls).to.equal(2);
    });
    cy.get('[data-testid="site-page-preview-order"]').should('contain', '#1 · hero · hero');
  });
});

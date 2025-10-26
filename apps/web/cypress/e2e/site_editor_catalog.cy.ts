const catalogResponse = {
  items: [
    {
      id: 'page-home',
      slug: '/',
      title: 'Главная страница',
      type: 'landing',
      status: 'published',
      locale: 'ru',
      owner: 'marketing',
      updated_at: '2025-10-25T09:00:00Z',
      published_version: 12,
      draft_version: 14,
      has_pending_review: false,
    },
    {
      id: 'page-help',
      slug: '/help',
      title: 'Справка',
      type: 'article',
      status: 'draft',
      locale: 'ru',
      owner: 'support',
      updated_at: '2025-10-24T11:30:00Z',
      published_version: 5,
      draft_version: 7,
      has_pending_review: true,
    },
  ],
  page: 1,
  page_size: 20,
  total: 2,
};

const draftOnlyResponse = {
  items: [catalogResponse.items[1]],
  page: 1,
  page_size: 20,
  total: 1,
};

const historyResponse = {
  items: [
    {
      id: 'version-2',
      page_id: 'page-home',
      version: 2,
      data: {},
      meta: {},
      comment: 'Второй релиз',
      diff: [
        { type: 'block', blockId: 'hero-1', change: 'updated' },
        { type: 'block', blockId: 'promo-1', change: 'added' },
      ],
      published_at: '2025-10-25T10:00:00Z',
      published_by: 'editor@caves.dev',
    },
  ],
  total: 1,
  limit: 10,
  offset: 0,
};

const auditResponse = {
  items: [
    {
      id: 'audit-1',
      entity_type: 'page',
      entity_id: 'page-home',
      action: 'publish',
      snapshot: { version: 2, comment: 'Второй релиз' },
      actor: 'editor@caves.dev',
      created_at: '2025-10-25T10:00:05Z',
    },
  ],
  total: 1,
  limit: 20,
  offset: 0,
};

describe('Site editor catalog', () => {
  beforeEach(() => {
    cy.intercept('GET', '/v1/users/me', {
      user: {
        id: 'admin-1',
        email: 'admin@caves.dev',
        roles: ['site.admin'],
      },
    }).as('getCurrentUser');

    cy.intercept('POST', '/v1/metrics/rum', { statusCode: 204, body: {} }).as('rumEvent');
    cy.intercept('GET', /\/v1\/site\/pages\/[^/]+\/history.*/, {
      statusCode: 200,
      body: historyResponse,
    }).as('getSiteHistory');
    cy.intercept('GET', /\/v1\/site\/audit.*/, {
      statusCode: 200,
      body: auditResponse,
    }).as('getSiteAudit');
  });

  it('lists pages and filters by status', () => {
    const requests: string[] = [];

    cy.intercept('GET', '/v1/site/pages*', (req) => {
      requests.push(req.url);
      if (req.query?.status === 'draft') {
        req.reply({ statusCode: 200, body: draftOnlyResponse });
      } else {
        req.reply({ statusCode: 200, body: catalogResponse });
      }
    }).as('getSitePages');

    cy.visit('/management/site-editor');
    cy.wait(['@getCurrentUser', '@getSitePages', '@getSiteHistory', '@getSiteAudit', '@rumEvent']);

    cy.get('table').should('contain', 'Главная страница').and('contain', 'Справка');
    cy.get('[data-testid="site-page-detail"]')
      .should('contain', 'Главная страница')
      .and('contain', 'marketing')
      .and('contain', '/')
      .and('contain', 'Версия v2');

    cy.get('select[aria-label="Фильтр по статусу"]').select('Черновик');
    cy.wait('@getSitePages').its('request.url').should('include', 'status=draft');

    cy.get('table').should('not.contain', 'Главная страница').and('contain', 'Справка');
    cy.get('[data-testid="site-page-detail"]')
      .should('contain', 'Справка')
      .and('contain', 'support')
      .and('contain', '/help');

    cy.wrap(null).then(() => {
      const draftRequests = requests.filter((url) => url.includes('status=draft'));
      expect(draftRequests).to.have.length(1);
    });
  });
});

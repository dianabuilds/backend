const draftResponse = {
  slug: 'main',
  draft: {
    id: 'draft-1',
    slug: 'main',
    version: 1,
    status: 'draft',
    data: { blocks: [] },
    created_at: '2025-10-10T09:55:00Z',
    updated_at: '2025-10-10T09:55:00Z',
    published_at: null,
    created_by: 'admin@caves.dev',
    updated_by: 'admin@caves.dev',
    draft_of: null,
  },
  published: null,
};

const previewPayload = {
  slug: 'main',
  version: 1,
  updated_at: '2025-10-10T09:55:05Z',
  generated_at: '2025-10-10T09:55:05Z',
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
  ],
  fallbacks: [],
  meta: { title: 'Главная' },
};

describe('Security rate limit handling', () => {
  beforeEach(() => {
    cy.intercept('GET', '/v1/users/me', {
      user: {
        id: 'admin-1',
        email: 'admin@caves.dev',
        roles: ['admin'],
      },
    }).as('getCurrentUser');

    cy.intercept('GET', '/v1/admin/home', draftResponse).as('getHomeDraft');
    cy.intercept('POST', '/v1/metrics/rum', { statusCode: 204, body: {} }).as('rumEvent');
  });

  it('shows toast on 429 and retries after timeout', () => {
    let previewCalls = 0;

    cy.intercept('POST', '/v1/admin/home/preview', (req) => {
      previewCalls += 1;
      if (previewCalls === 1) {
        req.reply({
          statusCode: 429,
          headers: { 'Retry-After': '1' },
          body: { error: { code: 'rate_limited', message: 'Too fast' } },
        });
      } else {
        req.reply({ statusCode: 200, body: { slug: 'main', payload: previewPayload } });
      }
    }).as('previewHome');

    cy.visit('/management/home');
    cy.wait(['@getCurrentUser', '@getHomeDraft']);

    cy.wait('@previewHome').its('response.statusCode').should('eq', 429);
    cy.contains('Превышен лимит запросов').should('be.visible');
    cy.wait('@previewHome').its('response.statusCode').should('eq', 200);

    cy.get('[data-testid="home-preview-success"]').should('be.visible');
    cy.wrap(null).then(() => {
      expect(previewCalls).to.equal(2);
    });
  });
});

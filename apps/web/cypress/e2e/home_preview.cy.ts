const draftBlocks = [
  {
    id: 'hero',
    type: 'hero',
    enabled: true,
    title: 'Главный блок',
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

const draftResponse = {
  slug: 'main',
  draft: {
    id: 'draft-1',
    slug: 'main',
    version: 7,
    status: 'draft',
    data: { blocks: draftBlocks },
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
  version: 7,
  updated_at: '2025-10-10T09:55:00Z',
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
  meta: { title: 'Главная' },
};

describe('Home preview panel', () => {
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

  it('renders preview blocks in the editor order', () => {
    cy.intercept('POST', '/v1/admin/home/preview', (req) => {
      expect(req.body?.data?.blocks).to.have.length(2);
      req.reply({ statusCode: 200, body: { slug: 'main', payload: previewPayload } });
    }).as('previewHome');

    cy.visit('/management/home');
    cy.wait(['@getCurrentUser', '@getHomeDraft', '@previewHome']);

    cy.get('[data-testid="home-preview-order"]').should(($items) => {
      const text = $items.text();
      expect(text).to.contain('#1 · hero · hero');
      expect(text).to.contain('#2 · quests · quests_carousel');
    });

    cy.get('[data-testid="home-preview-frame"]').its('0.contentDocument.body').should('contain.text', 'Главный блок');
  });

  it('shows retry UI and recovers after network errors', () => {
    let previewCalls = 0;
    cy.intercept('POST', '/v1/admin/home/preview', (req) => {
      previewCalls += 1;
      if (previewCalls === 1) {
        req.reply({ statusCode: 503, body: { detail: 'home_storage_unavailable' } });
      } else {
        req.reply({ statusCode: 200, body: { slug: 'main', payload: previewPayload } });
      }
    }).as('previewHome');

    cy.visit('/management/home');
    cy.wait(['@getCurrentUser', '@getHomeDraft', '@previewHome']);

    cy.get('[data-testid="home-preview-error"]').should('contain', 'Не удалось');

    cy.contains('button', 'Попробовать снова').click();
    cy.wait('@previewHome');

    cy.get('[data-testid="home-preview-success"]').should('be.visible');
    cy.get('[data-testid="home-preview-order"]').should('contain', '#1 · hero · hero');
  });
});


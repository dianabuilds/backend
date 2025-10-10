const initialResponse = {
  slug: 'main',
  draft: {
    id: 'draft-1',
    slug: 'main',
    version: 7,
    status: 'draft',
    data: { blocks: [] },
    created_at: '2025-10-10T09:55:00Z',
    updated_at: '2025-10-10T09:58:00Z',
    published_at: null,
  },
  published: {
    id: 'pub-5',
    slug: 'main',
    version: 5,
    status: 'published',
    data: { blocks: [] },
    created_at: '2025-10-09T08:00:00Z',
    updated_at: '2025-10-09T08:05:00Z',
    published_at: '2025-10-09T08:05:00Z',
  },
  history: [
    {
      config_id: 'pub-5',
      version: 5,
      action: 'publish',
      actor: 'alice@caves.dev',
      actor_team: null,
      comment: 'Осеннее обновление',
      created_at: '2025-10-09T08:05:00Z',
      published_at: '2025-10-09T08:05:00Z',
      is_current: true,
    },
    {
      config_id: 'pub-4',
      version: 4,
      action: 'publish',
      actor: 'bob@caves.dev',
      actor_team: null,
      comment: 'Предыдущее оформление',
      created_at: '2025-10-01T07:00:00Z',
      published_at: '2025-10-01T07:00:00Z',
      is_current: false,
    },
  ],
};

const afterPublishResponse = {
  slug: 'main',
  draft: {
    id: 'draft-2',
    slug: 'main',
    version: 6,
    status: 'draft',
    data: { blocks: [] },
    created_at: '2025-10-10T10:10:00Z',
    updated_at: '2025-10-10T10:10:00Z',
    published_at: null,
  },
  published: {
    id: 'pub-6',
    slug: 'main',
    version: 6,
    status: 'published',
    data: { blocks: [] },
    created_at: '2025-10-10T10:10:00Z',
    updated_at: '2025-10-10T10:10:00Z',
    published_at: '2025-10-10T10:10:00Z',
  },
  history: [
    {
      config_id: 'pub-6',
      version: 6,
      action: 'publish',
      actor: 'editor@caves.dev',
      actor_team: null,
      comment: 'ship it',
      created_at: '2025-10-10T10:10:00Z',
      published_at: '2025-10-10T10:10:00Z',
      is_current: true,
    },
    {
      config_id: 'pub-5',
      version: 5,
      action: 'publish',
      actor: 'alice@caves.dev',
      actor_team: null,
      comment: 'Осеннее обновление',
      created_at: '2025-10-09T08:05:00Z',
      published_at: '2025-10-09T08:05:00Z',
      is_current: false,
    },
  ],
};

const restoreResponse = {
  slug: 'main',
  draft: {
    id: 'draft-restored',
    slug: 'main',
    version: 5,
    status: 'draft',
    data: { blocks: [] },
    created_at: '2025-10-10T10:15:00Z',
    updated_at: '2025-10-10T10:15:00Z',
    published_at: null,
  },
};

describe('Home publish & restore flow', () => {
  beforeEach(() => {
    cy.intercept('GET', '/v1/users/me', {
      user: {
        id: 'admin-1',
        email: 'admin@caves.dev',
        roles: ['admin'],
      },
    }).as('getCurrentUser');

    cy.intercept('POST', '/v1/metrics/rum', { statusCode: 204 }).as('rumEvent');

    let getCalls = 0;
    cy.intercept('GET', '/v1/admin/home', (req) => {
      getCalls += 1;
      if (getCalls === 1) {
        req.reply(initialResponse);
      } else {
        req.reply(afterPublishResponse);
      }
    }).as('getHome');

    cy.intercept('POST', '/v1/admin/home/publish', (req) => {
      expect(req.body).to.deep.equal({ slug: 'main', data: null, comment: 'ship it' });
      req.reply({ slug: 'main', published: afterPublishResponse.published });
    }).as('publishHome');

    cy.intercept('POST', '/v1/admin/home/restore/5', (req) => {
      expect(req.body).to.deep.equal({ slug: 'main', data: null, comment: 'rollback' });
      req.reply(restoreResponse);
    }).as('restoreHome');
  });

  it('publishes draft and restores previous version', () => {
    cy.visit('/management/home');
    cy.wait(['@getCurrentUser', '@getHome']);

    cy.contains('button', 'Опубликовать').click();
    cy.get('[role="dialog"]').within(() => {
      cy.get('textarea').clear().type('  ship it  ');
      cy.contains('button', 'Опубликовать').click();
    });

    cy.wait(['@publishHome', '@getHome']);
    cy.contains('Конфигурация опубликована').should('be.visible');

    cy.get('[data-testid="home-history-panel"]').within(() => {
      cy.get('[data-testid="home-history-entry"]').first().should('contain.text', 'Версия v6');
      cy.get('[data-testid="home-history-entry"]').first().should('contain.text', 'ship it');
    });

    cy.get('[data-testid="home-history-entry"]').eq(1).within(() => {
      cy.contains('button', 'Восстановить').click();
    });

    cy.get('[role="dialog"]').within(() => {
      cy.contains('Восстановить версию v5');
      cy.get('textarea').clear().type('  rollback ');
      cy.contains('button', 'Восстановить').click();
    });

    cy.wait('@restoreHome');
    cy.contains('Версия v5 восстановлена').should('be.visible');
  });
});

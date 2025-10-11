const listResponse = {
  items: [
    {
      id: 1,
      slug: 'first-post',
      title: 'First Post',
      summary: 'A quick look at what changed this week.',
      coverUrl: null,
      publishAt: '2025-10-10T10:00:00Z',
      updatedAt: '2025-10-10T12:00:00Z',
      author: { id: '42', name: 'Team' },
      tags: ['updates', 'alpha'],
    },
    {
      id: 2,
      slug: 'second-post',
      title: 'Second Post',
      summary: 'Deep dive into rendering optimisations.',
      coverUrl: null,
      publishAt: '2025-10-08T09:00:00Z',
      updatedAt: '2025-10-08T09:00:00Z',
      author: { id: '99', name: 'Engineering' },
      tags: ['engineering'],
    },
  ],
  total: 2,
  hasNext: false,
  availableTags: ['updates', 'alpha', 'engineering'],
  dateRange: { start: '2025-10-01T00:00:00Z', end: '2025-10-10T12:00:00Z' },
  appliedTags: [],
};

const filteredResponse = {
  ...listResponse,
  items: [listResponse.items[0]],
  total: 1,
  hasNext: false,
  appliedTags: ['updates'],
};

const detailResponse = {
  post: {
    id: 1,
    slug: 'first-post',
    title: 'First Post',
    summary: 'A quick look at what changed this week.',
    coverUrl: null,
    publishAt: '2025-10-10T10:00:00Z',
    updatedAt: '2025-10-10T12:00:00Z',
    author: { id: '42', name: 'Team' },
    content: '<p>Release notes and highlights.</p>',
    status: 'published',
    isPublic: true,
    tags: ['updates', 'alpha'],
  },
  prev: null,
  next: {
    id: 2,
    slug: 'second-post',
    title: 'Second Post',
    summary: null,
    coverUrl: null,
    publishAt: '2025-10-08T09:00:00Z',
    updatedAt: '2025-10-08T09:00:00Z',
    author: { id: '99', name: 'Engineering' },
  },
};

describe('Public dev blog', () => {
  beforeEach(() => {
    cy.intercept('POST', '/v1/metrics/rum', { statusCode: 204, body: {} }).as('rumEvent');

    cy.intercept('GET', /\/v1\/nodes\/dev-blog\?.*/, (req) => {
      const url = new URL(req.url, 'http://localhost');
      const tags = url.searchParams.getAll('tag');
      if (tags.includes('updates')) {
        req.reply({ statusCode: 200, body: filteredResponse });
      } else {
        req.reply({ statusCode: 200, body: listResponse });
      }
    }).as('getDevBlogList');

    cy.intercept('GET', '/v1/nodes/dev-blog/first-post', { statusCode: 200, body: detailResponse }).as('getDevBlogPost');
  });

  it('navigates through list filters and opens a post', () => {
    cy.visit('/dev-blog');
    cy.wait('@getDevBlogList');

    cy.contains('h1', 'Дев-блог: новости и обновления').should('be.visible');
    cy.contains('button', 'Сбросить фильтры').should('be.disabled');
    cy.contains('First Post').should('be.visible');

    cy.contains('button', '#updates').click();
    cy.wait('@getDevBlogList');
    cy.contains('Second Post').should('not.exist');
    cy.contains('button', 'Сбросить фильтры').should('not.be.disabled');

    cy.contains('First Post').click();
    cy.wait('@getDevBlogPost');

    cy.contains('h1', 'First Post').should('be.visible');
    cy.contains('section', 'Поделиться постом').should('be.visible');
    cy.get('meta[property="og:title"]').should('have.attr', 'content', 'First Post');
    cy.title().should('contain', 'First Post');
  });
});

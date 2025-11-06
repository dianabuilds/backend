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
  pinned?: boolean | null;
  shared_bindings?: Array<Record<string, unknown>>;
  default_locale?: string | null;
  available_locales?: string[] | null;
  localized_slugs?: Record<string, string> | null;
  locales?: Array<{
    locale: string;
    slug: string;
    status?: string | null;
    title?: string | null;
    description?: string | null;
  }> | null;
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
  shared_bindings?: Array<Record<string, unknown>>;
  locales?: Record<
    string,
    {
      data?: Record<string, unknown>;
      meta?: Record<string, unknown>;
      status?: string | null;
      slug?: string | null;
      title?: string | null;
    }
  >;
};

type PageHistoryEntry = {
  id: string;
  page_id: string;
  version: number;
  data: Record<string, unknown>;
  meta: Record<string, unknown>;
  comment?: string | null;
  diff?: Array<Record<string, unknown>> | null;
  published_at?: string | null;
  published_by?: string | null;
  shared_bindings?: Array<Record<string, unknown>>;
};

type AuditEntry = {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor?: string | null;
  created_at: string;
  snapshot?: Record<string, unknown> | null;
};

type MetricsResponse = {
  page_id: string;
  period: string;
  range: { start: string; end: string };
  previous_range?: { start: string; end: string };
  status: string;
  source_lag_ms?: number | null;
  metrics: Record<string, { value: number | null; delta?: number | null; trend?: number[] | null; unit?: string | null }>;
  alerts: Array<Record<string, unknown>>;
};

type DraftDiff = {
  draft_version: number;
  published_version?: number | null;
  diff: Array<Record<string, unknown>>;
};

type SaveDraftRequestBody = {
  version: number;
  data: Record<string, unknown>;
  meta: Record<string, unknown>;
  locales?: Record<
    string,
    {
      data?: Record<string, unknown>;
      meta?: Record<string, unknown>;
      status?: string | null;
      slug?: string | null;
      title?: string | null;
    }
  >;
  review_status?: string | null;
  comment?: string | null;
};

const NEW_PAGE_ID = 'page-new';
const BASE_NOW = '2025-10-30T10:00:00Z';

function decodePageId(url: string, pattern: RegExp): string | null {
  const match = pattern.exec(url);
  if (!match || !match[1]) {
    return null;
  }
  try {
    return decodeURIComponent(match[1]);
  } catch {
    return match[1];
  }
}

describe('Site editor publish flow', () => {
  const existingPages: PageSummary[] = [
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
      default_locale: 'ru',
      available_locales: ['ru'],
      localized_slugs: { ru: '' },
      locales: [
        {
          locale: 'ru',
          slug: '',
          status: 'published',
          title: 'Главная страница',
        },
      ],
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
      default_locale: 'ru',
      available_locales: ['ru'],
      localized_slugs: { ru: 'help' },
      locales: [
        {
          locale: 'ru',
          slug: 'help',
          status: 'draft',
          title: 'Справка',
        },
      ],
    },
  ];

  const existingDrafts = new Map<string, PageDraft>([
    [
      'page-home',
      {
        page_id: 'page-home',
        version: 14,
        data: { locales: { ru: { blocks: [] } }, shared: {} },
        meta: { locales: { ru: { title: 'Главная страница', slug: '', status: 'ready' } }, shared: {} },
        review_status: 'none',
        updated_at: '2025-10-25T09:00:00Z',
        updated_by: 'editor@caves.dev',
        locales: {
          ru: {
            data: { blocks: [] },
            meta: { title: 'Главная страница' },
            status: 'ready',
            slug: '',
            title: 'Главная страница',
          },
        },
      },
    ],
    [
      'page-help',
      {
        page_id: 'page-help',
        version: 7,
        data: { locales: { ru: { blocks: [] } }, shared: {} },
        meta: { locales: { ru: { title: 'Справка', slug: 'help', status: 'draft' } }, shared: {} },
        review_status: 'pending',
        updated_at: '2025-10-24T11:30:00Z',
        updated_by: 'editor@caves.dev',
        locales: {
          ru: {
            data: { blocks: [] },
            meta: { title: 'Справка' },
            status: 'draft',
            slug: 'help',
            title: 'Справка',
          },
        },
      },
    ],
  ]);

  const existingHistory = new Map<string, PageHistoryEntry[]>([
    [
      'page-home',
      [
        {
          id: 'version-12',
          page_id: 'page-home',
          version: 12,
          data: { blocks: [] },
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
    ],
    [
      'page-help',
      [],
    ],
  ]);

  const existingAudit = new Map<string, AuditEntry[]>([
    [
      'page-home',
      [
        {
          id: 'audit-home-1',
          entity_type: 'page',
          entity_id: 'page-home',
          action: 'publish',
          actor: 'editor@caves.dev',
          created_at: '2025-10-25T10:00:05Z',
          snapshot: { version: 12, comment: 'Второй релиз' },
        },
      ],
    ],
    [
      'page-help',
      [
        {
          id: 'audit-help-1',
          entity_type: 'page',
          entity_id: 'page-help',
          action: 'create_draft',
          actor: 'support@caves.dev',
          created_at: '2025-10-24T11:30:00Z',
          snapshot: { version: 7, comment: 'Черновик c обновлениями' },
        },
      ],
    ],
  ]);

  const existingDiffs = new Map<string, DraftDiff>([
    [
      'page-home',
      {
        draft_version: 14,
        published_version: 12,
        diff: [],
      },
    ],
    [
      'page-help',
      {
        draft_version: 7,
        published_version: 5,
        diff: [],
      },
    ],
  ]);

  const existingMetrics = new Map<string, MetricsResponse>([
    [
      'page-home',
      {
        page_id: 'page-home',
        period: '7d',
        range: { start: '2025-10-18T00:00:00Z', end: '2025-10-25T00:00:00Z' },
        previous_range: { start: '2025-10-11T00:00:00Z', end: '2025-10-18T00:00:00Z' },
        status: 'ok',
        source_lag_ms: 0,
        metrics: {
          impressions: { value: 12450, delta: 5, trend: [1800, 2000, 2100, 2200, 2300, 2400, 2500] },
          clicks: { value: 1560, delta: 8, trend: [180, 190, 200, 210, 220, 230, 240] },
        },
        alerts: [],
      },
    ],
    [
      'page-help',
      {
        page_id: 'page-help',
        period: '7d',
        range: { start: '2025-10-18T00:00:00Z', end: '2025-10-25T00:00:00Z' },
        status: 'draft',
        source_lag_ms: null,
        metrics: {},
        alerts: [],
      },
    ],
  ]);

  let pageOrder: string[];
  let pageDetails: Map<string, PageSummary>;
  let pageDrafts: Map<string, PageDraft>;
  let pageHistory: Map<string, PageHistoryEntry[]>;
  let pageAudit: Map<string, AuditEntry[]>;
  let pageDiffs: Map<string, DraftDiff>;
  let pageMetrics: Map<string, MetricsResponse>;

  const getHistoryResponse = (pageId: string) => {
    const entries = pageHistory.get(pageId) ?? [];
    return {
      items: entries,
      total: entries.length,
      limit: 10,
      offset: 0,
    };
  };

  const getAuditResponse = (pageId: string) => {
    const items = pageAudit.get(pageId) ?? [];
    return {
      items,
      total: items.length,
      limit: 10,
      offset: 0,
    };
  };

  const createMetrics = (pageId: string): MetricsResponse => ({
    page_id: pageId,
    period: '7d',
    range: { start: '2025-10-23T00:00:00Z', end: '2025-10-30T00:00:00Z' },
    previous_range: { start: '2025-10-16T00:00:00Z', end: '2025-10-23T00:00:00Z' },
    status: 'draft',
    source_lag_ms: 0,
    metrics: {
      impressions: { value: 0, delta: 0, trend: [] },
      clicks: { value: 0, delta: 0, trend: [] },
    },
    alerts: [],
  });

  beforeEach(() => {
    pageOrder = existingPages.map((page) => page.id);
    pageDetails = new Map(existingPages.map((page) => [page.id, { ...page }]));
    pageDrafts = new Map(Array.from(existingDrafts.entries()).map(([key, value]) => [key, { ...value }]));
    pageHistory = new Map(Array.from(existingHistory.entries()).map(([key, value]) => [key, value.map((entry) => ({ ...entry }))]));
    pageAudit = new Map(Array.from(existingAudit.entries()).map(([key, value]) => [key, value.map((entry) => ({ ...entry }))]));
    pageDiffs = new Map(Array.from(existingDiffs.entries()).map(([key, value]) => [key, { ...value }]));
    pageMetrics = new Map(Array.from(existingMetrics.entries()).map(([key, value]) => [key, { ...value }]));

    cy.intercept('POST', '/v1/metrics/rum', { statusCode: 204, body: {} }).as('rumEvent');
    cy.intercept('GET', '/v1/users/me', {
      user: {
        id: 'admin-1',
        email: 'editor@caves.dev',
        roles: ['editor', 'admin'],
      },
    }).as('getCurrentUser');

    cy.intercept('GET', '/v1/site/pages*', (req) => {
      const url = new URL(req.url, 'http://localhost');
      const statusFilter = url.searchParams.get('status');
      const draftFilter = url.searchParams.get('has_draft');
      const localeFilter = url.searchParams.get('locale');
      const pinnedFilter = url.searchParams.get('pinned');

      let items = pageOrder
        .map((id) => pageDetails.get(id))
        .filter((item): item is PageSummary => Boolean(item));

      if (statusFilter) {
        items = items.filter((item) => item.status === statusFilter);
      }
      if (draftFilter != null) {
        const expected = draftFilter === 'true';
        items = items.filter((item) => (expected ? pageDrafts.has(item.id) : !pageDrafts.has(item.id)));
      }
      if (localeFilter) {
        items = items.filter((item) => item.locale === localeFilter);
      }
      if (pinnedFilter != null) {
        const shouldBePinned = pinnedFilter === 'true';
        items = items.filter((item) => Boolean(item.pinned) === shouldBePinned);
      }

      req.reply({
        statusCode: 200,
        body: {
          items,
          page: 1,
          page_size: 20,
          total: items.length,
        },
      });
    }).as('getSitePages');

    cy.intercept('GET', /\/v1\/site\/pages\/[^/]+$/, (req) => {
      const pageId = decodePageId(req.url, /\/v1\/site\/pages\/([^/]+)$/);
      const summary = pageId ? pageDetails.get(pageId) : undefined;
      if (pageId === NEW_PAGE_ID) {
        req.alias = 'getNewPage';
      }
      req.reply({
        statusCode: summary ? 200 : 404,
        body: summary ?? { message: 'Page not found' },
      });
    });

    cy.intercept('GET', /\/v1\/site\/pages\/[^/]+\/draft$/, (req) => {
      const pageId = decodePageId(req.url, /\/v1\/site\/pages\/([^/]+)\/draft$/);
      const draft = pageId ? pageDrafts.get(pageId) : undefined;
      if (pageId === NEW_PAGE_ID) {
        req.alias = 'getNewDraft';
      }
      req.reply({
        statusCode: 200,
        body: draft ?? null,
      });
    });

    cy.intercept('GET', /\/v1\/site\/pages\/[^/]+\/draft\/diff.*$/, (req) => {
      const pageId = decodePageId(req.url, /\/v1\/site\/pages\/([^/]+)\/draft\/diff/);
      const diff = pageId ? pageDiffs.get(pageId) : undefined;
      if (pageId === NEW_PAGE_ID) {
        req.alias = 'getNewDiff';
      }
      req.reply({
        statusCode: 200,
        body: diff ?? { draft_version: 0, published_version: null, diff: [] },
      });
    });

    cy.intercept('GET', /\/v1\/site\/pages\/[^/]+\/history.*$/, (req) => {
      const pageId = decodePageId(req.url, /\/v1\/site\/pages\/([^/]+)\/history/);
      if (pageId === NEW_PAGE_ID) {
        req.alias = 'getNewHistory';
      }
      req.reply({
        statusCode: 200,
        body: pageId ? getHistoryResponse(pageId) : getHistoryResponse('page-home'),
      });
    });

    cy.intercept('GET', /\/v1\/site\/pages\/[^/]+\/metrics.*$/, (req) => {
      const pageId = decodePageId(req.url, /\/v1\/site\/pages\/([^/]+)\/metrics/);
      if (pageId === NEW_PAGE_ID) {
        req.alias = 'getNewMetrics';
      }
      const metrics = pageId ? pageMetrics.get(pageId) : undefined;
      req.reply({
        statusCode: 200,
        body: metrics ?? createMetrics(pageId ?? 'page-home'),
      });
    });

    cy.intercept('GET', /\/v1\/site\/audit.*$/, (req) => {
      const url = new URL(req.url, 'http://localhost');
      const entityId = url.searchParams.get('entity_id') ?? '';
      if (entityId === NEW_PAGE_ID) {
        req.alias = 'getNewAudit';
      }
      req.reply({
        statusCode: 200,
        body: getAuditResponse(entityId || 'page-home'),
      });
    });

    cy.intercept('GET', /\/v1\/site\/global-blocks.*$/, {
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
    });

    cy.intercept('GET', /\/v1\/site\/global-blocks\/[^/]+$/, {
      block: null,
    });

    cy.intercept('POST', '/v1/site/pages', (req) => {
      const { slug, title, type, locale, owner, pinned } = req.body as {
        slug: string;
        title: string;
        type: string;
        locale?: string;
        owner?: string;
        pinned?: boolean;
      };

      const normalizedSlug = (slug || '').startsWith('/') ? slug : `/${slug ?? ''}`;
      const normalizedLocale = (locale ?? 'ru').toLowerCase();
      const primarySlug = normalizedSlug.replace(/^\//, '');
      const createdPage: PageSummary = {
        id: NEW_PAGE_ID,
        slug: normalizedSlug,
        title,
        type,
        status: 'draft',
        locale: normalizedLocale,
        owner: owner ?? null,
        updated_at: BASE_NOW,
        published_version: null,
        draft_version: 1,
        has_pending_review: false,
        pinned: Boolean(pinned),
        shared_bindings: [],
        default_locale: normalizedLocale,
        available_locales: [normalizedLocale],
        localized_slugs: { [normalizedLocale]: primarySlug },
        locales: [
          {
            locale: normalizedLocale,
            slug: primarySlug,
            status: 'draft',
            title,
          },
        ],
      };

      const createdDraft: PageDraft = {
        page_id: NEW_PAGE_ID,
        version: 1,
        data: { locales: { [normalizedLocale]: { blocks: [] } }, shared: {} },
        meta: {
          locales: {
            [normalizedLocale]: {
              title,
              slug: primarySlug,
              status: 'draft',
            },
          },
          shared: {},
        },
        review_status: 'none',
        updated_at: BASE_NOW,
        updated_by: 'editor@caves.dev',
        shared_bindings: [],
        locales: {
          [normalizedLocale]: {
            data: { blocks: [] },
            meta: { title },
            status: 'draft',
            slug: primarySlug,
            title,
          },
        },
      };

      pageDetails.set(NEW_PAGE_ID, createdPage);
      pageDrafts.set(NEW_PAGE_ID, createdDraft);
      pageHistory.set(NEW_PAGE_ID, []);
      pageAudit.set(NEW_PAGE_ID, [
        {
          id: 'audit-new-1',
          entity_type: 'page',
          entity_id: NEW_PAGE_ID,
          action: 'create',
          actor: 'editor@caves.dev',
          created_at: BASE_NOW,
          snapshot: { title, slug: normalizedSlug, type },
        },
      ]);
      pageDiffs.set(NEW_PAGE_ID, {
        draft_version: 1,
        published_version: null,
        diff: [],
      });
      pageMetrics.set(NEW_PAGE_ID, createMetrics(NEW_PAGE_ID));
      pageOrder = [NEW_PAGE_ID, ...pageOrder.filter((id) => id !== NEW_PAGE_ID)];

      req.reply({
        statusCode: 200,
        body: createdPage,
      });
    }).as('createPage');

    cy.intercept('POST', `/v1/site/pages/${NEW_PAGE_ID}/draft/validate`, (req) => {
      req.alias = 'validateDraft';
      const body = req.body as SaveDraftRequestBody;
      req.reply({
        statusCode: 200,
        body: {
          valid: true,
          data: body.data ?? {},
          meta: body.meta ?? {},
        },
      });
    });

    cy.intercept('PUT', `/v1/site/pages/${NEW_PAGE_ID}/draft`, (req) => {
      req.alias = 'saveDraft';
      const body = req.body as SaveDraftRequestBody;
      const currentDraft = pageDrafts.get(NEW_PAGE_ID);
      const nextVersion = (body.version ?? currentDraft?.version ?? 1) + 1;
      const updatedDraft: PageDraft = {
        page_id: NEW_PAGE_ID,
        version: nextVersion,
        data: body.data ?? { locales: {} },
        meta: body.meta ?? { locales: {} },
        review_status: body.review_status ?? currentDraft?.review_status ?? 'none',
        updated_at: '2025-10-30T10:03:00Z',
        updated_by: 'editor@caves.dev',
        locales: body.locales ?? currentDraft?.locales ?? {},
        shared_bindings: currentDraft?.shared_bindings ?? [],
      };
      pageDrafts.set(NEW_PAGE_ID, updatedDraft);

      const summary = pageDetails.get(NEW_PAGE_ID);
      if (summary) {
        const localizedSlugs = { ...(summary.localized_slugs ?? {}) };
        const localeEntries = (summary.locales ?? []).map((entry) => ({ ...entry }));
        const localeKeys = Object.keys(body.locales ?? {});
        localeKeys.forEach((localeCode) => {
          const entry = body.locales?.[localeCode] ?? {};
          const slugValue =
            typeof entry?.slug === 'string'
              ? entry.slug
              : localizedSlugs[localeCode] ?? '';
          const titleValue =
            typeof entry?.title === 'string'
              ? entry.title
              : localeEntries.find((locale) => locale.locale === localeCode)?.title ?? summary.title;
          const statusValue =
            typeof entry?.status === 'string'
              ? entry.status
              : localeEntries.find((locale) => locale.locale === localeCode)?.status ?? 'draft';

          if (slugValue) {
            localizedSlugs[localeCode] = slugValue;
          }
          const localePayload = {
            locale: localeCode,
            slug: slugValue,
            status: statusValue,
            title: titleValue,
          };
          const existingIndex = localeEntries.findIndex((item) => item.locale === localeCode);
          if (existingIndex >= 0) {
            localeEntries[existingIndex] = localePayload;
          } else {
            localeEntries.push(localePayload);
          }
        });
        const nextAvailableLocales = Array.from(
          new Set([...(summary.available_locales ?? []), ...Object.keys(body.locales ?? {})]),
        );
        const defaultLocale = summary.default_locale ?? localeKeys[0] ?? 'ru';
        const defaultSlugValue = localizedSlugs[defaultLocale] ?? summary.slug.replace(/^\//, '');
        const canonicalSlug = defaultLocale === 'ru'
          ? `/${defaultSlugValue}`
          : `/${defaultLocale}/${defaultSlugValue}`;
        pageDetails.set(NEW_PAGE_ID, {
          ...summary,
          slug: canonicalSlug,
          available_locales: nextAvailableLocales,
          localized_slugs: localizedSlugs,
          locales: localeEntries,
        });
      }

      pageDiffs.set(NEW_PAGE_ID, {
        draft_version: nextVersion,
        published_version: pageDetails.get(NEW_PAGE_ID)?.published_version ?? null,
        diff: [],
      });

      req.reply({
        statusCode: 200,
        body: updatedDraft,
      });
    });

    cy.intercept('POST', `/v1/site/pages/${NEW_PAGE_ID}/preview`, (req) => {
      const { locale: requestedLocale = 'ru' } = req.body as { locale?: string };
      const summary = pageDetails.get(NEW_PAGE_ID);
      const draft = pageDrafts.get(NEW_PAGE_ID);
      const effectiveLocale = (requestedLocale ?? summary?.default_locale ?? 'ru').toLowerCase();
      const draftDataLocales =
        ((draft?.data as { locales?: Record<string, { blocks?: unknown[] }> })?.locales) ?? {};
      const draftMetaLocales =
        ((draft?.meta as { locales?: Record<string, Record<string, unknown>> })?.locales) ?? {};
      const localeMeta = draft?.locales?.[effectiveLocale] ?? {
        slug: summary?.localized_slugs?.[effectiveLocale] ?? '',
        title: summary?.locales?.find((entry) => entry.locale === effectiveLocale)?.title ?? summary?.title ?? '',
      };
      const slugPath =
        effectiveLocale === 'ru'
          ? `/${localeMeta?.slug ?? 'promo-autumn'}`
          : `/${effectiveLocale}/${localeMeta?.slug ?? 'promo-autumn-en'}`;
      req.alias = `generatePreview-${effectiveLocale}`;

      req.reply({
        statusCode: 200,
        body: {
          page: summary,
          draft_version: draft?.version ?? 1,
          published_version: summary?.published_version ?? null,
          requested_version: draft?.version ?? 1,
          version_mismatch: false,
          layouts: {
            desktop: {
              layout: 'desktop',
              generated_at: '2025-10-30T10:02:00Z',
              data: draft?.data ?? { locales: {} },
              meta: draft?.meta ?? { locales: {} },
              payload: {
                locale: effectiveLocale,
                slug: slugPath,
                title: localeMeta?.title ?? summary?.title ?? 'Предпросмотр',
                blocks: draftDataLocales[effectiveLocale]?.blocks ?? [],
                meta: draftMetaLocales[effectiveLocale] ?? {},
                fallbacks: [],
              },
            },
          },
        },
      });
    });

    cy.intercept('POST', `/v1/site/pages/${NEW_PAGE_ID}/publish`, (req) => {
      req.alias = 'publishPage';
      const { locales: localesRequest, comment } = req.body as { locales?: string[]; comment?: string };
      const publishLocales = Array.isArray(localesRequest) && localesRequest.length
        ? localesRequest.map((locale) => locale.toLowerCase())
        : ['ru'];
      expect(publishLocales).to.include('ru');

      const summary = pageDetails.get(NEW_PAGE_ID);
      const draft = pageDrafts.get(NEW_PAGE_ID);

      const publishTimestamp = '2025-10-30T10:05:00Z';
      const publishedVersion: PageHistoryEntry = {
        id: 'version-1',
        page_id: NEW_PAGE_ID,
        version: 1,
        data: draft?.data ?? { locales: {} },
        meta: draft?.meta ?? { locales: {} },
        comment: comment ?? 'Первый релиз',
        diff: [],
        published_at: publishTimestamp,
        published_by: 'editor@caves.dev',
        shared_bindings: [],
      };

      pageHistory.set(NEW_PAGE_ID, [publishedVersion]);
      pageAudit.set(NEW_PAGE_ID, [
        ...(pageAudit.get(NEW_PAGE_ID) ?? []),
        {
          id: 'audit-new-2',
          entity_type: 'page',
          entity_id: NEW_PAGE_ID,
          action: 'publish',
          actor: 'editor@caves.dev',
          created_at: publishTimestamp,
          snapshot: { version: 1, locales: publishLocales },
        },
      ]);

      const nextDraftVersion = (draft?.version ?? 1) + 1;
      pageDrafts.set(NEW_PAGE_ID, {
        page_id: NEW_PAGE_ID,
        version: nextDraftVersion,
        data: draft?.data ?? { locales: {} },
        meta: draft?.meta ?? { locales: {} },
        review_status: 'none',
        updated_at: '2025-10-30T10:06:00Z',
        updated_by: 'editor@caves.dev',
        shared_bindings: draft?.shared_bindings ?? [],
        locales: draft?.locales ?? {},
      });

      pageDiffs.set(NEW_PAGE_ID, {
        draft_version: nextDraftVersion,
        published_version: 1,
        diff: [],
      });

      if (summary) {
        const localizedSlugs = { ...(summary.localized_slugs ?? {}) };
        const nextLocales = new Map<string, PageSummary['locales'][number]>();
        (summary.locales ?? []).forEach((entry) => {
          nextLocales.set(entry.locale, { ...entry });
        });
        publishLocales.forEach((localeCode) => {
          const draftLocale = draft?.locales?.[localeCode];
          const slugValue =
            typeof draftLocale?.slug === 'string'
              ? draftLocale.slug
              : localizedSlugs[localeCode] ?? '';
          if (slugValue) {
            localizedSlugs[localeCode] = slugValue;
          }
          const titleValue =
            typeof draftLocale?.title === 'string'
              ? draftLocale.title
              : summary.title;
          nextLocales.set(localeCode, {
            locale: localeCode,
            slug: slugValue,
            status: 'published',
            title: titleValue,
          });
        });

        const nextAvailableLocales = Array.from(
          new Set([...(summary.available_locales ?? []), ...publishLocales]),
        );
        const defaultLocale = summary.default_locale ?? publishLocales[0] ?? 'ru';
        const defaultSlugValue = localizedSlugs[defaultLocale] ?? summary.slug.replace(/^\//, '');
        const canonicalSlug = defaultLocale === 'ru'
          ? `/${defaultSlugValue}`
          : `/${defaultLocale}/${defaultSlugValue}`;

        pageDetails.set(NEW_PAGE_ID, {
          ...summary,
          slug: canonicalSlug,
          status: 'published',
          draft_version: nextDraftVersion,
          published_version: 1,
          updated_at: publishTimestamp,
          available_locales: nextAvailableLocales,
          localized_slugs: localizedSlugs,
          locales: Array.from(nextLocales.values()),
        });
      }

      req.reply({
        statusCode: 200,
        body: publishedVersion,
      });
    });
  });

  it('creates a page, previews it and publishes the changes', () => {
    cy.visit('/management/site-editor');
    cy.wait(['@getCurrentUser', '@getSitePages', '@rumEvent']);

    cy.contains('button', 'Создать страницу').click();

    cy.contains('label', 'Название').find('input').clear().type('Новая промо-страница');
    cy.contains('label', 'Слаг').find('input').clear().type('promo-autumn').blur();
    cy.contains('label', 'Тип').find('select').select('Лэндинг');
    cy.contains('label', 'Локаль').find('select').select('Русский (ru)');
    cy.contains('label', 'Ответственный').find('input').clear().type('growth');

    cy.contains('button', 'Создать').click();
    cy.wait('@createPage');

    cy.get('[data-testid="site-page-detail"]')
      .should('contain', 'Новая промо-страница')
      .and('contain', '/promo-autumn')
      .and('contain', 'Черновик');

    cy.contains('[data-testid="site-page-item"]', 'Новая промо-страница')
      .should('be.visible')
      .within(() => {
        cy.contains('button', 'Открыть').click();
      });

    cy.wait('@getNewPage');
    cy.wait('@getNewDraft');
    cy.wait('@getNewHistory');
    cy.wait('@getNewAudit');
    cy.wait('@getNewDiff');
    cy.wait('@getNewMetrics');

    cy.url().should('include', `/management/site-editor/pages/${NEW_PAGE_ID}`);
    cy.contains('h1', 'Новая промо-страница').should('be.visible');
    cy.contains('Slug').parent().should('contain', '/promo-autumn');

    cy.contains('summary', 'Основная информация').click();

    cy.contains('label', 'Название')
      .find('input')
      .clear()
      .type('Новая промо-страница');
    cy.contains('label', 'Slug')
      .find('input')
      .clear()
      .type('promo-autumn')
      .blur();
    cy.contains('label', 'Статус локали')
      .find('select')
      .select('Готов к публикации');

    cy.contains('button', 'Сохранить черновик').click();
    cy.wait('@validateDraft');
    cy.wait('@saveDraft');

    cy.contains('button', 'Добавить английский').click();
    cy.contains('button', 'Английский (en)').click();

    cy.contains('label', 'Название')
      .find('input')
      .clear()
      .type('Autumn Promo Page');
    cy.contains('label', 'Slug')
      .find('input')
      .clear()
      .type('promo-autumn-en')
      .blur();
    cy.contains('label', 'Статус локали')
      .find('select')
      .select('Готов к публикации');

    cy.contains('button', 'Сохранить черновик').click();
    cy.wait('@validateDraft');
    cy.wait('@saveDraft');

    cy.contains('button', 'Русский (ru)').click();
    cy.contains('button', 'Предпросмотр').click();
    cy.contains('button', 'Обновить предпросмотр').click();

    cy.wait('@generatePreview-ru').then((interception) => {
      expect(interception?.request?.body?.locale).to.eq('ru');
      expect(interception?.request?.body?.locales?.ru?.slug).to.eq('promo-autumn');
      expect(interception?.response?.body?.layouts?.desktop?.payload?.slug).to.eq('/promo-autumn');
    });
    cy.get('[data-testid="site-page-preview-success"]').should('be.visible');

    cy.contains('button', 'Английский (en)').click();
    cy.contains('button', 'Обновить предпросмотр').click();

    cy.wait('@generatePreview-en').then((interception) => {
      expect(interception?.request?.body?.locale).to.eq('en');
      expect(interception?.request?.body?.locales?.en?.slug).to.eq('promo-autumn-en');
      expect(interception?.response?.body?.layouts?.desktop?.payload?.slug).to.eq('/en/promo-autumn-en');
    });
    cy.get('[data-testid="site-page-preview-success"]').should('be.visible');

    cy.contains('button', 'Опубликовать').click();
    cy.contains('[role="dialog"]', 'Опубликовать страницу')
      .should('be.visible')
      .within(() => {
        cy.contains('button', 'Опубликовать').click();
      });

    cy.wait('@publishPage').then((interception) => {
      expect(interception?.request?.body?.locales).to.include.members(['ru', 'en']);
    });
    cy.wait('@getNewPage');
    cy.wait('@getNewDraft');
    cy.wait('@getNewHistory');
    cy.wait('@getNewAudit');

    cy.contains('Страница опубликована').should('be.visible');
    cy.contains('Публикация').parent().should('contain', 'v1');

    cy.contains('Назад к списку страниц').click();
    cy.wait('@getSitePages');

    cy.contains('[data-testid="site-page-item"]', 'Новая промо-страница')
      .should('contain', 'Опубликована')
      .and('contain', '/promo-autumn');
  });
});

import { describe, expect, it } from 'vitest';

import type { SitePagePreviewResponse } from '@shared/types/management';

import { mapPreviewResponseToHomeResponse } from '../pages';

const basePreviewResponse: SitePagePreviewResponse = {
  page: {
    id: 'page-1',
    slug: '/sample',
    type: 'landing',
    status: 'draft',
    title: 'Sample',
    locale: 'ru',
    default_locale: 'ru',
    available_locales: ['ru'],
    localized_slugs: { ru: '/sample' },
    locales: null,
    bindings: [],
    shared_bindings: [],
    has_pending_review: null,
    pinned: null,
    published_version: null,
    draft_version: 1,
    owner: null,
    updated_at: null,
  },
  draft_version: 1,
  published_version: null,
  requested_version: null,
  version_mismatch: false,
  default_locale: 'ru',
  available_locales: ['ru'],
  localized_slugs: { ru: '/sample' },
  bindings: [],
  shared: {},
  locales: {},
  preview: {
    page_id: 'page-1',
    slug: '/sample',
    locale: 'ru',
    title: 'Sample',
    type: 'landing',
    version: 1,
    generated_at: '2025-11-01T00:00:00Z',
    meta: {},
    payload: {
      locale: 'ru',
      blocks: [],
      fallbacks: [],
      meta: {},
      version: 1,
    },
    blocks: [],
    fallbacks: [],
  },
  preview_variants: [],
  layouts: {},
  meta_localized: undefined,
};

describe('siteEditor pages helpers', () => {
  it('extracts HomeResponse from main preview payload', () => {
    const payload = mapPreviewResponseToHomeResponse(basePreviewResponse);
    expect(payload).not.toBeNull();
    expect(payload?.blocks).toEqual([]);
  });

  it('prefers specified layout variant when provided', () => {
    const response: SitePagePreviewResponse = {
      ...basePreviewResponse,
      preview: {
        ...basePreviewResponse.preview!,
        payload: {
          locale: 'ru',
          blocks: [{ id: 'primary', type: 'hero', items: [] }],
          fallbacks: [],
          meta: {},
          version: 1,
        },
      },
      preview_variants: [
        {
          layout: 'mobile',
          response: {
            page_id: 'page-1',
            slug: '/sample',
            locale: 'ru',
            title: 'Sample',
            type: 'landing',
            version: 1,
            generated_at: '2025-11-01T00:00:00Z',
            meta: {},
            payload: {
              locale: 'ru',
              blocks: [{ id: 'primary', type: 'hero', items: [] }],
              fallbacks: [],
              meta: {},
              version: 1,
            },
            blocks: [{ id: 'primary', type: 'hero', items: [] }],
            fallbacks: [],
          },
        },
      ],
      layouts: {
        desktop: {
          layout: 'desktop',
          generated_at: '2025-11-01T00:00:00Z',
          data: {},
          meta: {},
          payload: {},
        },
      },
    };

    const payload = mapPreviewResponseToHomeResponse(response, { layout: 'mobile' });
    expect(payload).not.toBeNull();
    expect(payload?.blocks).toHaveLength(1);
    expect(payload?.blocks?.[0]?.type).toBe('hero');
  });
});

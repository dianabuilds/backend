import { describe, expect, it } from 'vitest';

import {
  normalizeBlockTemplate,
  normalizeDraft,
  normalizePage,
  normalizePreviewResponse,
} from '../normalizers';

describe('siteEditor normalizers', () => {
  it('normalizes bindings inside page summary', () => {
    const result = normalizePage({
      id: 'page-1',
      slug: '/home',
      title: 'Home',
      type: 'landing',
      status: 'draft',
      locale: 'ru',
      bindings: [
        {
          key: 'header',
          section: 'header',
          block_id: 'block-1',
          title: 'Header',
          status: 'published',
          locale: 'ru',
          default_locale: 'ru',
          available_locales: ['ru'],
          requires_publisher: false,
          published_version: 1,
          draft_version: 2,
          has_draft_binding: true,
          last_published_at: '2025-10-31T20:00:00Z',
          updated_at: '2025-10-31T20:00:00Z',
          updated_by: 'editor@example.com',
          scope: 'shared',
        },
      ],
    });

    expect(result).not.toBeNull();
    expect(result?.shared_bindings).toHaveLength(1);
    expect(result?.bindings).toEqual(result?.shared_bindings);
    expect(result?.shared_bindings?.[0]).toMatchObject({
      key: 'header',
      block_id: 'block-1',
      locale: 'ru',
      requires_publisher: false,
    });
  });

  it('normalizes block template catalog fields', () => {
    const result = normalizeBlockTemplate({
      id: 'tpl-hero',
      key: 'hero',
      title: 'Hero',
      section: 'hero',
      status: 'available',
      description: 'Hero block',
      default_locale: 'ru',
      available_locales: ['ru', 'en'],
      default_data: { layout: { variant: 'full' } },
      default_meta: { requires_publisher: true },
      block_type: 'hero',
      category: 'hero',
      sources: ['manual', 'auto'],
      surfaces: ['desktop'],
      owners: ['team_public_site'],
      catalog_locales: ['ru'],
      documentation_url: '/docs',
      keywords: ['hero', 'promo'],
      preview_kind: 'screenshot',
      status_note: 'beta',
      requires_publisher: true,
      allow_shared_scope: true,
      allow_page_scope: false,
      shared_note: 'Shared carefully',
      key_prefix: 'hero',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-02T00:00:00Z',
    });

    expect(result).toMatchObject({
      id: 'tpl-hero',
      key: 'hero',
      section: 'hero',
      default_locale: 'ru',
      available_locales: ['ru', 'en'],
      block_type: 'hero',
      category: 'hero',
      documentation_url: '/docs',
      preview_kind: 'screenshot',
      status_note: 'beta',
      requires_publisher: true,
      allow_shared_scope: true,
      allow_page_scope: false,
      shared_note: 'Shared carefully',
      key_prefix: 'hero',
    });
    expect(result?.default_data).toEqual({ layout: { variant: 'full' } });
    expect(result?.default_meta).toEqual({ requires_publisher: true });
    expect(result?.sources).toEqual(['manual', 'auto']);
    expect(result?.surfaces).toEqual(['desktop']);
    expect(result?.owners).toEqual(['team_public_site']);
    expect(result?.catalog_locales).toEqual(['ru']);
    expect(result?.keywords).toEqual(['hero', 'promo']);

    const fallback = normalizeBlockTemplate({
      id: 'tpl-footer',
      key: 'footer',
      title: 'Footer',
      section: 'footer',
      status: 'available',
    });
    expect(fallback).toMatchObject({
      default_locale: 'ru',
      available_locales: ['ru'],
      default_data: {},
      default_meta: {},
      sources: [],
      surfaces: [],
      owners: [],
      catalog_locales: [],
      keywords: [],
      requires_publisher: false,
      allow_shared_scope: true,
      allow_page_scope: true,
    });
  });

  it('normalizes block refs inside page summary', () => {
    const result = normalizePage({
      id: 'page-refs',
      slug: '/with-shared',
      title: 'Page With Shared',
      type: 'landing',
      status: 'draft',
      locale: 'ru',
      block_refs: [
        'header-shared',
        { key: 'footer-shared', section: 'footer' },
      ],
    });

    expect(result?.block_refs).toEqual([
      { key: 'header-shared' },
      { key: 'footer-shared', section: 'footer' },
    ]);
  });

  it('normalizes block refs inside drafts', () => {
    const draft = normalizeDraft({
      page_id: 'page-refs',
      version: 5,
      data: {},
      meta: {},
      block_refs: [
        'hero-shared',
        { key: 'header-shared', section: 'header' },
      ],
    });

    expect(draft?.block_refs).toEqual([
      { key: 'hero-shared' },
      { key: 'header-shared', section: 'header' },
    ]);
  });

  it('normalizes preview response with shared bindings and layouts', () => {
    const response = normalizePreviewResponse({
      page: {
        id: 'page-42',
        slug: '/preview',
        title: 'Preview page',
        type: 'landing',
        status: 'draft',
        locale: 'ru',
        bindings: [
          {
            key: 'hero',
            section: 'hero',
            block_id: 'block-hero',
            title: 'Hero',
            status: 'draft',
            locale: 'ru',
            available_locales: ['ru'],
            requires_publisher: true,
            draft_version: 3,
            published_version: 2,
            has_draft_binding: true,
            last_published_at: '2025-10-25T12:00:00Z',
            updated_at: '2025-11-01T00:00:00Z',
            updated_by: 'designer@example.com',
            scope: 'shared',
          },
        ],
      },
      draft_version: 3,
      published_version: 2,
      requested_version: 3,
      version_mismatch: false,
      default_locale: 'ru',
      available_locales: ['ru'],
      localized_slugs: { ru: '/preview' },
      meta_localized: { ru: { title: 'Preview page' } },
      bindings: [
        {
          key: 'hero',
          section: 'hero',
          block_id: 'block-hero',
          title: 'Hero',
          status: 'draft',
          locale: 'ru',
          available_locales: ['ru'],
          requires_publisher: true,
          draft_version: 3,
          published_version: 2,
          has_draft_binding: true,
          last_published_at: '2025-10-25T12:00:00Z',
          updated_at: '2025-11-01T00:00:00Z',
          updated_by: 'designer@example.com',
          scope: 'shared',
        },
      ],
      shared: { theme: 'dark' },
      locales: {
        ru: {
          data: { blocks: [] },
          meta: { title: 'Preview page ru' },
        },
      },
      preview: {
        page_id: 'page-42',
        slug: '/preview',
        locale: 'ru',
        title: 'Preview page',
        type: 'landing',
        version: 3,
        generated_at: '2025-11-01T00:00:00Z',
        meta: {},
        payload: {},
        blocks: [],
        fallbacks: [],
      },
      preview_variants: [
        {
          layout: 'desktop',
          response: {
            page_id: 'page-42',
            slug: '/preview',
            locale: 'ru',
            title: 'Preview page',
            type: 'landing',
            version: 3,
            generated_at: '2025-11-01T00:00:00Z',
            meta: {},
            payload: { variant: 'desktop' },
            blocks: [],
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
    });

    expect(response.shared_bindings).toHaveLength(1);
    expect(response.bindings).toEqual(response.shared_bindings);
    expect(response.preview_variants).toHaveLength(1);
    expect(response.shared).toMatchObject({ theme: 'dark' });
    expect(response.locales?.ru).toMatchObject({
      meta: { title: 'Preview page ru' },
    });
  });
});

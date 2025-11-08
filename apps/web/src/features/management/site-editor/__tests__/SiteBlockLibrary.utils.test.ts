import { describe, it, expect } from 'vitest';
import type { SiteBlock } from '@shared/types/management';
import { collectLocales, pickDocumentationUrl } from '../components/SiteBlockLibrary.utils';

const BASE_BLOCK: SiteBlock = {
  id: 'block-1',
  key: 'sample-block',
  title: 'Sample block',
  section: 'hero',
  status: 'draft',
  review_status: 'none',
  requires_publisher: false,
  scope: 'shared',
  locale: null,
  default_locale: 'ru',
  available_locales: ['ru'],
  template_id: null,
  template_key: null,
  published_version: null,
  draft_version: 1,
  version: 1,
  usage_count: 0,
  comment: null,
  data: {},
  meta: {},
  updated_at: null,
  updated_by: null,
  created_at: null,
  created_by: null,
  last_used_at: null,
  has_pending_publish: null,
  extras: {},
  is_template: false,
  origin_block_id: null,
};

describe('collectLocales', () => {
  it('aggregates locale hints from block fields and avoids duplicates', () => {
    const locales = collectLocales({
      ...BASE_BLOCK,
      locale: 'ru',
      available_locales: ['ru', 'en', 'EN', 'de '],
    });
    expect(new Set(locales)).toEqual(new Set(['ru', 'en', 'de']));
  });

  it('includes locales declared inside data.meta maps', () => {
    const locales = collectLocales({
      ...BASE_BLOCK,
      locale: 'en',
      default_locale: 'ru',
      available_locales: ['ru'],
      data: {
        locales: {
          en: {},
          de: {},
        },
      },
      meta: {
        locales: {
          fr: {},
        },
      },
    });
    expect(new Set(locales)).toEqual(new Set(['en', 'ru', 'de', 'fr']));
  });
});

describe('pickDocumentationUrl', () => {
  it('prefers direct documentation_url field when present', () => {
    expect(
      pickDocumentationUrl({
        documentation_url: 'https://docs.caves.dev/blocks/header',
        meta: {},
      }),
    ).toBe('https://docs.caves.dev/blocks/header');
  });

  it('falls back to meta documentation keys, including legacy ones', () => {
    expect(
      pickDocumentationUrl({
        meta: {
          documentation_url: 'https://docs.caves.dev/blocks/footer',
        },
      }),
    ).toBe('https://docs.caves.dev/blocks/footer');

    expect(
      pickDocumentationUrl({
        meta: {
          documentation: 'https://legacy.docs/hero',
        },
      }),
    ).toBe('https://legacy.docs/hero');
  });

  it('reads nested meta.links.documentation when nothing else provided', () => {
    expect(
      pickDocumentationUrl({
        meta: {
          links: {
            documentation: 'https://docs.caves.dev/library',
          },
        },
      }),
    ).toBe('https://docs.caves.dev/library');
  });

  it('returns null when documentation link is missing', () => {
    expect(pickDocumentationUrl({ meta: {} })).toBeNull();
  });
});

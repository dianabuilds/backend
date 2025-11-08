import { describe, expect, it } from 'vitest';

import { homeDraftAdapter } from '../homeDraftAdapter';
import type { DraftData } from '../types';

describe('homeDraftAdapter', () => {
  it('normalizes site block metadata for global sources', () => {
    const raw = {
      blocks: [
        {
          id: 'hero-1',
          type: 'hero',
          enabled: true,
          source: 'global',
          key: 'hero-primary',
          block_id: 'site-block-id',
          block_title: 'Главный hero',
          block_status: 'published',
          block_review_status: 'none',
          block_requires_publisher: true,
          block_has_pending_publish: true,
          block_has_draft: true,
          block_updated_at: '2025-11-01T10:00:00Z',
          block_updated_by: 'editor@caves.dev',
          locale: 'ru',
          section: 'hero',
        },
      ],
    };

    const normalized = homeDraftAdapter.normalizeDraftData(raw);
    expect(normalized.blocks).toHaveLength(1);
    const [block] = normalized.blocks;
    expect(block.source).toBe('site');
    expect(block.siteBlockKey).toBe('hero-primary');
    expect(block.siteBlockId).toBe('site-block-id');
    expect(block.siteBlockTitle).toBe('Главный hero');
    expect(block.siteBlockStatus).toBe('published');
    expect(block.siteBlockReviewStatus).toBe('none');
    expect(block.siteBlockRequiresPublisher).toBe(true);
    expect(block.siteBlockHasPendingPublish).toBe(true);
    expect(block.siteBlockHasDraft).toBe(true);
    expect(block.siteBlockUpdatedAt).toBe('2025-11-01T10:00:00Z');
    expect(block.siteBlockUpdatedBy).toBe('editor@caves.dev');
    expect(block.siteBlockLocale).toBe('ru');
    expect(block.siteBlockSection).toBe('hero');
  });

  it('builds payload for site-attached blocks', () => {
    const draft: DraftData = {
      blocks: [
        {
          id: 'hero-1',
          type: 'hero',
          enabled: true,
          source: 'site',
          siteBlockKey: 'hero-primary',
          siteBlockId: 'site-block-id',
          siteBlockLocale: 'ru',
          siteBlockSection: 'hero',
        },
      ],
      meta: null,
      shared: {
        assignments: {},
      },
    };

    const payload = homeDraftAdapter.buildDraftPayload(draft);
    const blocks = Array.isArray(payload.data.blocks)
      ? (payload.data.blocks as Array<Record<string, unknown>>)
      : [];
    expect(blocks).toHaveLength(1);
    expect(blocks[0]).toMatchObject({
      id: 'hero-1',
      source: 'global',
      key: 'hero-primary',
      block_id: 'site-block-id',
      section: 'hero',
      locale: 'ru',
    });
  });
});

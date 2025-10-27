import { describe, it, expect } from 'vitest';

import {
  applyGlobalBlockAssignments,
  extractGlobalBlockAssignments,
} from '../utils/globalBlocks';

describe('global block helpers', () => {
  it('извлекает назначения из meta.globalBlocks', () => {
    const meta = {
      globalBlocks: [
        { type: 'global_block', reference: 'header-default', section: 'header' },
        { type: 'global_block', ref: 'footer-main', section: 'footer' },
      ],
    };

    const assignments = extractGlobalBlockAssignments(meta);

    expect(assignments).toEqual({
      header: { key: 'header-default', section: 'header' },
      footer: { key: 'footer-main', section: 'footer' },
    });
  });

  it('извлекает назначения из мета-разделов header/footer', () => {
    const meta = {
      header: { reference: 'header-alt' },
      footer: 'footer-secondary',
    };

    const assignments = extractGlobalBlockAssignments(meta);

    expect(assignments).toEqual({
      header: { key: 'header-alt', section: 'header' },
      footer: { key: 'footer-secondary', section: 'footer' },
    });
  });

  it('формирует meta c записями глобальных блоков', () => {
    const assignments = {
      header: { key: 'header-default', section: 'header' },
      footer: { key: 'footer-main', section: 'footer' },
    };

    const nextMeta = applyGlobalBlockAssignments(null, assignments);

    expect(nextMeta).toEqual({
      globalBlocks: [
        {
          type: 'global_block',
          reference: 'footer-main',
          ref: 'footer-main',
          key: 'footer-main',
          section: 'footer',
        },
        {
          type: 'global_block',
          reference: 'header-default',
          ref: 'header-default',
          key: 'header-default',
          section: 'header',
        },
      ],
      header: {
        type: 'global_block',
        reference: 'header-default',
        ref: 'header-default',
        key: 'header-default',
        section: 'header',
      },
      footer: {
        type: 'global_block',
        reference: 'footer-main',
        ref: 'footer-main',
        key: 'footer-main',
        section: 'footer',
      },
    });
  });

  it('очищает meta при отсутствии назначений', () => {
    const result = applyGlobalBlockAssignments(
      {
        header: { reference: 'header-old' },
        globalBlocks: [{ ref: 'header-old', section: 'header' }],
      },
      {},
    );

    expect(result).toBeNull();
  });
});

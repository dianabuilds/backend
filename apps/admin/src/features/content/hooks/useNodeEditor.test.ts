import { describe, expect, it } from 'vitest';
import { normalizeTags } from './useNodeEditor';

describe('normalizeTags', () => {
  it('returns strings as-is', () => {
    expect(normalizeTags(['a', 'B'])).toEqual(['a', 'B']);
  });

  it('extracts slugs from objects', () => {
    expect(normalizeTags([{ slug: 'a' }, { name: 'B' }])).toEqual(['a', 'B']);
  });

  it('reads nested tagSlugs', () => {
    expect(normalizeTags({ tagSlugs: ['x', 'y'] })).toEqual(['x', 'y']);
  });
});

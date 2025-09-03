import { describe, expect, it } from 'vitest';
import { normalizeTags } from './useNodeEditor';

describe('normalizeTags', () => {
  it('returns strings as-is', () => {
    expect(normalizeTags(['a', 'B'])).toEqual(['a', 'B']);
  });

  it('extracts slugs from objects', () => {
    expect(normalizeTags([{ slug: 'a' }, { name: 'B' }])).toEqual(['a', 'B']);
  });

  it('reads nested tags', () => {
    expect(normalizeTags({ tags: ['x', 'y'] })).toEqual(['x', 'y']);
    expect(normalizeTags({ meta: { tags: ['a'] } })).toEqual(['a']);
  });
});

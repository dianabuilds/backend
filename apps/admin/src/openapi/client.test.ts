import { describe, expectTypeOf, it } from 'vitest';

import type { NodeOut } from './';

describe('generated client', () => {
  it('NodeOut has no node_type field', () => {
    expectTypeOf<NodeOut>().not.toHaveProperty('node_type');
  });
});

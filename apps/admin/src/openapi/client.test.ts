import { expectTypeOf, describe, it } from 'vitest';
import { NodeOut } from './';

describe('generated client', () => {
  it('NodeOut has no node_type field', () => {
    expectTypeOf<NodeOut>().not.toHaveProperty('node_type');
  });
});

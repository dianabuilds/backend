export * from './list';
export * from './mutations';
export * from './authors';

import { nodesListApi } from './list';
import { nodesMutationsApi } from './mutations';
import { nodesAuthorsApi } from './authors';

export const nodesApi = {
  ...nodesListApi,
  ...nodesMutationsApi,
  ...nodesAuthorsApi,
};


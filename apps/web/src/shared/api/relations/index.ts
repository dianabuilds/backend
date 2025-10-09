export * from './overview';
export * from './strategies';

import { relationsStrategiesApi } from './strategies';
import { fetchRelationsOverview, fetchTopRelations } from './overview';

export const relationsApi = {
  fetchRelationsOverview,
  fetchTopRelations,
  ...relationsStrategiesApi,
};


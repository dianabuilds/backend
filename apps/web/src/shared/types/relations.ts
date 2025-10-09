export type RelationStrategyOverview = {
  key: string;
  weight: number;
  enabled: boolean;
  usageShare: number | null;
  links: number | null;
  updatedAt: string | null;
};

export type RelationsDiversitySnapshot = {
  coverage: number | null;
  entropy: number | null;
  gini: number | null;
};

export type RelationLink = {
  sourceId: string;
  sourceTitle: string | null;
  sourceSlug: string | null;
  targetId: string;
  targetTitle: string | null;
  targetSlug: string | null;
  score: number | null;
  algo: string | null;
  updatedAt: string | null;
};

export type RelationsOverview = {
  strategies: RelationStrategyOverview[];
  diversity: RelationsDiversitySnapshot;
  popular: Record<string, RelationLink[]>;
};

export type RelationStrategyUpdatePayload = {
  weight: number;
  enabled: boolean;
};


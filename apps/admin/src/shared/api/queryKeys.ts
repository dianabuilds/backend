export const queryKeys = {
  nodes: (params?: Record<string, unknown>) => ['nodes', params] as const,
  node: (id: number) => ['nodes', id] as const,
  worlds: ['worlds'] as const,
  worldCharacters: (worldId: string) => ['worlds', worldId, 'characters'] as const,
};

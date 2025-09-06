export const queryKeys = {
  nodes: (accountId: string, params?: Record<string, unknown>) => [
    "nodes",
    accountId,
    params,
  ] as const,
  node: (accountId: string, id: number) => ["nodes", accountId, id] as const,
  worlds: ["worlds"] as const,
  worldCharacters: (worldId: string) => ["worlds", worldId, "characters"] as const,
};

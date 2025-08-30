export const queryKeys = {
  nodes: (workspaceId: string, params?: Record<string, unknown>) => [
    "nodes",
    workspaceId,
    params,
  ] as const,
  node: (workspaceId: string, id: string) => ["nodes", workspaceId, id] as const,
  worlds: ["worlds"] as const,
  worldCharacters: (worldId: string) => ["worlds", worldId, "characters"] as const,
};

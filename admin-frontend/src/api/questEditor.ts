import { api } from "./client";

export interface VersionSummary {
  id: string;
  quest_id: string;
  number: number;
  status: string;
  created_at: string;
  released_at?: string | null;
}

export interface GraphNode {
  key: string;
  title: string;
  type?: "start" | "normal" | "end";
  content?: any;
  rewards?: any;
}

export interface GraphEdge {
  from_node_key: string;
  to_node_key: string;
  label?: string | null;
  condition?: any;
}

export interface VersionGraph {
  version: VersionSummary;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export async function createQuest(title: string): Promise<string> {
  const res = await api.post<{ id: string }>("/admin/quests/create", { title });
  return (res.data as any).id;
}

export async function createDraft(questId: string): Promise<string> {
  const res = await api.post<{ versionId: string }>(`/admin/quests/${questId}/draft`);
  return (res.data as any).versionId;
}

export async function getVersion(versionId: string): Promise<VersionGraph> {
  const res = await api.get<VersionGraph>(`/admin/quests/versions/${versionId}`);
  return res.data as VersionGraph;
}

export async function putGraph(versionId: string, graph: VersionGraph): Promise<void> {
  await api.put(`/admin/quests/versions/${versionId}/graph`, graph);
}

export async function validateVersion(versionId: string): Promise<{ ok: boolean; errors: string[]; warnings: string[] }> {
  const res = await api.post(`/admin/quests/versions/${versionId}/validate`);
  return res.data as any;
}

export async function publishVersion(versionId: string): Promise<void> {
  await api.post(`/admin/quests/versions/${versionId}/publish`);
}

export interface QuestMeta {
  id: string;
  title: string;
  subtitle?: string | null;
  description?: string | null;
  cover_image?: string | null;
  price?: number | null;
  is_premium_only?: boolean;
  allow_comments?: boolean;
  tags?: string[];
}

export async function getQuestMeta(questId: string): Promise<QuestMeta> {
  const res = await api.get<QuestMeta>(`/admin/quests/${encodeURIComponent(questId)}/meta`);
  return res.data as QuestMeta;
}

export async function updateQuestMeta(questId: string, patch: Partial<QuestMeta>): Promise<QuestMeta> {
  const res = await api.patch<QuestMeta>(`/admin/quests/${encodeURIComponent(questId)}/meta`, patch);
  return res.data as QuestMeta;
}

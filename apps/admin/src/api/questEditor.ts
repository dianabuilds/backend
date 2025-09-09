import type { QuestGraphIn,QuestOut, QuestUpdate, ValidateResult } from '../openapi';
// Local alias for the graph used by editor. Keep it broad to avoid tight coupling
// to generated types that may change naming between versions.
export type VersionGraph = unknown;
import { api } from './client';

export async function createQuest(title: string): Promise<string> {
  const res = await api.post<{ title: string }, { id: string }>(
    '/admin/quests/create',
    { title },
  );
  return res.data!.id;
}

export async function createDraft(questId: string): Promise<string> {
  const res = await api.post<unknown, { versionId: string }>(`/admin/quests/${questId}/draft`);
  return res.data!.versionId;
}

export async function getVersion(versionId: string): Promise<VersionGraph> {
  const res = await api.get<VersionGraph>(`/admin/quests/versions/${versionId}`);
  return res.data!;
}

export async function putGraph(versionId: string, graph: QuestGraphIn | VersionGraph): Promise<void> {
  await api.put(`/admin/quests/versions/${versionId}/graph`, graph);
}

export async function validateVersion(versionId: string): Promise<ValidateResult> {
  const res = await api.post<unknown, ValidateResult>(
    `/admin/quests/versions/${versionId}/validate`,
  );
  return res.data ?? { ok: true };
}

export async function publishVersion(versionId: string): Promise<void> {
  await api.post(`/admin/quests/versions/${versionId}/publish`);
}

export async function autofixVersion(versionId: string): Promise<unknown> {
  const res = await api.post<unknown>(`/admin/quests/versions/${versionId}/autofix`);
  return res.data;
}

export async function getQuestMeta(questId: string): Promise<QuestOut> {
  const res = await api.get<QuestOut>(`/admin/quests/${encodeURIComponent(questId)}/meta`);
  return res.data!;
}

export async function updateQuestMeta(questId: string, patch: QuestUpdate): Promise<QuestOut> {
  const res = await api.patch<QuestUpdate, QuestOut>(
    `/admin/quests/${encodeURIComponent(questId)}/meta`,
    patch,
  );
  return res.data!;
}

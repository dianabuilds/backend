import type {
  AutofixReport,
  QuestOut,
  QuestUpdate,
  ValidateResult,
  VersionGraphInput,
  VersionGraphOutput,
} from "../openapi";
export type { VersionGraphOutput as VersionGraph } from "../openapi";
import { api } from "./client";

export async function createQuest(title: string): Promise<string> {
  const res = await api.post<{ id: string }>("/admin/quests/create", { title });
  return res.data!.id;
}

export async function createDraft(questId: string): Promise<string> {
  const res = await api.post<{ versionId: string }>(`/admin/quests/${questId}/draft`);
  return res.data!.versionId;
}

export async function getVersion(versionId: string): Promise<VersionGraphOutput> {
  const res = await api.get<VersionGraphOutput>(
    `/admin/quests/versions/${versionId}`,
  );
  return res.data!;
}

export async function putGraph(
  versionId: string,
  graph: VersionGraphInput,
): Promise<void> {
  await api.put(`/admin/quests/versions/${versionId}/graph`, graph);
}

export async function validateVersion(
  versionId: string,
): Promise<ValidateResult> {
  const res = await api.post<ValidateResult>(
    `/admin/quests/versions/${versionId}/validate`,
  );
  return res.data!;
}

export async function publishVersion(versionId: string): Promise<void> {
  await api.post(`/admin/quests/versions/${versionId}/publish`);
}

export async function autofixVersion(
  versionId: string,
): Promise<AutofixReport> {
  const res = await api.post<AutofixReport>(
    `/admin/quests/versions/${versionId}/autofix`,
  );
  return res.data!;
}

export async function getQuestMeta(questId: string): Promise<QuestOut> {
  const res = await api.get<QuestOut>(
    `/admin/quests/${encodeURIComponent(questId)}/meta`,
  );
  return res.data!;
}

export async function updateQuestMeta(
  questId: string,
  patch: QuestUpdate,
): Promise<QuestOut> {
  const res = await api.patch<QuestOut>(
    `/admin/quests/${encodeURIComponent(questId)}/meta`,
    patch,
  );
  return res.data!;
}

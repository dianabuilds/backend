import { wsApi } from './wsApi';

export type AccessMode = 'everyone' | 'premium_only' | 'early_access';

export type PublishInfo = {
  status: string;
  published_at?: string | null;
  scheduled?: { run_at: string; access: AccessMode; status: string } | null;
};

export async function getPublishInfo(workspaceId: string, nodeId: number): Promise<PublishInfo> {
  const { data } = await wsApi.get(
    `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(String(nodeId))}/publish_info`,
  );
  return data as PublishInfo;
}

export async function publishNow(
  workspaceId: string,
  nodeId: number,
  access: AccessMode = 'everyone',
): Promise<any> {
  const { data } = await wsApi.post(
    `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(String(nodeId))}/publish`,
    { access },
  );
  return data;
}

export async function schedulePublish(
  workspaceId: string,
  nodeId: number,
  runAtISO: string,
  access: AccessMode = 'everyone',
): Promise<PublishInfo> {
  const { data } = await wsApi.post(
    `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(String(nodeId))}/schedule_publish`,
    { run_at: runAtISO, access },
  );
  return data as PublishInfo;
}

export async function cancelScheduledPublish(
  workspaceId: string,
  nodeId: number,
): Promise<{ canceled: boolean }> {
  const { data } = await wsApi.delete(
    `/admin/workspaces/${encodeURIComponent(workspaceId)}/nodes/${encodeURIComponent(String(nodeId))}/schedule_publish`,
  );
  return data as { canceled: boolean };
}

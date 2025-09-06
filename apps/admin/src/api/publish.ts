import { wsApi } from './wsApi';

export type AccessMode = 'everyone' | 'premium_only' | 'early_access';

export type PublishInfo = {
  status: string;
  published_at?: string | null;
  scheduled?: { run_at: string; access: AccessMode; status: string } | null;
};

export async function getPublishInfo(accountId: string, nodeId: number): Promise<PublishInfo> {
  const info = await wsApi.get<PublishInfo>(
    `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(nodeId))}/publish_info`,
    { accountId, account: false },
  );
  return info;
}

export async function publishNow(
  accountId: string,
  nodeId: number,
  access: AccessMode = 'everyone',
): Promise<{ ok: true } | Record<string, unknown>> {
  const res = await wsApi.post<{ access: AccessMode }, { ok: true } | Record<string, unknown>>(
    `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(nodeId))}/publish`,
    { access },
    { accountId, account: false },
  );
  return res;
}

export async function schedulePublish(
  accountId: string,
  nodeId: number,
  runAtISO: string,
  access: AccessMode = 'everyone',
): Promise<PublishInfo> {
  const info = await wsApi.post<{ run_at: string; access: AccessMode }, PublishInfo>(
    `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(nodeId))}/schedule_publish`,
    { run_at: runAtISO, access },
    { accountId, account: false },
  );
  return info;
}

export async function cancelScheduledPublish(
  accountId: string,
  nodeId: number,
): Promise<{ canceled: boolean }> {
  const res = await wsApi.delete<{ canceled: boolean }>(
    `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(nodeId))}/schedule_publish`,
    { accountId, account: false },
  );
  return res;
}

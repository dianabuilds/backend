import { accountApi } from './accountApi';

export type AccessMode = 'everyone' | 'premium_only' | 'early_access';

export type PublishInfo = {
  status: string;
  published_at?: string | null;
  scheduled?: { run_at: string; access: AccessMode; status: string } | null;
};

export async function getPublishInfo(accountId: string, nodeId: number): Promise<PublishInfo> {
  if (accountId) {
    const info = await accountApi.get<PublishInfo>(
      `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(nodeId))}/publish_info`,
      { accountId, account: false },
    );
    return info;
  }
  return await accountApi.get<PublishInfo>(
    `/admin/nodes/${encodeURIComponent(String(nodeId))}/publish_info`,
    { accountId: "", account: false },
  );
}

export async function publishNow(
  accountId: string,
  nodeId: number,
  access: AccessMode = 'everyone',
): Promise<{ ok: true } | Record<string, unknown>> {
  if (accountId) {
    const res = await accountApi.post<{ access: AccessMode }, { ok: true } | Record<string, unknown>>(
      `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(nodeId))}/publish`,
      { access },
      { accountId, account: false },
    );
    return res;
  }
  return await accountApi.post<{ access: AccessMode }, { ok: true } | Record<string, unknown>>(
    `/admin/nodes/${encodeURIComponent(String(nodeId))}/publish`,
    { access },
    { accountId: "", account: false },
  );
}

export async function schedulePublish(
  accountId: string,
  nodeId: number,
  runAtISO: string,
  access: AccessMode = 'everyone',
): Promise<PublishInfo> {
  if (accountId) {
    const info = await accountApi.post<{ run_at: string; access: AccessMode }, PublishInfo>(
      `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(nodeId))}/schedule_publish`,
      { run_at: runAtISO, access },
      { accountId, account: false },
    );
    return info;
  }
  return await accountApi.post<{ run_at: string; access: AccessMode }, PublishInfo>(
    `/admin/nodes/${encodeURIComponent(String(nodeId))}/schedule_publish`,
    { run_at: runAtISO, access },
    { accountId: "", account: false },
  );
}

export async function cancelScheduledPublish(
  accountId: string,
  nodeId: number,
): Promise<{ canceled: boolean }> {
  if (accountId) {
    const res = await accountApi.delete<{ canceled: boolean }>(
      `/admin/accounts/${encodeURIComponent(accountId)}/nodes/${encodeURIComponent(String(nodeId))}/schedule_publish`,
      { accountId, account: false },
    );
    return res;
  }
  return await accountApi.delete<{ canceled: boolean }>(
    `/admin/nodes/${encodeURIComponent(String(nodeId))}/schedule_publish`,
    { accountId: "", account: false },
  );
}

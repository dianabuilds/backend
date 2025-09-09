import type { ValidateResult } from '../openapi';
import { api } from './client';
import type { Page } from './types';

export type AdminQuest = {
  id: string;
  slug: string;
  title: string;
  is_draft: boolean;
  created_at: string;
  published_at?: string | null;
  // расширяем по мере необходимости
};

export type PublishAccess = 'premium_only' | 'everyone' | 'early_access';

const listCache = new Map<string, { etag: string | null; data: AdminQuest[] }>();

export async function listQuests(params?: {
  q?: string;
  draft?: boolean;
  length?: 'short' | 'long';
  created_from?: string;
  created_to?: string;
  page?: number;
  per_page?: number;
}): Promise<AdminQuest[]> {
  const q = new URLSearchParams();
  if (params?.q) q.set('q', params.q);
  if (typeof params?.draft === 'boolean') q.set('draft', String(params.draft));
  if (params?.length) q.set('length', params.length);
  if (params?.created_from) q.set('created_from', params.created_from);
  if (params?.created_to) q.set('created_to', params.created_to);
  if (typeof params?.page === 'number') q.set('page', String(params.page));
  if (typeof params?.per_page === 'number') q.set('per_page', String(params.per_page));
  const url = `/admin/quests${q.toString() ? `?${q.toString()}` : ''}`;
  const cached = listCache.get(url);
  const res = await api.get<Page<AdminQuest> | AdminQuest[]>(url, {
    etag: cached?.etag ?? undefined,
    acceptNotModified: true,
  });
  if (res.status === 304 && cached) return cached.data;
  const data: AdminQuest[] = Array.isArray((res.data as Page<AdminQuest> | undefined)?.items)
    ? (res.data as Page<AdminQuest>).items
    : Array.isArray(res.data)
      ? (res.data as AdminQuest[])
      : [];
  if (res.etag) listCache.set(url, { etag: res.etag, data });
  return data;
}

export async function validateQuest(questId: string): Promise<ValidateResult> {
  const res = await api.get<ValidateResult>(
    `/admin/quests/${encodeURIComponent(questId)}/validation`,
  );
  return res.data!;
}

export async function publishQuest(
  questId: string,
  opts: {
    access: PublishAccess;
    coverUrl?: string | null;
    style_preset?: string | null;
  },
) {
  const res = await api.post<unknown>(`/admin/quests/${encodeURIComponent(questId)}/publish`, {
    access: opts.access,
    coverUrl: opts.coverUrl || null,
    style_preset: opts.style_preset || null,
  });
  return res.data;
}

export async function autofixQuest(questId: string, actions: string[]) {
  const res = await api.post<unknown>(
    `/admin/quests/${encodeURIComponent(questId)}/autofix`,
    { actions },
  );
  return res.data;
}

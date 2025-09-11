import type { BlacklistItem, MergeReport, TagListItem } from '../openapi';
import { api } from './client';

export async function dryRunMerge(from_id: string, to_id: string): Promise<MergeReport> {
  const res = await api.post<{ from_id: string; to_id: string; dryRun: boolean }, MergeReport>(
    '/admin/tags/merge',
    {
      from_id,
      to_id,
      dryRun: true,
    },
  );
  return res.data!;
}

export async function applyMerge(
  from_id: string,
  to_id: string,
  reason?: string,
): Promise<MergeReport> {
  const res = await api.post<
    { from_id: string; to_id: string; dryRun: boolean; reason?: string },
    MergeReport
  >('/admin/tags/merge', {
    from_id,
    to_id,
    dryRun: false,
    reason,
  });
  return res.data!;
}

export async function getBlacklist(q?: string): Promise<BlacklistItem[]> {
  const qs = q ? `?q=${encodeURIComponent(q)}` : '';
  const res = await api.get<BlacklistItem[]>(`/admin/tags/blacklist${qs}`);
  return res.data ?? [];
}

export async function addToBlacklist(slug: string, reason?: string): Promise<BlacklistItem> {
  const res = await api.post<{ slug: string; reason?: string }, BlacklistItem>(
    '/admin/tags/blacklist',
    { slug, reason },
  );
  return res.data!;
}

export async function removeFromBlacklist(slug: string): Promise<void> {
  await api.del(`/admin/tags/blacklist/${encodeURIComponent(slug)}`);
}

/** Admin list item returned by /admin/tags/list */
export async function listAdminTags(params: {
  q?: string;
  limit?: number;
  offset?: number;
}): Promise<TagListItem[]> {
  const { q, limit, offset } = params ?? {};
  const qs = [
    q ? `q=${encodeURIComponent(q)}` : '',
    typeof limit === 'number' ? `limit=${limit}` : '',
    typeof offset === 'number' ? `offset=${offset}` : '',
  ]
    .filter(Boolean)
    .join('&');
  const res = await api.get<TagListItem[]>(`/admin/tags/list${qs ? `?${qs}` : ''}`);
  return res.data ?? [];
}

export async function createAdminTag(slug: string, name: string): Promise<TagListItem> {
  const res = await api.post<{ slug: string; name: string }, TagListItem>('/admin/tags', {
    slug,
    name,
  });
  return res.data!;
}

// Re-export for pages that import the type from this module
export type { BlacklistItem } from '../openapi';

export async function deleteAdminTag(id: string): Promise<void> {
  await api.del(`/admin/tags/${encodeURIComponent(id)}`);
}
